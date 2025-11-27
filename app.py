import streamlit as st
import google.generativeai as genai
import pandas as pd
from PyPDF2 import PdfReader
import io
import os
import time
import tempfile
import zipfile
from dotenv import load_dotenv

load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Context Switcher Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM PROFESSIONAL CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #1c1f26; color: #ffffff; border: 1px solid #2d313a; border-radius: 8px;
    }
    h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 600; color: #ffffff; }
    .stButton > button {
        width: 100%; border-radius: 8px; font-weight: bold; background-color: #2563eb;
        color: white; border: none; padding: 0.5rem 1rem; transition: all 0.2s;
    }
    .stButton > button:hover { background-color: #1d4ed8; }
    .stSuccess, .stInfo, .stWarning { background-color: #1c1f26; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configuration")
    st.markdown("---")
    # Try to get key from environment or streamlit secrets
    default_key = os.getenv("GOOGLE_API_KEY", "")
    if not default_key and "GOOGLE_API_KEY" in st.secrets:
        default_key = st.secrets["GOOGLE_API_KEY"]
        
    api_key = st.text_input("Google Gemini API Key", type="password", value=default_key)
    
    st.markdown("### 🎯 Audit Mode")
    audit_mode = st.radio("Select Goal:", [
        "🔄 Full Project Handoff (Resume Work)",
        "🛠 Fix Specific Error (Debug)",
        "🧠 Architecture Analysis (Review)"
    ])
    st.markdown("---")
    st.caption("Supports: ZIP, Code, PDF, Excel, Audio, Video")

# --- LOGIC CORE ---

def is_junk_file(filename):
    """Filters out system files and heavy folders."""
    ignore_patterns = ['__MACOSX', '.DS_Store', '.git', 'node_modules', '__pycache__', '.venv', 'package-lock.json']
    for pattern in ignore_patterns:
        if pattern in filename:
            return True
    return False

def process_file_content(filename, file_bytes):
    """Processes file content based on extension (Text, PDF, Excel)."""
    try:
        ext = filename.split('.')[-1].lower()
        
        # 1. Text/Code
        if ext in ['txt', 'py', 'js', 'tsx', 'jsx', 'html', 'css', 'json', 'md', 'csv', 'java', 'cpp']:
            return f"\n--- FILE: {filename} ---\n" + file_bytes.decode("utf-8", errors='ignore')
        
        # 2. Excel
        elif ext == 'xlsx':
            df = pd.read_excel(io.BytesIO(file_bytes))
            return f"\n--- FILE: {filename} (Data Summary) ---\n" + df.to_markdown()
        
        # 3. PDF
        elif ext == 'pdf':
            reader = PdfReader(io.BytesIO(file_bytes))
            text = "".join([page.extract_text() for page in reader.pages])
            return f"\n--- FILE: {filename} ---\n" + text
            
    except Exception as e:
        return f"\n[ERROR READING {filename}: {str(e)}]\n"
    return ""

def upload_media_to_gemini(filename, file_bytes, mime_type=None):
    """Uploads Audio/Video to Gemini Server."""
    # Create temp file because Gemini API needs a path
    suffix = "." + filename.split('.')[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    
    remote_file = genai.upload_file(path=tmp_path, display_name=filename, mime_type=mime_type)
    
    # Wait for processing
    while remote_file.state.name == "PROCESSING":
        time.sleep(1)
        remote_file = genai.get_file(remote_file.name)
        
    return remote_file

# --- MAIN UI ---
st.title("⚡ Universal Context Distiller")
st.markdown("Upload **ZIP folders** or individual files. We will audit everything and create a perfect handoff.")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📥 Input Zone")
    uploaded_files = st.file_uploader("Upload ZIPs, Code, Docs, Media", accept_multiple_files=True)
    raw_text = st.text_area("Paste Chat Logs / Errors", height=300)

with col2:
    st.subheader("📤 Output Zone")
    
    if st.button("🚀 ANALYZE & DISTILL STATE"):
        if not api_key:
            st.error("⚠️ Please enter your Google API Key in the Sidebar.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro-latest')
                
                status_text = st.empty()
                progress_bar = st.progress(0)
                gemini_payload = []
                
                # System Prompt
                gemini_payload.append(f"""
                ROLE: Senior Technical Lead.
                GOAL: Create a 'State Snapshot' for a project handoff.
                MODE: {audit_mode}
                INSTRUCTIONS:
                1. Read all files (including those extracted from ZIPs).
                2. Identify the LATEST state. Ignore old errors if newer code fixes them.
                3. Output a clean Markdown 'SYSTEM INJECTION' prompt containing:
                   - Project Summary
                   - Current Active Code (Only relevant parts)
                   - Known Issues
                   - Immediate Next Step
                """)

                if raw_text:
                    gemini_payload.append(f"--- MANUAL PASTE ---\n{raw_text}")

                # File Processing
                if uploaded_files:
                    status_text.info("📂 Unzipping and reading files...")
                    
                    for file in uploaded_files:
                        file_name = file.name
                        file_bytes = file.getvalue()
                        
                        # CASE A: ZIP FILE
                        if file_name.endswith('.zip'):
                            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                                for sub_name in z.namelist():
                                    if not is_junk_file(sub_name) and not sub_name.endswith('/'):
                                        content = z.read(sub_name)
                                        # Check if media inside zip (simplified: mostly text inside zips usually)
                                        processed_text = process_file_content(sub_name, content)
                                        if processed_text: 
                                            gemini_payload.append(processed_text)
                                            
                        # CASE B: AUDIO/VIDEO
                        elif file_name.split('.')[-1].lower() in ['mp3', 'wav', 'mp4', 'mov', 'avi', 'm4a']:
                            status_text.info(f"🎥 Uploading {file_name} to Brain...")
                            remote_file = upload_media_to_gemini(file_name, file_bytes)
                            gemini_payload.append(remote_file)
                            gemini_payload.append(f"\n[MEDIA CONTEXT: {file_name}]\n")
                        
                        # CASE C: REGULAR DOCS
                        else:
                            processed_text = process_file_content(file_name, file_bytes)
                            if processed_text:
                                gemini_payload.append(processed_text)

                # Call AI
                status_text.info("🧠 Distilling Logic... (This handles unlimited context)")
                progress_bar.progress(80)
                
                response = model.generate_content(gemini_payload)
                
                progress_bar.progress(100)
                status_text.success("✅ Ready!")
                
                st.code(response.text, language="markdown")
                st.info("Copy above text -> Paste into new AI.")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
