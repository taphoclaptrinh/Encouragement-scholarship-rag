import os
import json
from src.rag.chunker import DocumentChunker
from src.rag.hybrid_search import HybridSearchEngine
from src.core.llm_client import LLMClient
from src.agent.mcp_client import DynamicMCPClient
from src.agent.safe_parser import SafeActionParser
from src.schemas.rag_types import UsageMetric

def inspect_agent_execution(query: str):
    print("=" * 75)
    print("   SOI TỪNG BƯỚC VÒNG LẶP REACT: CONVERSATION_HISTORY VS TRACE_STEPS")
    print(f"   CÂU HỎI: \"{query}\"")
    print("=" * 75)

    # 1. Khởi tạo
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    corpus_dir = os.path.join(base_dir, "data", "corpus")
    server_path = os.path.join(base_dir, "src", "mcp_server", "server.py")
    prompts_dir = os.path.join(base_dir, "prompts")

    chunker = DocumentChunker(corpus_dir)
    chunks = chunker.load_and_chunk_all()
    hybrid_engine = HybridSearchEngine(chunks)
    mcp_client = DynamicMCPClient(server_path)
    llm_client = LLMClient()

    with open(os.path.join(prompts_dir, "system_agent.txt"), "r", encoding="utf-8") as f:
        system_prompt = f.read()

    # Tạo menu tool
    mcp_tools = mcp_client.discover_tools()
    rag_desc = "- rag_search(query: str, filter_doc_id: Optional[str] = None): Tra cứu quy chế đào tạo, học bổng.\n"
    tools_description = rag_desc + mcp_client.get_tools_description_text()

    # 2. Ngữ cảnh ban đầu (Step 0)
    conversation_history = (
        f"{system_prompt}\n\n"
        f"DANH SÁCH TOOLS KHẢ DỤNG:\n{tools_description}\n\n"
        f"YÊU CẦU CỦA NGƯỜI DÙNG: {query}\n"
    )
    trace_steps = []

    print("\n[BƯỚC 0 - TRẠNG THÁI KHỞI ĐẦU]")
    print(f">> Độ dài conversation_history ban đầu: {len(conversation_history)} ký tự.")
    print(f">> trace_steps ban đầu: {trace_steps} (Danh sách rỗng [])")
    print("-" * 75)

    step = 0
    max_steps = 6

    while step < max_steps:
        step += 1
        print(f"\n{'#' * 30} BƯỚC {step} BẮT ĐẦU {'#' * 30}")

        # Gọi LLM
        prompt_for_step = (
            f"{conversation_history}\n"
            f"Bước {step}: Hãy suy nghĩ (Thought) và chọn Action hoặc đưa ra Final Answer nếu đã có kết quả."
        )
        response_text, p_tok, c_tok, latency = llm_client.call(prompt_for_step)

        # Parse output
        action_name, action_args, direct_final = SafeActionParser.parse(response_text)

        step_record = {
            "step": step,
            "thought_and_raw": response_text.strip(),
            "action": action_name,
            "action_args": action_args,
            "observation": None
        }

        print(f"\n1. [LLM SINH RA Ở BƯỚC {step}]:")
        print(f"   {response_text.strip()}")

        # TH1: Final Answer
        if direct_final:
            print(f"\n>>> PHÁT HIỆN FINAL ANSWER! VÒNG LẶP SẼ DỪNG LẠI.")
            trace_steps.append(step_record)
            break

        if not action_name:
            print(f"\n>>> KHÔNG THẤY ACTION NÀO! KẾT THÚC.")
            trace_steps.append(step_record)
            break

        # TH2: Gọi Tool
        print(f"\n2. [THỰC THI TOOL]: {action_name} với tham số {action_args}")
        if action_name == "rag_search":
            q = action_args.get("query") or action_args.get("value") or ""
            res = hybrid_engine.search(q, top_k=2)
            observation = "\n".join([f"[{r.chunk.chunk_id}] {r.chunk.text[:90]}..." for r in res])
        else:
            observation = mcp_client.call_tool(action_name, action_args)

        step_record["observation"] = observation
        trace_steps.append(step_record)

        # CẬP NHẬT 2 BIẾN:
        history_before_len = len(conversation_history)
        conversation_history += (
            f"\nAction: {action_name}\n"
            f"Action Input: {json.dumps(action_args, ensure_ascii=False)}\n"
            f"Observation: {observation}\n"
        )
        history_after_len = len(conversation_history)

        print(f"\n3. [KẾT QUẢ QUAN SÁT (OBSERVATION)]:")
        print(f"   {observation[:120]}..." if len(observation) > 120 else f"   {observation}")

        # IN RA SỰ THAY ĐỔI CỦA 2 BIẾN
        print(f"\n4. [SỰ THAY ĐỔI CỦA HAI BIẾN SAU BƯỚC {step}]:")
        print(f"   * conversation_history: Tăng thêm {history_after_len - history_before_len} ký tự (Tổng cộng: {history_after_len} ký tự).")
        print(f"     -> Đoạn text vừa được nối thêm vào đuôi:")
        print(f"        Action: {action_name}")
        print(f"        Action Input: {json.dumps(action_args, ensure_ascii=False)}")
        print(f"        Observation: {observation[:60]}...")
        print(f"   * trace_steps: Đã tích lũy {len(trace_steps)} phần tử Object.")
        print(f"     -> Phần tử vừa thêm vào trace_steps:")
        print(f"        {json.dumps(step_record, ensure_ascii=False, indent=8)}")

        # AUTO-VERIFY NẾU CÓ
        if action_name == "submit_scholarship_nomination" and "nomination_id" in observation:
            try:
                obs_json = json.loads(observation)
                nom_id = obs_json.get("nomination_id") or (obs_json.get("data", {}).get("nomination_id") if isinstance(obs_json.get("data"), dict) else None)
                if nom_id:
                    print(f"\n   [!] [KÍCH HOẠT AUTO-VERIFY CHO BẢN GHI: {nom_id}]")
                    verify_obs = mcp_client.call_tool("verify_scholarship_nomination", {"nomination_id": nom_id})
                    conversation_history += (
                        f"\n[AUTO-VERIFY STEP]\n"
                        f"Action: verify_scholarship_nomination\n"
                        f"Action Input: {{\"nomination_id\": \"{nom_id}\"}}\n"
                        f"Observation: {verify_obs}\n"
                    )
                    trace_steps.append({
                        "step": step,
                        "substep": "auto_verify",
                        "action": "verify_scholarship_nomination",
                        "action_args": {"nomination_id": nom_id},
                        "observation": verify_obs
                    })
                    print(f"       -> trace_steps tăng lên {len(trace_steps)} phần tử do có thêm bước verify.")
            except Exception as e:
                pass

        print("-" * 75)

    print("\n" + "=" * 75)
    print("   TỔNG KẾT SAU KHI VÒNG LẶP KẾT THÚC:")
    print(f"   - Tổng số bước: {step}")
    print(f"   - Tổng số phần tử trong trace_steps: {len(trace_steps)}")
    print(f"   - Kích thước cuối cùng của conversation_history: {len(conversation_history)} ký tự")
    print("=" * 75)

if __name__ == "__main__":
    inspect_agent_execution("Hãy thẩm định sinh viên Nguyễn Hoàng Nam (mã số 23110101). Nếu đủ điều kiện Xuất sắc hãy nộp đơn đề cử học bổng và xác minh.")
