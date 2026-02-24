import re
from langchain_ollama import OllamaLLM

class MermaidAgent:
    def __init__(self):
        self.llm = OllamaLLM(model="llama3.2", temperature=0)

    def generate(self, text):
        prompt = f"""
        任務：將以下維修步驟文字轉換為 Mermaid.js 流程圖代碼。
        
        輸入文本：
        {text}
        
        要求：
        1. 使用 flowchart TD (由上而下)。
        2. 節點文字請簡潔，使用繁體中文。
        3. 邏輯需包含：開始 -> 判斷條件(菱形) -> 執行動作(矩形) -> 結束。
        4. 只輸出 ```mermaid ... ``` 區塊，不要有其他解釋文字。
        """
        
        response = self.llm.invoke(prompt)
        
        # 使用正則表達式提取代碼
        match = re.search(r"```mermaid(.*?)```", response, re.DOTALL)
        if match:
            return match.group(0)
        else:
            return "⚠️ 無法生成圖表：模型未回傳正確的 Mermaid 語法。"
