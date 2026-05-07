"""
Test script to verify the RAG-enabled bidding workflow.
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflow import bid_workflow
from langchain_core.messages import HumanMessage


def test_rag_workflow():
    print("\n" + "="*60)
    print("🚀 Starting RAG-Enabled Workflow Test")
    print("="*60)

    # 1. Load a sample tender document
    tender_path = "/root/it-bidding-copilot/vault/10-Knowledge/Evergreen/招标文件案例.md"
    with open(tender_path, "r", encoding="utf-8") as f:
        tender_md = f.read()[:30000] # Truncate for speed in test

    print(f"Loaded tender doc: {len(tender_md)} chars")

    # 2. Initialize State
    initial_state = {
        "project_id": 1,
        "messages": [HumanMessage(content="开始分析招标文件并起草标书。")],
        "parsed_markdown": tender_md,
        "plan_report": "",
        "missing_materials": [],
        "scoring_items": [],
        "hard_requirements": [],
        "drafts": {},
        "review_report": "",
        "current_mode": "planning",
    }

    # 3. Run Workflow
    print("\n--- Running Workflow ---")
    
    # Run the graph until it hits a breakpoint or finishes
    # In this test, we skip human confirmation by just letting it run
    # (assuming we've set up the graph to not actually block in this test)
    
    # We will invoke it ONCE. It will go START -> analyze -> human -> draft -> review -> END
    # because human_confirmation_node is just a pass-through in this setup.
    state = bid_workflow.invoke(initial_state, {"configurable": {"thread_id": "test_thread"}})
    
    print(f"\n✅ Workflow complete. Final Mode: {state['current_mode']}")
    print(f"Drafts generated: {list(state['drafts'].keys())}")

    # 4. Verify RAG quality in the first draft (e.g., 商务偏离表)
    first_draft = state["drafts"].get("商务偏离表", "")
    print("\n" + "="*60)
    print("📝 VERIFYING DRAFT CONTENT (商务偏离表)")
    print("="*60)
    print(first_draft[:1000])
    
    # Check for keywords that should come from real evidence
    keywords = ["ISO9001", "营业执照", "授权书", "ZStack", "信核", "PMP"]
    found = [kw for kw in keywords if kw in first_draft]
    print(f"\nKeywords found in draft: {found}")
    
    if "详见附件" in first_draft or "证" in first_draft:
        print("\n✨ RAG integration seems SUCCESSFUL! The model is referencing evidence.")
    else:
        print("\n⚠️  No clear evidence references found. Check RAG logs.")

    print("\n" + "="*60)
    print("🏁 Test Finished")
    print("="*60)


if __name__ == "__main__":
    test_rag_workflow()
