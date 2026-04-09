import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ToneCalibrator:
    """
    标书语调校准器：
    1. 自动识别并剔除“AI 爹味”词汇（如：总之、综上所述、不仅如此）。
    2. 增强技术颗粒度，将模糊词汇替换为专业术语。
    3. 确保段落结构符合“结论先行”的行业规范。
    """
    
    # 禁用词库：AI 常用但标书忌讳的虚词
    FORBIDDEN_PATTERNS = [
        r"总之", r"综上所述", r"不仅如此", r"值得注意的是", 
        r"深入人心", r"致力于", r"一个巨大的", r"无可比拟的",
        r"事实上", r"众所周知", r"简单来说"
    ]
    
    # 词汇替换表：[模糊词] -> [专业词]
    TECHNICAL_MAPPING = {
        "很多": "海量/高并发",
        "很快": "毫秒级响应",
        "很稳": "高可用/金融级容灾",
        "处理": "调度与编排",
        "保护": "全链路加密/多维安全审计",
        "帮忙": "赋能/协同",
        "这种方法": "该技术方案/本演进路径"
    }

    def calibrate_text(self, text: str) -> str:
        """
        对文本进行预设规则校验与修复。
        """
        # 1. 剔除禁用词 (Regex Clean)
        calibrated = text
        for pattern in self.FORBIDDEN_PATTERNS:
            calibrated = re.sub(pattern, "", calibrated)
        
        # 2. 专业化词汇映射
        for fuzzy, tech in self.TECHNICAL_MAPPING.items():
            calibrated = calibrated.replace(fuzzy, tech)
            
        # 3. 结构修剪：收回多余的空行与自恋式导语
        calibrated = self._trim_ai_verbosity(calibrated)
        
        return calibrated.strip()

    def _trim_ai_verbosity(self, text: str) -> str:
        """剔除句首常见的 AI 开场白"""
        ai_intros = [
            "好的，根据您的要求", "我为您准备了", "作为一名专家", 
            "本方案旨在", "以下是具体的"
        ]
        lines = text.split('\n')
        if lines and any(text.startswith(intro) for intro in ai_intros):
            # 尝试移除第一行
            return '\n'.join(lines[1:])
        return text

    def smart_calibrate_with_llm(self, text: str, llm=None) -> str:
        """
        [进阶] 利用 LLM 进行深层次语义重塑。
        """
        if not llm:
            return self.calibrate_text(text)
            
        prompt = f"""
        你是一位资深 IT 标书专家。请对以下内容进行“去 AI 化”处理。
        要求：
        1. 删掉所有的感情色彩词汇和虚头巴脑的形容词。
        2. 增加技术名词的密度。
        3. 采用“确定性”语气，不要使用“可能”、“也许”。
        4. 结构采用【结论先行 -> 数据支撑 -> 架构保证】。
        
        待处理内容：
        {text}
        """
        try:
            return llm.predict(prompt)
        except Exception as e:
            logger.error(f"LLM Calibration failed: {e}")
            return self.calibrate_text(text)

if __name__ == "__main__":
    calibrator = ToneCalibrator()
    sample = "总之，这个系统真的很快，不仅如此，它还保护了数据非常稳。"
    print(f"Original: {sample}")
    print(f"Calibrated: {calibrator.calibrate_text(sample)}")
