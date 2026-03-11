import sys
import gradio as gr
import time
import base64
import os
import json
import re
import glob
from datetime import datetime

# 解決編碼問題
sys.stdout.reconfigure(encoding='utf-8')

# 匯入您的自定義模組
from retrieval_brain import MaintenanceRAG
from mermaid_agent import MermaidAgent

# 初始化組件
rag = MaintenanceRAG()
painter = MermaidAgent()

# --- 建立儲存歷史紀錄的資料夾 ---
SAVE_DIR = "history_outputs"
os.makedirs(SAVE_DIR, exist_ok=True)

def sanitize_filename(text):
    """清除不合法的檔名字元，確保存檔不報錯"""
    return re.sub(r'[^\w\u4e00-\u9fa5]', '_', text)[:20]

def save_to_local(query, answer, html_content):
    """將每次的查詢、文本與可視化 HTML 儲存到本地端"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = sanitize_filename(query)
    base_filename = f"{timestamp}_{safe_query}"
    
    # 儲存 metadata JSON
    json_path = os.path.join(SAVE_DIR, f"{base_filename}.json")
    record = {
        "timestamp": timestamp,
        "query": query,
        "answer_text": answer
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=4)
        
    # 儲存完整的 HTML
    html_path = os.path.join(SAVE_DIR, f"{base_filename}.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"[系統日誌] 已儲存檢索紀錄: {base_filename}")

def get_history_list():
    """掃描資料夾，回傳最新的歷史紀錄列表"""
    files = glob.glob(os.path.join(SAVE_DIR, "*.html"))
    # 依照修改時間排序，最新的在最上面
    files.sort(key=os.path.getmtime, reverse=True)
    # 只取檔名（不含副檔名）作為選單選項
    return [os.path.basename(f).replace('.html', '') for f in files]

def load_history(selected_file):
    """讀取選定的歷史 HTML 檔案並回傳 iframe 顯示"""
    if not selected_file:
        return '<div class="dashed-placeholder">請從上方選單選擇一筆紀錄...</div>'
    
    html_path = os.path.join(SAVE_DIR, f"{selected_file}.html")
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            raw_html = f.read()
        # 將讀出來的 HTML 轉為 Base64 iframe 以避免污染 Gradio 全局 CSS
        b64 = base64.b64encode(raw_html.encode('utf-8')).decode('utf-8')
        return f'<iframe src="data:text/html;base64,{b64}" width="100%" height="900px" style="border:none; border-radius:15px;"></iframe>'
    else:
        return f'<div class="dashed-placeholder">找不到對應的檔案：{selected_file}</div>'

# --- CSS 樣式 ---
custom_css = """
.gradio-container { background-color: #9bbabf; }
.blue-info-box {
    background-color: #262730; border: 1px solid #424a57; border-left: 5px solid #4e8df5;
    padding: 15px; border-radius: 5px; color: #e0e0e0; margin-bottom: 20px;
}
.dashed-placeholder {
    border: 2px dashed #4b4b4b; border-radius: 10px; height: 300px; display: flex;
    align-items: center; justify-content: center; color: #151820; font-size: 16px; background-color: #FCFCFC;
}
"""

def generate_mermaid_html(answer_text, mermaid_code):
    """封裝 Mermaid 繪圖至 Base64 Iframe，並同時回傳原始 HTML"""
    clean_code = mermaid_code.replace('```mermaid', '').replace('```', '').strip()
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
        <style>
            body {{ font-family: "Segoe UI", "Microsoft JhengHei", sans-serif; background: #f8fafc; padding: 20px; margin: 0; }}
            .card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
            h2 {{ color: #1e293b; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }}
            .advice-text {{ white-space: pre-wrap; line-height: 1.7; color: #475569; margin-bottom: 20px; }}
            .mermaid {{ display: flex; justify-content: center; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>💡 維修診斷建議</h2>
            <div class="advice-text">{answer_text}</div>
            <h2>📊 維修操作流程圖</h2>
            <div class="mermaid">{clean_code}</div>
        </div>
        <script>
            mermaid.initialize({{ startOnLoad: true, theme: 'neutral', securityLevel: 'loose' }});
            mermaid.contentLoaded();
        </script>
    </body>
    </html>
    """
    
    b64 = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
    iframe_html = f'<iframe src="data:text/html;base64,{b64}" width="100%" height="900px" style="border:none; border-radius:15px;"></iframe>'
    
    return iframe_html, html_content

def handle_query(message, history):
    """處理核心邏輯"""
    raw_answer = rag.search_and_reason(message)
    answer = raw_answer.replace("ตรวจสอบ", "檢查").replace("ตรวจ", "檢")
    
    vis_html = ""
    raw_html_to_save = ""
    
    if any(k in answer for k in ["檢查", "步驟", "解決", "流程"]):
        chart_code = painter.generate(answer)
        vis_html, raw_html_to_save = generate_mermaid_html(answer, chart_code)
    else:
        vis_html = f'<div class="card" style="background:white; padding:20px; border-radius:12px;"><h3>📝 分析結果</h3><p>{answer}</p></div>'
        raw_html_to_save = f'<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8"></head><body style="font-family: sans-serif; padding: 20px;"><h2>📝 分析結果</h2><p>{answer}</p></body></html>'
    
    save_to_local(message, answer, raw_html_to_save)
    
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": "分析已完成，請查看左側面板的詳細維修流程圖。您可以隨時在「歷史紀錄查詢」分頁回顧此次分析。"})
    
    return "", history, vis_html

# --- 介面建置 ---
with gr.Blocks(title="太陽能設備維修助手", theme=gr.themes.Soft(primary_hue="blue"), css=custom_css) as demo:
    
    with gr.Tabs():
        # --- 分頁 1: 核心系統 ---
        with gr.Tab("🛠️ 維修診斷主系統"):
            with gr.Sidebar():
                gr.Markdown("## 📂 資料設定")
                file_input = gr.File(label="上傳手冊 (PDF/CSV)", file_types=[".csv", ".pdf"], height=500)
                gr.HTML('<div style="background-color: #ddebe5; padding: 10px; border-radius: 5px; color: #202426;">💡 提示：上傳後系統會自動更新知識庫。</div>')

            gr.Markdown("""
                # 📊 太陽能設備維修助手
                此系統整合了 **資料視覺化** 與 **對話助理**，協助您快速洞察數據。
                """)

            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("### 🔗 維修建議與操作流程")
                    vis_output = gr.HTML('<div class="dashed-placeholder">等待分析數據...</div>')

                with gr.Column(scale=1):
                    gr.Markdown("### 💬 AI 分析助理")
                    chatbot = gr.Chatbot(height=450, label="對話視窗")
                    msg = gr.Textbox(placeholder="輸入故障情況...", show_label=False)
                    
                    msg.submit(handle_query, [msg, chatbot], [msg, chatbot, vis_output])

        # --- 分頁 2: 歷史紀錄 ---
        with gr.Tab("📁 歷史紀錄查詢"):
            gr.Markdown("## 🗂️ 過去檢索與分析紀錄")
            gr.Markdown("在此選擇您過往查詢過的維修案例，系統將重新載入當時的流程圖與建議內容。")
            
            with gr.Row():
                with gr.Column(scale=1):
                    refresh_btn = gr.Button("🔄 重新載入列表", variant="secondary")
                with gr.Column(scale=3):
                    # 預設載入時讀取一次清單
                    history_dropdown = gr.Dropdown(choices=get_history_list(), label="選擇歷史紀錄", interactive=True)
            
            history_display = gr.HTML('<div class="dashed-placeholder">請從上方選單選擇一筆紀錄...</div>')

            # --- 綁定歷史紀錄事件 ---
            # 點擊重新整理按鈕時，更新下拉選單的選項
            refresh_btn.click(fn=lambda: gr.update(choices=get_history_list()), outputs=history_dropdown)
            # 當下拉選單的值改變時，讀取並顯示對應的 HTML
            history_dropdown.change(fn=load_history, inputs=history_dropdown, outputs=history_display)

if __name__ == "__main__":
    # 啟動 Gradio 應用程式
    demo.launch(
        server_name="127.0.0.1",  # 確保這行寫完整，不要只有 server_na
        theme=gr.themes.Soft(primary_hue="blue"),
        css=custom_css
    )
