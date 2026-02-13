import streamlit as st
import requests

BACKEND_URL = "http://backend:8000"

st.set_page_config(page_title="Streaming Chat", layout="centered")
st.title("💬 Streaming Chat")

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("سوال خود را بنویسید...")

if question:
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    payload = {
        "question": question,
        "conversation_id": st.session_state.conversation_id,
    }

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""

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

    st.session_state.messages.append(
        {"role": "assistant", "content": full_text}
    )
