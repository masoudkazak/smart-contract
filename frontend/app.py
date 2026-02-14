import streamlit as st
import requests

BACKEND_URL = "http://backend:8000/api"

st.set_page_config(page_title="Streaming Chat & Upload", layout="wide")
st.title("💬 سیستم چت با قابلیت آپلود فایل")

with st.sidebar:
    st.header("📄 آپلود فایل")
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "یک فایل انتخاب کنید (PDF / DOCX)", 
        type=["pdf", "docx"]
    )

    if uploaded_file is not None:
        if st.button("آپلود فایل", type="primary", use_container_width=True):
            with st.spinner("در حال آپلود فایل..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    response = requests.post(
                        f"{BACKEND_URL}/documents/upload",
                        files=files,
                        timeout=300,
                    )
                    response.raise_for_status()
                    doc = response.json()
                    st.success(f"✅ فایل با موفقیت آپلود شد!")

                except requests.exceptions.RequestException as e:
                    st.error(f"❌ خطا در آپلود: {e}")

    st.markdown("---")
    st.markdown("### ℹ️ وضعیت")
    if "conversation_id" in st.session_state and st.session_state.conversation_id:
        st.success(f"✅ مکالمه فعال: {st.session_state.conversation_id[:8]}...")
    else:
        st.info("⏳ در انتظار شروع مکالمه...")


st.header("💬 گفتگو با دستیار")

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("سوال خود را بنویسید...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    payload = {
        "question": question,
        "conversation_id": st.session_state.conversation_id,
    }

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""

        try:
            with requests.post(
                f"{BACKEND_URL}/chat/stream",
                json=payload,
                stream=True,
                timeout=300,
            ) as r:
                r.raise_for_status()

                if "X-Conversation-Id" in r.headers:
                    st.session_state.conversation_id = str(
                        r.headers["X-Conversation-Id"]
                    )

                for chunk in r.iter_content(chunk_size=None):
                    if not chunk:
                        continue

                    text = chunk.decode("utf-8")
                    full_text += text
                    placeholder.markdown(full_text + "▌")

            placeholder.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})
            
        except requests.exceptions.RequestException as e:
            st.error(f"❌ خطا در ارتباط با سرور: {e}")
