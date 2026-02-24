import os
import re
import webbrowser

def process_mermaid_to_html(text_input, mermaid_response, film_name="flowchart_output"):
    """
    將 Mermaid 代碼轉換為 HTML 並自動預覽。
    優化：解決圖形不顯示問題，增加渲染容錯率。
    """
    folder_name = "flowchart"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # 1. 強化清理邏輯
    # 移除 Markdown 語法標籤、前後空白以及可能干擾渲染的隱形字元
    clean_code = mermaid_response.replace('```mermaid', '').replace('```', '').strip()
    
    # 2. 建立強健的 HTML 模板
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>維修報告 - {film_name}</title>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
        <style>
            :root {{ --bg: #f8fafc; --text: #1e293b; --accent: #3b82f6; --card: #ffffff; }}
            body {{ font-family: "Segoe UI", "Microsoft JhengHei", sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
            .container {{ display: flex; gap: 20px; flex-wrap: wrap; justify-content: center; }}
            .card {{ background: var(--card); padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
            .text-panel {{ flex: 1; min-width: 350px; max-width: 500px; }}
            .graph-panel {{ flex: 2; min-width: 550px; text-align: center; overflow: auto; }}
            h2 {{ color: var(--text); border-bottom: 2px solid var(--accent); padding-bottom: 10px; margin-top: 0; }}
            .advice-text {{ white-space: pre-wrap; line-height: 1.7; color: #475569; font-size: 0.95rem; }}
            .mermaid {{ display: block; margin: 0 auto; }}
            .error-hint {{ color: #ef4444; font-weight: bold; padding: 20px; display: none; }}
        </style>
    </head>
    <body>
        <h1 style="text-align:center; color: var(--primary); margin-bottom: 30px;">🛠️ 智慧維修分析報告</h1>
        <div class="container">
            <div class="card text-panel">
                <h2>💡 維修建議</h2>
                <div class="advice-text">{text_input}</div>
            </div>

            <div class="card graph-panel">
                <h2>📊 流程圖預覽</h2>
                <div id="mermaid-container" class="mermaid">
{clean_code}
                </div>
                <div id="error-msg" class="error-hint">⚠️ 圖表語法錯誤或渲染失敗，請檢查輸入代碼。</div>
            </div>
        </div>

        <script>
            // 監聽渲染失敗事件
            window.addEventListener('error', function(e) {{
                if (e.target.id === 'mermaid-container') {{
                    document.getElementById('error-msg').style.display = 'block';
                }}
            }}, true);

            // 初始化與渲染
            mermaid.initialize({{ 
                startOnLoad: true, 
                theme: 'neutral',
                securityLevel: 'loose',
                fontFamily: 'inherit',
                flowchart: {{ 
                    useMaxWidth: true, 
                    htmlLabels: true,
                    curve: 'basis'
                }}
            }});
            
            // 強制再次嘗試渲染
            mermaid.contentLoaded();
        </script>
    </body>
    </html>
    """

    # 3. 儲存與開啟
    html_file_path = os.path.join(folder_name, f"{film_name}.html")
    try:
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        full_path = os.path.abspath(html_file_path)
        print(f"✅ 報告已生成：{full_path}")
        webbrowser.open(f"file://{full_path}")
    except Exception as e:
        print(f"❌ 檔案寫入失敗: {e}")
