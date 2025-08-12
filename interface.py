import streamlit as st
import requests

st.title("Text Processing Interface")

st.sidebar.title("Select Function")
function_choice = st.sidebar.radio("Choose a function:", ["PDF Text Summarizer", "Document Classification", "Q&A Chatbot"])

if function_choice == "PDF Text Summarizer":
    st.header("📄 PDF Text Summarizer")
    
    pdf_url = st.text_input("Enter PDF URL:")
    
    if st.button("Summarize PDF", type="primary") and pdf_url.strip():
        response = requests.post("http://1.53.58.232:8521/summarize_pdf", json={"pdf_url": pdf_url})
        result = response.json()
        
        if "summary" in result:
            st.subheader("📝 Summary")
            st.write(result["summary"])
        else:
            st.json(result)

elif function_choice == "Document Classification":
    st.header("📋 Document Classification")
    
    summary = st.text_area("Document Summary:", height=150)
    issuing_agency = st.text_input("Issuing Agency:")
    
    if st.button("Classify Document", type="primary") and summary.strip() and issuing_agency.strip():
        response = requests.post("http://1.53.58.232:8686/classify", 
                               json={"summary": summary, "issuing_agency": issuing_agency})
        st.json(response.json())

elif function_choice == "Q&A Chatbot":
    st.header("🤖 Q&A Chatbot")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        payload = {
            "fallback_response": "Hiện mình chưa có đủ thông tin để trả lời yêu cầu của bạn. Bạn vui lòng mô tả thêm một chút nhé!",
            "query": prompt,
            "collection_name": "cb92553d-c21e-4921-b036-de0bb290a773",
            "history": [],
            "slots": [],
            "activate_slots": False,
            "activate_history": False
        }

        response = requests.post("http://1.53.58.232:5558/chatbot-answer/", json=payload)
        answer = response.json()["message"]

        with st.chat_message("assistant"):
            st.markdown(answer)
            
        st.session_state.messages.append({"role": "assistant", "content": answer})