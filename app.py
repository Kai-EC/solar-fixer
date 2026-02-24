import gradio as gr
import time
from retrieval_brain import MaintenanceRAG
from mermaid_agent import MermaidAgent

# --- 初始化 AI 模組 ---
print("正在初始化 AI 智慧維修系統模組...")
rag = MaintenanceRAG()
painter = MermaidAgent()
print("模組載入完成！")

# --- CSS 樣式定義區 ---
custom_css = """
/* 主容器背景：淺灰、#9bbabf、淺灰 */
.gradio-container {
    background: linear-gradient(180deg, #dcdcdc, #9bbabf, #dcdcdc);
}

/* 側邊欄背景顏色 */
.sidebar {
    background-color: #97a1a6;
    padding: 15px;
    border-radius: 10px;
}

/* 藍色提示框樣式 */
.blue-info-box {
    background-color: #262730;
    border: 1px solid #424a57;
    border-left: 5px solid #4e8df5;
    padding: 15px;
    border-radius: 5px;
    color: #e0e0e0;
    margin-bottom: 20px;
}

/* 虛線預覽框樣式 */
.dashed-placeholder {
    border: 2px dashed #4b4b4b;
    border-radius: 10px;
    height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #151820;
    font-size: 16px;
    background-color: #FCFCFC;
}
"""

# --- Mermaid 轉換邏輯 (擷取自 mermaid_html.py) ---
def generate_mermaid_html(text_input, mermaid_response):
    """
    將 Mermaid 代碼清理並打包成獨立的 HTML iframe 字串，
    確保在 Gradio 中渲染不會受到外部 CSS/JS 干擾。
    """
    clean_code = mermaid_response.replace('```mermaid', '').replace('```', '').strip()
    
    # 建立純淨的 HTML 模板
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
        <style>
            body {{ font-family: "Segoe UI", sans-serif; background: #ffffff; color: #1e293b; padding: 20px; margin: 0; }}
            h2 {{ color: #1e293b; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }}
            .advice-text {{ white-space: pre-wrap; line-height: 1.6; color: #475569; font-size: 14px; margin-bottom: 20px; }}
            .mermaid-container {{ text-align: center; overflow: auto; margin-top: 20px; }}
            .mermaid {{ display: inline-block; }}
        </style>
    </head>
    <body>
        <h2>💡 維修步驟解析</h2>
        <div class="advice-text">{text_input}</div>
        <h2>📊 流程圖</h2>
        <div class="mermaid-container">
            <div class="mermaid">
{clean_code}
            </div>
        </div>
        <script>
            mermaid.initialize({{ 
                startOnLoad: true, 
                theme: 'neutral',
                securityLevel: 'loose'
            }});
        </script>
    </body>
    </html>
    """
    
    # 將 HTML 放入 iframe 中回傳給 Gradio，避免樣式污染
    # 注意：這裡使用 srcdoc 屬性直接嵌入 HTML
    safe_html = html_content.replace('"', '&quot;')
    iframe_code = f'<iframe srcdoc="{safe_html}" style="width: 100%; height: 600px; border: none; border-radius: 10px; background-color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.08);"></iframe>'
    
    return iframe_code

# --- 核心邏輯函式區 ---
def chat_response(message, history):
    history = history or []
    
    # 1. 呼叫 RAG 進行檢索與推論
    answer = rag.search_and_reason(message)
    # 修正幻覺字眼
    answer = answer.replace("ตรวจสอบ", "檢查").replace("ตรวจ", "檢")
    
    # 更新對話紀錄
    history.append([message, answer])
    
    # 預設圖表區不變（若無流程圖觸發）
    vis_update = gr.update()
    
    # 2. 判斷是否需要繪製流程圖
    if any(keyword in answer for keyword in ["檢查", "步驟", "解決"]):
        chart_code = painter.generate(answer)
        # 呼叫轉換函式產生 HTML iframe
        new_html = generate_mermaid_html(answer, chart_code)
        vis_update = new_html

    return "", history, vis_update

def file_upload_handler(file):
    # 這裡保留你原本的檔案上傳前端邏輯，後續可以串接 data_processor.py
    if file:
        file_names = [f.name.split('/')[-1] for f in file] if isinstance(file, list) else [file.name.split('/')[-1]]
        names_str = ", ".join(file_names)
        return f"""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; color: white; height: 200px;">
            <h3 style="color: #4CAF50;">✅ 資料已載入</h3>
            <p>檔案名稱: {names_str}</p>
            <p>等待輸入問題進行分析...</p>
        </div>
        """
    return '<div class="dashed-placeholder">維修文本與動態維修流程圖展示區 (等待資料...)</div>'

# --- 介面建置區 ---
with gr.Blocks(title="太陽能設備維修助手", css=custom_css) as demo:
    with gr.Sidebar(elem_classes="sidebar"):
        gr.Markdown("## 📂 資料設定")
        gr.Markdown("請上傳資料檔案 (CSV/PDF)")

        file_input = gr.File(
            label="Drag and drop file here",
            file_types=[".csv", ".pdf"],
            file_count="multiple",
            height=150
        )

        gr.HTML("""
        <div style="background-color: #ddebe5; padding: 10px; border-radius: 5px; font-size: 0.9em; color: #202426; margin-top: 10px;">
            💡 <b>提示：</b>上傳檔案後，<br>右側將自動顯示分析結果。
        </div>
        """)

    gr.Markdown("""
        # 📊 太陽能設備維修助手
        此系統整合了 **資料視覺化** 與 **對話助理**，協助您快速洞察數據。
    """)

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 🔗 維修文本與動態維修流程圖")
            gr.HTML("""
                <div class="blue-info-box">
                    👉 請先從左側側邊欄上傳資料檔案，並在右側對話視窗輸入維修問題。
                </div>
            """)
            # 這是圖表渲染區
            vis_output = gr.HTML(
                '<div class="dashed-placeholder">維修文本與動態維修流程圖展示區 (等待資料...)</div>'
            )

        with gr.Column(scale=1):
            gr.Markdown("### 💬 AI 分析助理")
            chatbot = gr.Chatbot(
                height=400,
                label="對話視窗"
            )
            msg = gr.Textbox(
                placeholder="請輸入您的問題 (例如：列出可能發生的問題)...",
                show_label=False,
                container=True
            )
            
            # 綁定 Submit 事件：輸入問題 -> 清空對話框, 更新聊天室, 更新圖表區
            msg.submit(
                chat_response, 
                inputs=[msg, chatbot], 
                outputs=[msg, chatbot, vis_output]
            )

    file_input.change(fn=file_upload_handler, inputs=file_input, outputs=vis_output)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        theme=gr.themes.Soft(primary_hue="blue"),
        css=custom_css
    )