import gradio as gr
import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load env
load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "dev-secret-key-12345")
TAGS = ["HR", "Legal", "Finance"]

# --- Custom CSS ---
CUSTOM_CSS = """
.container { max-width: 1200px; margin: auto; }
.search-card {
    background: white;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    border: 1px solid #e5e7eb;
}
.search-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    border-color: #6366f1;
}
.score-bar-bg {
    background: #e5e7eb;
    height: 6px;
    border-radius: 3px;
    margin-top: 8px;
    width: 100%;
}
.score-bar-fill {
    height: 6px;
    border-radius: 3px;
    background: linear-gradient(90deg, #6366f1, #818cf8);
}
.source-tag {
    display: inline-block;
    background: #f3f4f6;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    color: #4b5563 !important;
    margin-right: 5px;
    border: 1px solid #e5e7eb;
}
"""

def get_headers():
    return {"Authorization": f"Bearer {API_KEY}"}

# --- Functions ---

def upload_document(file, tag, uploaded_by):
    if not file:
        return "⚠️ Please select a file."
    
    try:
        with open(file, "rb") as f:
            pdf_content = f.read()
            
        import base64
        base64_content = base64.b64encode(pdf_content).decode("utf-8")
        
        payload = {
            "filename": os.path.basename(file.name),
            "tag": tag,
            "base64_content": base64_content,
            "uploaded_by": uploaded_by
        }
        
        response = requests.post(f"{API_URL}/ingest", json=payload, headers=get_headers())
        
        if response.status_code == 201:
            data = response.json()
            # Success Card HTML
            return f"""
            <div style="background: #ecfdf5; border: 1px solid #34d399; padding: 20px; border-radius: 8px; text-align: center;">
                <div style="font-size: 40px; margin-bottom: 10px;">✅</div>
                <h3 style="color: #065f46 !important; margin: 0;">Upload Successful</h3>
                <p style="color: #047857 !important;"><b style="color: #047857 !important;">{data.get('filename')}</b> has been added.</p>
                <div style="margin-top: 15px; display: flex; justify-content: center; gap: 20px; font-size: 0.9em; color: #064e3b !important;">
                    <span style="color: #064e3b !important;">📄 {data.get('pages_ingested')} Pages</span>
                    <span style="color: #064e3b !important;">🏷️ {data.get('tag')}</span>
                    <span style="color: #064e3b !important;">👤 {data.get('uploaded_by')}</span>
                </div>
            </div>
            """
        else:
            return f"""
            <div style="background: #fef2f2; border: 1px solid #f87171; padding: 20px; border-radius: 8px;">
                <h3 style="color: #991b1b; margin: 0;">❌ Upload Failed</h3>
                <p style="color: #b91c1c;">Error {response.status_code}: {response.text}</p>
            </div>
            """
            
    except Exception as e:
        return f"⚠️ Exception: {str(e)}"

def chat_function(message, history, tag):
    if not message:
        return "", []
    
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"query": message, "tag": tag},
            headers=get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data["answer"]
            sources = data.get("sources", [])
            
            full_response = answer
            
            # Formatted Sources using <details> for cleaner UI
            if sources:
                source_list = "".join([f"<li style='color: #374151 !important;'>{s}</li>" for s in sources])
                full_response += f"""
                <br><br>
                <details style="background: #f9fafb; border: 1px solid #e5e7eb; padding: 10px; border-radius: 8px; color: #374151 !important;">
                    <summary style="cursor: pointer; font-weight: 600; color: #4b5563 !important;">📚 View Sources ({len(sources)})</summary>
                    <ul style="margin-top: 10px; padding-left: 20px; color: #374151 !important;">
                        {source_list}
                    </ul>
                </details>
                """
            return full_response
        else:
            return f"Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return f"Connection Failed: {str(e)}"

def search_documents(query, tag, top_k):
    try:
        response = requests.post(
            f"{API_URL}/retrieve",
            json={"query": query, "tag": tag, "top_k": int(top_k)},
            headers=get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data["results"]
            
            if not results:
                return "<div style='text-align: center; padding: 20px; color: #6b7280;'>No results found.</div>"
            
            cards_html = f"<h3 style='margin-bottom: 20px;'>Found {data['total_results']} matches</h3>"
            
            for res in results:
                score = res.get('similarity_score', 0)
                # Normalize visualization width (assuming score is 0-1)
                bar_width = max(0, min(100, score * 100))
                
                # Determine color based on score
                color = "#22c55e" # Green
                if score < 0.7: color = "#eab308" # Yellow
                if score < 0.5: color = "#ef4444" # Red
                
                fname = res.get('filename', 'Unknown')
                page = res.get('page_number', '?')
                text = res.get('text', '')
                
                # Truncate text
                truncated_text = text[:300] + "..." if len(text) > 300 else text
                
                cards_html += f"""
                <div class="search-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div>
                            <span style="font-weight: bold; color: #111827 !important;">📄 {fname}</span>
                            <span class="source-tag">Page {page}</span>
                        </div>
                        <div style="text-align: right; width: 100px;">
                            <div style="font-size: 0.85em; color: #6b7280 !important;">Match: {score:.3f}</div>
                            <div class="score-bar-bg">
                                <div class="score-bar-fill" style="width: {bar_width}%; background: {color};"></div>
                            </div>
                        </div>
                    </div>
                    <div style="font-family: monospace; background: #f9fafb; padding: 10px; border-radius: 6px; font-size: 0.9em; color: #374151 !important; white-space: pre-wrap;">
                        {truncated_text}
                    </div>
                </div>
                """
            return cards_html
        else:
            return f"<div style='color: red;'>Error {response.status_code}: {response.text}</div>"
    except Exception as e:
            return f"<div style='color: red;'>Error: {str(e)}</div>"

def check_health():
    try:
        start = time.time()
        response = requests.get(f"{API_URL}/health")
        duration = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            
            # Helper for badges
            def status_badge(is_healthy):
                return "✅ Online" if is_healthy else "❌ Offline"
            
            def status_color(is_healthy):
                return "#d1fae5" if is_healthy else "#fee2e2" # light green vs light red
                
            def text_color(is_healthy):
                return "#065f46" if is_healthy else "#991b1b"

            # Create Dashboard HTML
            dashboard = f"""
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div style="background: {status_color(data['checks']['database'])}; padding: 15px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.05);">
                    <div style="font-size: 0.9em; color: #6b7280 !important; font-weight: 600;">Database</div>
                    <div style="font-size: 1.2em; color: {text_color(data['checks']['database'])} !important; margin-top: 5px;">
                        {status_badge(data['checks']['database'])}
                    </div>
                </div>
                
                <div style="background: {status_color(data['checks']['pgvector'])}; padding: 15px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.05);">
                     <div style="font-size: 0.9em; color: #6b7280 !important; font-weight: 600;">PGVector</div>
                    <div style="font-size: 1.2em; color: {text_color(data['checks']['pgvector'])} !important; margin-top: 5px;">
                        {status_badge(data['checks']['pgvector'])}
                    </div>
                </div>

                <div style="background: {status_color(data['checks']['embedding_model'])}; padding: 15px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.05);">
                     <div style="font-size: 0.9em; color: #6b7280 !important; font-weight: 600;">Embedding Model</div>
                    <div style="font-size: 1.2em; color: {text_color(data['checks']['embedding_model'])} !important; margin-top: 5px;">
                         {status_badge(data['checks']['embedding_model'])}
                    </div>
                </div>
                
                <div style="background: {status_color(data['checks']['openrouter'])}; padding: 15px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.05);">
                     <div style="font-size: 0.9em; color: #6b7280 !important; font-weight: 600;">OpenRouter API</div>
                    <div style="font-size: 1.2em; color: {text_color(data['checks']['openrouter'])} !important; margin-top: 5px;">
                         {status_badge(data['checks']['openrouter'])}
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 20px; text-align: right; color: #9ca3af; font-size: 0.85em;">
                Latency: {duration:.0f}ms • Last Updated: {datetime.now().strftime('%H:%M:%S')}
            </div>
            """
            return dashboard
        else:
            return f"❌ Server Error: {response.status_code}"
    except Exception as e:
        return f"❌ Connection Failure: {e}"

# --- Layout ---

with gr.Blocks(title="Corporate RAG Chatbot", theme=gr.themes.Soft(primary_hue="indigo"), css=CUSTOM_CSS) as demo:
    with gr.Column(elem_classes="container"):
        gr.Markdown("# 🏢 Corporate Document Chatbot")
        
        with gr.Tabs():
            # Tab 1: Upload
            with gr.Tab("📤 Upload"):
                gr.Markdown("### Add Knowledge to the Base")
                with gr.Row():
                    with gr.Column(scale=1):
                        file_input = gr.File(label="Select PDF", file_types=[".pdf"])
                        tag_input = gr.Dropdown(choices=TAGS, label="Department Tag", value="HR")
                        email_input = gr.Textbox(label="Uploaded By", value="admin@company.com")
                        upload_btn = gr.Button("Upload Document", variant="primary", size="lg")
                    
                    with gr.Column(scale=1):
                        upload_output = gr.HTML(label="Status")
                
                upload_btn.click(
                    upload_document,
                    inputs=[file_input, tag_input, email_input],
                    outputs=upload_output
                )

            # Tab 2: Chat
            with gr.Tab("💬 Chat"):
                with gr.Row():
                    chat_tag = gr.Dropdown(choices=TAGS, label="Context", value="HR", scale=1)
                    with gr.Column(scale=3):
                        gr.Markdown("Ask questions about company policies, documents, and data.")
                
                chatbot = gr.Chatbot(height=500, type="messages", avatar_images=(None, "https://ui-avatars.com/api/?name=Bot&background=6366f1&color=fff"))
                
                with gr.Row():
                    msg = gr.Textbox(placeholder="E.g., What is the vacation policy?", label="Your Question", scale=4)
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                
                clear_btn = gr.Button("Clear Chat", variant="secondary")
                
                def user(user_message, history):
                    return "", history + [{"role": "user", "content": user_message}]

                def bot(history, tag):
                    if not history: return history
                    user_message = history[-1]["content"]
                    bot_message = chat_function(user_message, history, tag)
                    history.append({"role": "assistant", "content": bot_message})
                    return history

                msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
                    bot, [chatbot, chat_tag], chatbot
                )
                send_btn.click(user, [msg, chatbot], [msg, chatbot], queue=False).then(
                    bot, [chatbot, chat_tag], chatbot
                )
                clear_btn.click(lambda: None, None, chatbot, queue=False)

            # Tab 3: Search
            with gr.Tab("🔍 Search"):
                gr.Markdown("### Semantic Verification & Debugging")
                with gr.Row():
                    search_query = gr.Textbox(label="Query", placeholder="enter keywords or * for all", scale=3)
                    search_tag = gr.Dropdown(choices=TAGS, label="Tag", value="HR", scale=1)
                    top_k = gr.Number(label="Top K", value=5, precision=0, scale=1)
                    search_btn = gr.Button("Search", variant="primary", scale=1)
                
                search_results = gr.HTML(label="Results Container")
                
                search_btn.click(
                    search_documents,
                    inputs=[search_query, search_tag, top_k],
                    outputs=search_results
                )

            # Tab 4: Health
            with gr.Tab("📊 Health"):
                with gr.Row(equal_height=True):
                    gr.Markdown("### System Status Dashboard")
                    health_btn = gr.Button("Refresh Status", size="sm")
                
                health_output = gr.HTML()
                
                health_btn.click(check_health, inputs=[], outputs=health_output)

            # Initial Health Check
            demo.load(check_health, inputs=[], outputs=health_output)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
