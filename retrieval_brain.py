import os
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

class MaintenanceRAG:
    def __init__(self):
        # 確保路徑與處理器一致
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(BASE_DIR, "chroma_db_unified")
        
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        
        # 載入資料庫
        if os.path.exists(db_path):
            self.vectorstore = Chroma(persist_directory=db_path, embedding_function=self.embeddings)
            print("RAG Brain: 資料庫載入成功。")
        else:
            print(f"警告: 找不到資料庫 {db_path}，請先執行 data_processor.py")
            self.vectorstore = None

        self.llm = OllamaLLM(model="llama3.2", temperature=0)

    def search_and_reason(self, query):
        if not self.vectorstore:
            return "錯誤：資料庫未初始化。"

        # 檢索最相關的 4 個片段
        docs = self.vectorstore.similarity_search(query, k=4)
        context = "\n\n".join([d.page_content for d in docs])
        
        template = """你是一位專業的設備維修工程師。請根據以下參考資料回答使用者的維修問題。
        
        參考資料 Context:
        {context}
        
        使用者問題: {question}
        
        回答要求：
        1. 若參考資料中有具體解法，請列出【故障診斷】、【檢查步驟】與【解決方案】。
        2. 請使用繁體中文。
        3. 若資料不足，請誠實告知「查無相關手冊資訊」。
        
        專業建議："""
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        return chain.invoke({"context": context, "question": query})
