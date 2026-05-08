"""
End-to-end test of the full bidding workflow using the configured real LLM.
Tests the complete flow: Analyze -> Confirm -> Draft -> Review.
"""
import os
import sys
import json

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflow import bid_workflow
from src.config import settings
from langchain_core.messages import HumanMessage


def test_full_workflow():
    print("=" * 60)
    print("  IT Bidding Copilot - Full E2E Test (Real LLM)")
    print(f"  Model: {settings.LLM_MODEL} via OpenAI-compatible endpoint")
    print("=" * 60)

    # 1. Load mock tender document
    mock_doc_path = os.path.join(os.path.dirname(__file__), "mock_data", "tender_document.md")
    with open(mock_doc_path, "r", encoding="utf-8") as f:
        parsed_markdown = f.read()

    print(f"\n📄 Loaded tender document: {len(parsed_markdown)} chars")

    # 2. Initialize state
    initial_state = {
        "project_id": 1,
        "messages": [HumanMessage(content="请分析这份招标文件。")],
        "parsed_markdown": parsed_markdown,
        "plan_report": "",
        "missing_materials": [],
        "scoring_items": [],
        "hard_requirements": [],
        "drafts": {},
        "review_report": "",
        "current_mode": "plan",
    }

    # 3. Stream through the full workflow
    print("\n" + "-" * 60)
    print("🚀 Starting workflow execution...")
    print("-" * 60)

    final_state = dict(initial_state)
    for output in bid_workflow.stream(initial_state):
        for node_name, state_update in output.items():
            print(f"\n{'='*40}")
            print(f"📍 Node: {node_name}")
            print(f"{'='*40}")

            final_state.update(state_update)

            if "current_mode" in state_update:
                print(f"  Mode: {state_update['current_mode']}")

            if "plan_report" in state_update and state_update["plan_report"]:
                report = state_update["plan_report"]
                print(f"\n📋 Plan Report Preview ({len(report)} chars):")
                print("-" * 40)
                print(report[:1500])
                if len(report) > 1500:
                    print("... [truncated]")

            if "missing_materials" in state_update and state_update["missing_materials"]:
                print(f"\n⚠️  Missing Materials: {state_update['missing_materials']}")

            if "drafts" in state_update and state_update["drafts"]:
                print(f"\n📝 Drafts Generated:")
                for name, content in state_update["drafts"].items():
                    print(f"  - {name}: {len(content)} chars")
                    print(f"    Preview: {content[:200]}...")

            if "review_report" in state_update and state_update["review_report"]:
                report = state_update["review_report"]
                print(f"\n🔍 Review Report ({len(report)} chars):")
                print("-" * 40)
                print(report[:2000])
                if len(report) > 2000:
                    print("... [truncated]")

    # 4. Summary
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"  Final mode: {final_state.get('current_mode')}")
    print(f"  Missing materials: {len(final_state.get('missing_materials', []))}")
    print(f"  Drafts generated: {list(final_state.get('drafts', {}).keys())}")
    print(f"  Review report: {'Yes' if final_state.get('review_report') else 'No'}")

    # 5. Save outputs to files for inspection
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    if final_state.get("plan_report"):
        with open(os.path.join(output_dir, "plan_report.md"), "w", encoding="utf-8") as f:
            f.write(final_state["plan_report"])
        print(f"\n💾 Saved: output/plan_report.md")

    for name, content in final_state.get("drafts", {}).items():
        safe_name = name.replace("/", "_").replace(" ", "_")
        with open(os.path.join(output_dir, f"draft_{safe_name}.md"), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"💾 Saved: output/draft_{safe_name}.md")

    if final_state.get("review_report"):
        with open(os.path.join(output_dir, "review_report.md"), "w", encoding="utf-8") as f:
            f.write(final_state["review_report"])
        print(f"💾 Saved: output/review_report.md")


if __name__ == "__main__":
    test_full_workflow()
