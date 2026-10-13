import os

import requests
import streamlit as st

st.set_page_config(page_title="Customer Support Assistant", page_icon="💬", layout="centered")
st.title("Customer Support Assistant")
st.caption("Answers are based on the project's support knowledge base.")

api_url = os.getenv("RAG_API_URL", "http://127.0.0.1:8000").rstrip("/")
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources"):
                for source in message["sources"]:
                    st.write(
                        f"- {source.get('title', 'Support document')} "
                        f"(ID: {source.get('chunk_id', 'unknown')}; "
                        f"source: {source.get('source', 'knowledge base')})"
                    )

question = st.chat_input("Ask a customer-support question...")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"), st.spinner("Searching support information and preparing an answer..."):
        #try:
            try:
                response = requests.post(
                    f"{api_url}/query",
                    json={"question": question, "top_k": 4},
                    timeout=180,
                )
                response.raise_for_status()
                result = response.json()
                answer = result.get("answer", "No answer was returned.")
                sources = result.get("sources", [])
                st.markdown(answer)
                if sources:
                    with st.expander("Sources"):
                        for source in sources:
                            st.write(
                                f"- {source.get('title', 'Support document')} "
                                f"(ID: {source.get('chunk_id', 'unknown')}; "
                                f"source: {source.get('source', 'knowledge base')})"
                            )
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "sources": sources, "question": question}
                )
            except requests.RequestException as exc:
                st.error(f"Could not reach the API at {api_url}. Start the FastAPI server first. Details: {exc}")

last_answer = next(
    (m for m in reversed(st.session_state.messages) if m["role"] == "assistant" and m.get("question")),
    None,
)
if last_answer:
    st.divider()
    st.subheader("Was this answer helpful?")
    col1, col2 = st.columns(2)
    feedback_comment = st.text_input("Optional feedback comment", key="feedback_comment")
    if col1.button("👍 Helpful", use_container_width=True):
        try:
            r = requests.post(
                f"{api_url}/feedback",
                json={
                    "question": last_answer["question"],
                    "answer": last_answer["content"],
                    "rating": "positive",
                    "comment": feedback_comment,
                },
                timeout=15,
            )
            r.raise_for_status()
            st.success("Thank you! Your feedback was saved.")
        except requests.RequestException:
            st.error("Feedback could not be saved. Check that the API is running.")
    if col2.button("👎 Not helpful", use_container_width=True):
        try:
            r = requests.post(
                f"{api_url}/feedback",
                json={
                    "question": last_answer["question"],
                    "answer": last_answer["content"],
                    "rating": "negative",
                    "comment": feedback_comment,
                },
                timeout=15,
            )
            r.raise_for_status()
            st.success("Thank you. Your feedback was saved for review.")
        except requests.RequestException:
            st.error("Feedback could not be saved. Check that the API is running.")
