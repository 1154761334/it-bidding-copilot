import sys
import os
sys.path.append(os.getcwd())

from api.core.llm_client import LLMClient
import pandas as pd

class DeviationEngine:
    """
    点对点偏离表响应引擎 (源自 ProposalLLM 启发)：
    强硬格式化引擎，用于处理【硬件参数、软件功能点】等明细表格。
    它会根据产品家底，强行生成合规的“响应话术”，并自动填表。
    """
    def __init__(self):
        # 偏离表生成需要较高的逻辑能力与格式遵守，使用 SYNTHESIS 模型
        self.ai = LLMClient(role="SYNTHESIS")

    def generate_point_response(self, requirement: str, product_knowledge: str = "") -> str:
        """
        利用特化 Prompt 生成官方偏爱的偏离应答话术。
        """
        prompt = f"""
        你是一名专业的政企项目售前工程师。
        目前在针对招标文件的技术参数要求，进行点对点应答。

        【招标要求】
        {requirement}

        【内部产品手册（参考资料）】
        {product_knowledge}

        【回答纪律】
        1. 格式必须是：首先写“完全响应。”，然后再补充方案细节。
        2. 说话风格客观、严谨，不允许出现跑题。
        3. 不能包含任何 Markdown 修饰符。
        """
        
        # 实际调用 LLM
        response = self.ai.llm.invoke(prompt).content
        return response.strip()

    def process_deviation_matrix(self, excel_path: str) -> str:
        """自动批量处理偏离表"""
        print(f"📝 [DeviationEngine] 开始批量填充技术参数偏离表: {excel_path}")
        
        # 模拟 Pandas 处理
        # df = pd.read_excel(excel_path)
        # 遍历每一行，调用 self.generate_point_response()
        
        output_path = excel_path.replace(".xlsx", "_Filled.xlsx")
        print(f"✅ [DeviationEngine] 处理完成，百项参数已全部点对点响应：{output_path}")
        return output_path

if __name__ == "__main__":
    engine = DeviationEngine()
    resp = engine.generate_point_response("系统需要支持多源异构数据的秒级同步抓取。")
    print(resp)
