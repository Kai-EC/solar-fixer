import os
import sys
import hashlib
import pandas as pd
from glob import glob
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
sys.stdout.reconfigure(encoding='utf-8')

from docling.document_converter import DocumentConverter
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_DIR = os.path.join(BASE_DIR, "chroma_db_unified")
EMBED_MODEL = "nomic-embed-text"

def generate_doc_id(content: str) -> str:
    """生成出唯一的資料ID，防止資料重複"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def process_csv_files(embeddings):
    docs = []
    ids = []
    csv_files = glob(os.path.join(DATA_DIR, "*.csv"))

    if not csv_files:
        print("未發現 CSV 檔案。")
        return docs, ids

    print(f"發現 {len(csv_files)} 個 CSV，開始語意化處理...")
    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path, encoding='utf-8').fillna("無")
            for _, row in df.iterrows():
                content = (
                    f"【維修案例】設備：{row.get('設備', '未知')}。"
                    f"異常狀況：{row.get('常見異常原因', '未知')}。"
                    f"檢查步驟：{row.get('檢查方式', '無')}。"
                    f"解決方案：{row.get('解決方法', '無')}。"
                )
                docs.append(Document(
                    page_content=content, 
                    metadata={"source": os.path.basename(file_path), "type": "csv_log"}
                ))
                ids.append(generate_doc_id(content))
        except Exception as e:
            print(f"讀取 CSV 失敗 ({file_path}): {e}")
    return docs, ids

def process_pdf_files():
    docs = []
    ids = []
    pdf_files = glob(os.path.join(DATA_DIR, "*.pdf"))

    if not pdf_files:
        print("未發現 PDF 檔案。")
        return docs, ids

    print(f"發現 {len(pdf_files)} 個 PDF，開始 OCR 與切分...")
    converter = DocumentConverter()
    
    # 雙層切分策略
    md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("#", "H1"), ("##", "H2")])
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

    for file_path in pdf_files:
        try:
            print(f"   -> 正在解析: {os.path.basename(file_path)}")
            result = converter.convert(file_path)
            md_text = result.document.export_to_markdown()
            
            header_splits = md_splitter.split_text(md_text)
            final_chunks = text_splitter.split_documents(header_splits)

            for chunk in final_chunks:
                chunk.metadata["source"] = os.path.basename(file_path)
                chunk.metadata["type"] = "pdf_manual"
                docs.append(chunk)
                ids.append(generate_doc_id(chunk.page_content))
                
        except Exception as e:
            print(f"解析 PDF 失敗 ({file_path}): {e}")
    return docs, ids

def run_preprocessing():
    print("啟動資料預處理程序...")
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    
    csv_docs, csv_ids = process_csv_files(embeddings)
    pdf_docs, pdf_ids = process_pdf_files()
    
    all_docs = csv_docs + pdf_docs
    all_ids = csv_ids + pdf_ids

    if all_docs:
        print(f"正在寫入 {len(all_docs)} 筆資料至 ChromaDB...")
        vector_store = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
        vector_store.add_documents(documents=all_docs, ids=all_ids)
        print(f"完成！資料庫位於: {DB_DIR}")
    else:
        print("無資料可處理。")

if __name__ == "__main__":
    run_preprocessing()
