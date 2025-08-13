import streamlit as st
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

for key in ["pdf_url", "summary", "agency", "messages", "chat_input_value"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else ""

st.title("Text Processing Interface")
function_choice = st.sidebar.selectbox(
    "Choose function:",
    ["PDF Text Summarizer", "Document Classification", "Q&A Chatbot"]
)

if function_choice == "PDF Text Summarizer":
    st.header("PDF Text Summarizer")
    col1, col2 = st.columns([3, 1])

    with col1:
        pdf_url = st.text_input("Enter PDF URL:", value=st.session_state.pdf_url)
        st.session_state.pdf_url = pdf_url
        if st.button("Summarize PDF", type="primary"):
            if pdf_url:
                try:
                    with st.spinner("Processing PDF... This may take a while."):
                        response = requests.post(
                            "http://1.53.58.232:8521/summarize_pdf", 
                            json={"pdf_url": pdf_url},
                            timeout=60  # Increased timeout for PDF processing
                        )
                        if response.status_code == 200:
                            result = response.json()
                            if "summary" in result:
                                st.success("Summary generated!")
                                st.markdown(result["summary"])
                            else:
                                st.json(result)
                        else:
                            st.error(f"Error: {response.status_code}")
                except Timeout:
                    st.error("⏱️ Request timed out. The server is taking too long to respond. Please try again later.")
                except ConnectionError:
                    st.error("🔌 Connection error. Please check if the server is running and accessible.")
                except RequestException as e:
                    st.error(f"❌ Request failed: {str(e)}")
            else:
                st.warning("Please enter a PDF URL")

    with col2:
        st.markdown("**Examples**")
        if st.button("example 1"):
            st.session_state.pdf_url = "https://vbpl.vn/FileData/TW/Lists/vbpq/Attachments/176983/VanBanGoc_645029.pdf"
            st.rerun()
        if st.button("example 2"):
            st.session_state.pdf_url = "https://vbpl.vn/FileData/TW/Lists/vbpq/Attachments/175320/VanBanGoc_2025.%20TT%20Dieutra%20dien%20NL%20tai%20tao.pdf"
            st.rerun()
        if st.button("example 3"):
            st.session_state.pdf_url = "https://vbpl.vn/FileData/TW/Lists/vbpq/Attachments/177810/VanBanGoc_03-bnnmt.pdf"
            st.rerun()

elif function_choice == "Document Classification":
    st.header("Document Classification")
    col1, col2 = st.columns([3, 1])

    with col1:
        summary = st.text_area("Document Summary:", height=120, value=st.session_state.summary)
        agency = st.text_input("Issuing Agency:", value=st.session_state.agency)
        st.session_state.summary = summary
        st.session_state.agency = agency
        if st.button("Classify Document", type="primary"):
            if not summary or not agency:
                st.warning("Please fill in both fields")
            elif len(summary) < 5 or len(agency) < 5:
                st.warning("Text too short. Please enter at least 5 characters in both fields")
            else:
                try:
                    with st.spinner("Classifying document..."):
                        response = requests.post(
                            "http://1.53.58.232:8888/classify", 
                            json={"summary": summary, "issuing_agency": agency},
                            timeout=30  # 30 second timeout
                        )
                        if response.status_code == 200:
                            result = response.json()
                            st.success("Classification complete!")
                            if isinstance(result, dict):
                                for key, value in result.items():
                                    st.subheader(key.replace('_', ' ').title())
                                    if isinstance(value, list):
                                        for item in value:
                                            st.write(f"• {item}")
                                    elif isinstance(value, dict):
                                        for sub_key, sub_value in value.items():
                                            st.write(f"**{sub_key}:** {sub_value}")
                                    else:
                                        st.write(value)
                            else:
                                st.write(result)
                        else:
                            st.error(f"Error: {response.status_code}")
                except Timeout:
                    st.error("⏱️ Request timed out. The classification service is taking too long to respond.")
                except ConnectionError:
                    st.error("🔌 Connection error. Please check if the server is running.")
                except RequestException as e:
                    st.error(f"❌ Request failed: {str(e)}")

    with col2:
        st.markdown("**Examples**")
        if st.button("example 1"):
            st.session_state.summary = "Nghị định quy định chi tiết một số điều và biện pháp thi hành Luật tín ngưỡng, tôn giáo"
            st.session_state.agency = "Văn phòng Chính phủ"
            st.rerun()
        if st.button("example 2"):
            st.session_state.summary = "Phê duyệt Chiến lược phát triển trồng trọt đến năm 2030, tầm nhìn đến năm 2050"
            st.session_state.agency = "Thủ tướng Chính phủ"
            st.rerun()

elif function_choice == "Q&A Chatbot":
    col_header, col_clear = st.columns([3, 1])
    with col_header:
        st.header("Q&A Chatbot")
    with col_clear:
        if st.button("Clear Chat", type="secondary"):
            st.session_state.messages = []
            if "pending_question" in st.session_state:
                del st.session_state.pending_question
            if "selected_question" in st.session_state:
                del st.session_state.selected_question
            st.rerun()

    total_conversations = len(st.session_state.messages) // 2
    st.caption(f"Total conversations: {total_conversations}")
    col1, col2 = st.columns([3, 1])

    if "pending_question" not in st.session_state:
        st.session_state.pending_question = ""
    if "selected_question" not in st.session_state:
        st.session_state.selected_question = None

    def send_message(text):
        if not text.strip():
            return
        
        st.session_state.messages.append({"role": "user", "content": text})
        
        payload = {
            "fallback_response": "Hiện mình chưa có đủ thông tin để trả lời yêu cầu của bạn. Bạn vui lòng mô tả thêm một chút nhé!",
            "query": text,
            "collection_name": "cb92553d-c21e-4921-b036-de0bb290a773",
            "history": [],
            "slots": [],
            "activate_slots": False,
            "activate_history": False
        }
        
        try:
            with st.spinner("Getting response from chatbot..."):
                response = requests.post(
                    "http://1.53.58.232:5558/chatbot-answer/", 
                    json=payload, 
                    timeout=60  # Increased timeout to 60 seconds
                )
                if response.status_code == 200:
                    answer = response.json().get("message", "No response")
                else:
                    answer = f"Server error (Status: {response.status_code}). Please try again."
        except Timeout:
            answer = "⏱️ The chatbot is taking too long to respond. This might be due to high server load. Please try again in a moment."
        except ConnectionError:
            answer = "🔌 Unable to connect to the chatbot service. Please check your internet connection or try again later."
        except RequestException as e:
            answer = f"❌ Error communicating with chatbot: {str(e)}"
        except Exception as e:
            answer = f"❌ Unexpected error: {str(e)}"
        
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.pending_question = ""
        st.session_state.selected_question = None
        st.rerun()

    with col1:
        if st.session_state.selected_question:
            st.info("**Selected Question Preview:**")
            st.write(st.session_state.selected_question)
            col_confirm, col_cancel = st.columns([1, 1])
            with col_confirm:
                if st.button("✅ Send Question"):
                    send_message(st.session_state.selected_question)
            with col_cancel:
                if st.button("❌ Cancel"):
                    st.session_state.selected_question = None
                    st.rerun()
            st.divider()

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input("Ask your question...")
        if prompt:
            send_message(prompt)

    with col2:
        st.markdown("**Quick Questions**")
        questions = [
            ("Question 1", "nhân dân lên gặp địa chính xã để làm các thủ tục chuyển nhượng, chuyển mục đích, hợp đồng tặng cho quyền sử dụng đất. và địa chính cấp giấy tờ hợp đồng cho nhân dân. Vậy địa chính có được thu tiền giấy hợp đồng và các thu tục giấy tờ khác không? nếu được thu tiền thì thu theo quy định nào? và tiền đóng dấu UBND xã có còn thu thêm không?"),
            ("Question 2", "Việc cấp phép và giám sát khai thác tài nguyên thiên nhiên (như khoáng sản, nước ngầm) đang được cải thiện theo hướng nào để hạn chế khai thác quá mức?"),
            ("Question 3", "Công tác quản lý, giám sát chất lượng không khí và nguồn nước hiện nay được thực hiện ra sao, và có kế hoạch nâng cấp hệ thống quan trắc không?"),
            ("Question 4", "Kế hoạch xử lý ô nhiễm rác thải tại các “điểm nóng” như bãi rác Nam Sơn (Hà Nội) hoặc Đa Phước (TP.HCM) đang triển khai thế nào?")
        ]
        for label, question in questions:
            if st.button(label, key=label):
                st.session_state.selected_question = question
                st.rerun()