import streamlit as st
import requests

BACKEND_URL = "http://backend:8000/api"

st.set_page_config(page_title="Streaming Chat & Upload", layout="wide")
st.title("💬 سیستم چت با قابلیت آپلود فایل")

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_conversation_label" not in st.session_state:
    st.session_state.selected_conversation_label = "ایجاد مکالمه جدید"

if "selected_document_label" not in st.session_state:
    st.session_state.selected_document_label = "هیچ منبعی"

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
                    st.success(f"✅ فایل با موفقیت آپلود شد!")

                except requests.exceptions.RequestException as e:
                    st.error(f"❌ خطا در آپلود: {e}")

    st.markdown("---")
    st.header("📂 لیست داکیومنت‌ها")

    try:
        response = requests.get(f"{BACKEND_URL}/documents")
        response.raise_for_status()
        documents = response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ خطا در دریافت لیست داکیومنت‌ها: {e}")
        documents = []

    doc_options = {"هیچ منبعی": None}
    for d in documents:
        label = f"{d['original_filename'].split('/')[-1]} ({d['file_type']})"
        doc_options[label] = d

    if "selected_document_label" not in st.session_state:
        st.session_state.selected_document_label = "هیچ منبعی"

    selected_doc_label = st.selectbox(
        "یک داکیومنت انتخاب کنید",
        options=list(doc_options.keys()),
        index=list(doc_options.keys()).index(st.session_state.selected_document_label),
        key="doc_selectbox"
    )
    st.session_state.selected_document_label = selected_doc_label
    selected_document = doc_options[selected_doc_label]

    if selected_document:
        st.info(f"📄 منبع فعال: {selected_document['original_filename'].split('/')[-1]}")
    else:
        st.info("📄 هیچ منبعی انتخاب نشده است")

    st.markdown("---")
    st.header("🗂️ لیست مکالمات")

    def fetch_conversations():
        try:
            response = requests.get(f"{BACKEND_URL}/conversations")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ خطا در دریافت لیست مکالمات: {e}")
            return []

    conversations = fetch_conversations()
    conv_options = {"ایجاد مکالمه جدید": None}
    for conv in conversations:
        conv_label = f"{conv['title']}"
        conv_options[conv_label] = conv['id']

    if "selected_conversation_label" not in st.session_state:
        st.session_state.selected_conversation_label = "ایجاد مکالمه جدید"

    selected_conv_label = st.selectbox(
        "یک مکالمه انتخاب کنید",
        options=list(conv_options.keys()),
        index=list(conv_options.keys()).index(st.session_state.selected_conversation_label),
        key="conv_selectbox"
    )

    if st.session_state.get("selected_conversation_label") != selected_conv_label:
        st.session_state.selected_conversation_label = selected_conv_label
        st.session_state.conversation_id = conv_options[selected_conv_label]
        st.session_state.messages = []

st.header("💬 گفتگو با دستیار")

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.conversation_id and not st.session_state.messages:
    try:
        response = requests.get(f"{BACKEND_URL}/conversations/{st.session_state.conversation_id}")
        response.raise_for_status()
        conv_data = response.json()
        st.session_state.messages = [
            {"role": m["role"], "content": m["content"]} for m in conv_data.get("messages", [])
        ]
    except requests.exceptions.RequestException as e:
        st.error(f"❌ خطا در دریافت پیام‌های مکالمه: {e}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if selected_document:
    st.markdown(f"**📄 منبع انتخاب شده برای پیام‌ها:** {selected_document['original_filename'].split('/')[-1]}")
else:
    st.markdown("**📄 هیچ منبعی انتخاب نشده است**")

question = st.chat_input("سوال خود را بنویسید...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    payload = {
        "question": question,
        "conversation_id": st.session_state.conversation_id,
        "document_filename": selected_document["filename"] if selected_document else None
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
