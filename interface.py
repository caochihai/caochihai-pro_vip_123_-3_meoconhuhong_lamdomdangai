import streamlit as st
import requests
import base64
from requests.exceptions import RequestException, Timeout, ConnectionError

st.set_page_config(
    layout="wide", 
    page_title="AI Document Processor", 
    page_icon="📄",
    initial_sidebar_state="expanded"
)

# Unified CSS for color synchronization
st.markdown("""
<style>
    /* General Reset and Base Styles */
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    /* Main Container Styles */
    .main-header {
        text-align: center;
        color: #2c3e50;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 2rem;
    }

    .section-header {
        color: #2c3e50;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 1rem 0;
    }

    /* Buttons */
    .stButton > button {
        background: #3498db;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 500;
        transition: background-color 0.3s ease;
    }

    .stButton > button:hover {
        background: #2980b9;
    }

    /* Cards and Containers */
    .floating-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }

    .summary-box {
        background: #f8f9fa;
        color: #2c3e50;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #3498db;
        max-height: 400px;
        overflow-y: auto;
        line-height: 1.6;
    }

    .chat-container {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 1.5rem;
        min-height: 400px;
        max-height: 600px;
        overflow-y: auto;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }

    /* Sample Answer and Question Boxes */
    .sample-answer-container {
        background: #f8f9fa;
        border: 2px solid #3498db;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 8px rgba(52, 152, 219, 0.1);
    }

    .sample-answer-header {
        background: #3498db;
        color: #ffffff;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .sample-answer-content {
        color: #2c3e50;
        line-height: 1.6;
        font-size: 0.95rem;
        background: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #27ae60;
    }

    .question-sample-box {
        background: #f8f9fa;
        border: 2px solid #f39c12;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .question-header {
        background: #f39c12;
        color: #ffffff;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: 600;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }

    .question-content {
        color: #2c3e50;
        line-height: 1.4;
        font-size: 0.85rem;
        font-style: italic;
    }

    /* Chatbot Specific Styles */
    .header {
        background: linear-gradient(135deg, #3498db, #2980b9);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: #ffffff;
        text-align: center;
    }

    .stats {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-top: 1.5rem;
    }

    .stat {
        background: rgba(255, 255, 255, 0.2);
        padding: 0.8rem 1.5rem;
        border-radius: 10px;
    }

    .chat-box {
        background: #ffffff;
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }

    .sidebar {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }

    .preview {
        background: #f8f9fa;
        border: 2px solid #f39c12;
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 1rem;
        max-height: 400px;
        overflow-y: auto;
    }

    .preview-answer {
        background: #f0fdf4;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #27ae60;
        line-height: 1.6;
    }

    .empty {
        text-align: center;
        padding: 3rem 2rem;
        color: #2c3e50;
    }

    .chat-section-divider {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #3498db, transparent);
        margin: 2rem 0;
    }

    @media (max-width: 768px) {
        .stats {
            flex-direction: column;
            gap: 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with separate variables for different sections
for key in ["pdf_url", "pdf_summary", "classification_summary", "agency", "messages", "chat_input_value"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else ""

# Main title
st.markdown('<h1 class="main-header">📄 Document Processor</h1>', unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("""
<div style="background: #34495e; color: white; 
           padding: 2rem; margin: -1rem -1rem 2rem -1rem; border-radius: 0 0 10px 10px;">
    <h2 style="text-align: center; margin: 0;">⚡ Functions</h2>
</div>
""", unsafe_allow_html=True)

function_choice = st.sidebar.selectbox(
    "Choose your AI tool:",
    ["📄 PDF Text Summarizer", "🏷️ Document Classification", "💬 Q&A Chatbot"],
    key="function_selector"
)


if function_choice == "📄 PDF Text Summarizer":
    # Create two columns with different ratios
    col_input, col_viewer = st.columns([1, 2], gap="large")
    
    with col_input:
        # Input section with beautiful container
        st.markdown('<div class="floating-card">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">📎 PDF Input</h2>', unsafe_allow_html=True)
        
        pdf_url = st.text_input(
            "🔗 Enter PDF URL:",
            value=st.session_state.pdf_url,
            placeholder="Paste your PDF link here...",
            help="Enter a direct link to your PDF file"
        )
        st.session_state.pdf_url = pdf_url
        
        # Stylish button
        if st.button("✨ Generate Summary", use_container_width=True, type="primary"):
            if pdf_url:
                with st.spinner("📄 Processing PDF..."):
                    try:
                        response = requests.post(
                            "http://1.53.58.232:8521/summarize_pdf",
                            json={"pdf_url": pdf_url},
                            timeout=150
                        )
                        if response.status_code == 200:
                            result = response.json()
                            if "summary" in result:
                                st.success("✅ Summary completed!")
                                # Store model summary separately from sample summary
                                st.session_state.model_summary = result["summary"]
                            else:
                                st.session_state.model_summary = "No summary data available."
                        else:
                            st.session_state.model_summary = f"Error: {response.status_code}"
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.session_state.model_summary = f"Error: {str(e)}"
            else:
                st.warning("⚠️ Please enter a PDF URL first")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Summary section with comparison
        if st.session_state.pdf_summary or (hasattr(st.session_state, 'model_summary') and st.session_state.model_summary):
            st.markdown('<div class="floating-card" style="margin-top: 2rem;">', unsafe_allow_html=True)
            st.markdown('<h2 class="section-header">📝 Summary Comparison</h2>', unsafe_allow_html=True)
            
            # Create tabs for comparison
            tab1, tab2 = st.tabs(["📋 Sample Summary", "🤖 Model Generated"])
            
            with tab1:
                if st.session_state.pdf_summary:
                    st.markdown(
                        f"""
                        <div class="summary-box" style="background-color: #f8f9fa; border-left: 4px solid #007bff;">
                            {st.session_state.pdf_summary}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.info("📋 Sample summary will appear here when you select an example")
            
            with tab2:
                if hasattr(st.session_state, 'model_summary') and st.session_state.model_summary:
                    st.markdown(
                        f"""
                        <div class="summary-box" style="background-color: #f0fff4; border-left: 4px solid #28a745;">
                            {st.session_state.model_summary}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.info("🤖 Model-generated summary will appear here after clicking 'Generate Summary'")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Example buttons section
        st.markdown('<div class="floating-card" style="margin-top: 2rem;">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">📌 Examples</h3>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📌 example 1", use_container_width=True):
                st.session_state.pdf_url = "https://vbpl.vn/FileData/TW/Lists/vbpq/Attachments/176983/VanBanGoc_645029.pdf"
                # Set sample summary for example 1
                st.session_state.pdf_summary = """
                <strong>📋 Document Summary - Example 1</strong><br><br>
                <strong>🏛️ Document Type:</strong> Government Decree<br>
                <strong>📅 Issue Date:</strong> 2024<br>
                <strong>🎯 Main Topic:</strong> Administrative Procedures and Regulations<br><br>
                
                <strong>📝 Key Points:</strong><br>
                • Establishes new administrative procedures for government agencies<br>
                • Defines responsibilities and authorities of various departments<br>
                • Outlines compliance requirements and implementation timeline<br>
                • Specifies penalties for non-compliance with regulations<br>
                • Provides guidelines for inter-agency coordination and cooperation<br><br>
                
                <strong>🎯 Objective:</strong> To streamline administrative processes and improve efficiency in government operations while ensuring transparency and accountability in public service delivery.
                """
                st.rerun()
        with col2:
            if st.button("📌 example 2", use_container_width=True):
                st.session_state.pdf_url = "https://vbpl.vn/FileData/TW/Lists/vbpq/Attachments/175320/VanBanGoc_2025.%20TT%20Dieutra%20dien%20NL%20tai%20tao.pdf"
                # Set sample summary for example 2
                st.session_state.pdf_summary = """
                <strong>📋 Document Summary - Example 2</strong><br><br>
                <strong>🏛️ Document Type:</strong> Technical Circular<br>
                <strong>📅 Issue Date:</strong> 2025<br>
                <strong>🎯 Main Topic:</strong> Renewable Energy Investigation and Assessment<br><br>
                
                <strong>📝 Key Points:</strong><br>
                • Guidelines for renewable energy resource assessment and investigation<br>
                • Technical standards for energy potential evaluation methods<br>
                • Environmental impact assessment requirements<br>
                • Data collection and reporting procedures<br>
                • Quality control measures for energy studies<br><br>
                
                <strong>🎯 Objective:</strong> To provide comprehensive technical guidelines for conducting renewable energy investigations, ensuring standardized methodologies and accurate assessment of energy potential across different regions.
                """
                st.rerun()
        with col3:
            if st.button("📌 example 3", use_container_width=True):
                st.session_state.pdf_url = "https://vbpl.vn/FileData/TW/Lists/vbpq/Attachments/177810/VanBanGoc_03-bnnmt.pdf"
                # Set sample summary for example 3
                st.session_state.pdf_summary = """
                <strong>📋 Document Summary - Example 3</strong><br><br>
                <strong>🏛️ Document Type:</strong> Ministry Circular<br>
                <strong>📅 Issue Date:</strong> 2024<br>
                <strong>🎯 Main Topic:</strong> Natural Resources and Environmental Management<br><br>
                
                <strong>📝 Key Points:</strong><br>
                • Environmental protection policies and implementation measures<br>
                • Natural resource management and conservation strategies<br>
                • Monitoring and evaluation frameworks for environmental compliance<br>
                • Coordination mechanisms between local and national authorities<br>
                • Public participation requirements in environmental decision-making<br><br>
                
                <strong>🎯 Objective:</strong> To establish comprehensive environmental management frameworks that balance economic development with environmental protection, promoting sustainable use of natural resources while ensuring ecological preservation.
                """
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_viewer:
        if pdf_url:
            st.markdown('<div class="floating-card">', unsafe_allow_html=True)
            st.markdown('<h2 class="section-header">📖 PDF Viewer</h2>', unsafe_allow_html=True)
            
            try:
                with st.spinner("📄 Loading PDF..."):
                    pdf_data = requests.get(pdf_url, timeout=30).content
                    base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                    
                # Simple PDF viewer
                st.markdown(
                    f"""
                    <div style="border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden;">
                        <iframe src="data:application/pdf;base64,{base64_pdf}" 
                               width="100%" 
                               height="800" 
                               type="application/pdf"
                               style="border: none;">
                        </iframe>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            except:
                st.error("❌ Unable to load PDF. Please check the URL and try again.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # Placeholder when no PDF is loaded
            st.markdown(
                """
                <div class="floating-card" style="text-align: center; padding: 4rem;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">📄</div>
                    <h3 style="color: #666; margin-bottom: 1rem;">No PDF Selected</h3>
                    <p style="color: #999;">Enter a PDF URL to view the document here</p>
                </div>
                """,
                unsafe_allow_html=True
            )


############################## phan loai



elif function_choice == "🏷️ Document Classification":
    st.markdown('<h3>🏷️ Document Classification</h3>', unsafe_allow_html=True)
    col_input, col_viewer = st.columns([1, 2], gap="large")
    with col_input:
        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown('<h4>📝 Document Information</h4>', unsafe_allow_html=True)
        classification_summary = st.text_area(
            "Document Summary:",
            height=120,
            value=st.session_state.classification_summary,
            placeholder="Enter document summary here..."
        )
        agency = st.text_input(
            "Issuing Agency:",
            value=st.session_state.agency,
            placeholder="Enter the issuing agency..."
        )
        st.session_state.classification_summary = classification_summary
        st.session_state.agency = agency
        if st.button("🔍 Classify Document", type="primary", use_container_width=True):
            if not classification_summary or not agency:
                st.warning("⚠️ Please fill in both Summary and Agency fields")
            elif len(classification_summary) < 5 or len(agency) < 5:
                st.warning("⚠️ Text too short. Please enter at least 5 characters for Summary and Agency")
            else:
                with st.spinner("🔍 Classifying document..."):
                    try:
                        response = requests.post(
                            "http://1.53.58.232:8888/classify",
                            json={"summary": classification_summary, "issuing_agency": agency},
                            timeout=30
                        )
                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ Classification complete!")
                            st.markdown('<h4>📋 Classification Results</h4>', unsafe_allow_html=True)
                            col_label, col_other = st.columns([1, 1])
                            with col_label:
                                # Use actual_label from session_state if available, otherwise from API response
                                if hasattr(st.session_state, 'actual_label') and st.session_state.actual_label:
                                    actual_label = st.session_state.actual_label
                                else:
                                    actual_label = result.get("label", ["Not provided in response"]) if isinstance(result, dict) else ["Not provided"]
                                
                                if not isinstance(actual_label, list):
                                    actual_label = [actual_label]
                                
                                st.markdown(
                                    """
                                    <div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                                        <strong>Actual Label:</strong>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                for label in actual_label:
                                    st.markdown(
                                        f"""
                                        <div style='background-color: #e6e8ed; padding: 8px; border-radius: 5px; margin-bottom: 5px;'>
                                            {label}
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                            with col_other:
                                # Get predicted labels from API response
                                predicted_labels = []
                                if isinstance(result, dict):
                                    for key, value in result.items():
                                        if isinstance(value, list):
                                            predicted_labels.extend(value)
                                        elif isinstance(value, dict):
                                            for sub_key, sub_value in value.items():
                                                if isinstance(sub_value, list):
                                                    predicted_labels.extend(sub_value)
                                                else:
                                                    predicted_labels.append(str(sub_value))
                                        else:
                                            predicted_labels.append(str(value))
                                else:
                                    predicted_labels.append(str(result))
                                
                                st.markdown(
                                    """
                                    <div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                                        <strong>Predicted Labels:</strong>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                
                                # Display predicted labels with highlighting
                                if isinstance(result, dict):
                                    for key, value in result.items():
                                        if key != "label":
                                            if isinstance(value, list):
                                                for item in value:
                                                    # Check if this predicted label matches any actual label
                                                    is_correct = str(item) in [str(al) for al in actual_label] if hasattr(st.session_state, 'actual_label') and st.session_state.actual_label else False
                                                    bg_color = "#d4edda" if is_correct else "#f8d7da"  # Green for correct, red for incorrect
                                                    border_color = "#c3e6cb" if is_correct else "#f5c6cb"
                                                    st.markdown(
                                                        f"""
                                                        <div style='background-color: {bg_color}; border: 1px solid {border_color}; padding: 8px; border-radius: 5px; margin-bottom: 5px;'>
                                                            {item} {'✅' if is_correct else '❌'}
                                                        </div>
                                                        """,
                                                        unsafe_allow_html=True
                                                    )
                                            elif isinstance(value, dict):
                                                for sub_key, sub_value in value.items():
                                                    is_correct = str(sub_value) in [str(al) for al in actual_label] if hasattr(st.session_state, 'actual_label') and st.session_state.actual_label else False
                                                    bg_color = "#d4edda" if is_correct else "#f8d7da"
                                                    border_color = "#c3e6cb" if is_correct else "#f5c6cb"
                                                    st.markdown(
                                                        f"""
                                                        <div style='background-color: {bg_color}; border: 1px solid {border_color}; padding: 8px; border-radius: 5px; margin-bottom: 5px;'>
                                                            <strong>{sub_key}:</strong> {sub_value} {'✅' if is_correct else '❌'}
                                                        </div>
                                                        """,
                                                        unsafe_allow_html=True
                                                    )
                                            else:
                                                is_correct = str(value) in [str(al) for al in actual_label] if hasattr(st.session_state, 'actual_label') and st.session_state.actual_label else False
                                                bg_color = "#d4edda" if is_correct else "#f8d7da"
                                                border_color = "#c3e6cb" if is_correct else "#f5c6cb"
                                                st.markdown(
                                                    f"""
                                                    <div style='background-color: {bg_color}; border: 1px solid {border_color}; padding: 8px; border-radius: 5px; margin-bottom: 5px;'>
                                                        {value} {'✅' if is_correct else '❌'}
                                                    </div>
                                                    """,
                                                    unsafe_allow_html=True
                                                )
                                else:
                                    is_correct = str(result) in [str(al) for al in actual_label] if hasattr(st.session_state, 'actual_label') and st.session_state.actual_label else False
                                    bg_color = "#d4edda" if is_correct else "#f8d7da"
                                    border_color = "#c3e6cb" if is_correct else "#f5c6cb"
                                    st.markdown(
                                        f"""
                                        <div style='background-color: {bg_color}; border: 1px solid {border_color}; padding: 8px; border-radius: 5px; margin-bottom: 5px;'>
                                            {result} {'✅' if is_correct else '❌'}
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                        else:
                            st.error(f"❌ Error: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

        st.markdown('<h4>📌 Examples</h4>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)

        # Example 1: Religious Law
        with col1:
            if st.button("Exemple 1", use_container_width=True):
                st.session_state.classification_summary = "Nghị định quy định chi tiết một số điều và biện pháp thi hành Luật tín ngưỡng, tôn giáo"
                st.session_state.agency = "Văn phòng Chính phủ"
                st.session_state.example_pdf_url = "https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/01/95-cp.signed.pdf"
                st.session_state.actual_label = [s.lower() for s in[
                    "Vụ Pháp chế", "Vụ Đất đai", "Cục Biển và Hải đảo Việt Nam", "Cục Đăng ký và Dữ liệu thông tin đất đai",
                    "Cục Quy hoạch và Phát triển tài nguyên đất", "Viện Khoa học môi trường, biển và hải đảo",
                    "Vụ Môi trường", "Tổng cục Khí tượng Thuỷ văn", "Cục Bảo tồn thiên nhiên và Đa dạng sinh học",
                    "Cục Kiểm soát ô nhiễm môi trường", "Cục Biến đổi khí hậu", "Cục Quản lý Tài nguyên nước",
                    "Cục Viễn thám Quốc gia"
                ]]
                st.rerun()

        # Example 2: Agriculture Strategy
        with col2:
            if st.button("Exemple 2", use_container_width=True):
                st.session_state.classification_summary = "Phê duyệt Chiến lược phát triển trồng trọt đến năm 2030, tầm nhìn đến năm 2050"
                st.session_state.agency = "Thủ tướng Chính phủ"
                st.session_state.example_pdf_url = "https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/01/1748-ttg.signed.pdf"
                st.session_state.actual_label = [s.lower() for s in[
                    "Vụ Môi trường", "Tổng cục Khí tượng Thuỷ văn", "Cục Bảo tồn thiên nhiên và Đa dạng sinh học",
                    "Cục Kiểm soát ô nhiễm môi trường", "Cục Biến đổi khí hậu", "Cục Quản lý Tài nguyên nước",
                    "Cục Viễn thám Quốc gia", "Vụ Pháp chế", "Vụ Tổ chức cán bộ", "Cục Đo đạc, Bản đồ và Thông tin địa lý Việt Nam",
                    "Vụ Đất đai", "Cục Biển và Hải đảo Việt Nam", "Cục Đăng ký và Dữ liệu thông tin đất đai",
                    "Cục Quy hoạch và Phát triển tài nguyên đất", "Viện Khoa học môi trường, biển và hải đảo", "Vụ Kế hoạch - Tài chính"
                ]]
                st.rerun()

        # Example 3: Overseas Vietnamese Committee
        with col3:
            if st.button("Exemple 3", use_container_width=True):
                st.session_state.classification_summary = "Quyết định Quy định chức năng, nhiệm vụ, quyền hạn và cơ cấu tổ chức của Ủy ban Nhà nước về người Việt Nam ở nước ngoài trực thuộc Bộ Ngoại giao"
                st.session_state.agency = "Thủ tướng Chính phủ"
                st.session_state.example_pdf_url = "https://datafiles.chinhphu.vn/cpp/files/vbpq/2023/12/30-qdttg.signed.pdf"
                st.session_state.actual_label = [s.lower() for s in[
                    "Vụ Đất đai", "Cục Biển và Hải đảo Việt Nam", "Cục Đăng ký và Dữ liệu thông tin đất đai",
                    "Cục Quy hoạch và Phát triển tài nguyên đất", "Viện Khoa học môi trường, biển và hải đảo",
                    "Vụ Kế hoạch - Tài chính", "Vụ Pháp chế", "Vụ Tổ chức cán bộ", "Thanh tra Bộ",
                    "Cục Đo đạc, Bản đồ và Thông tin địa lý Việt Nam", "Viện Khoa học Đo đạc và Bản đồ",
                    "Trường Đào tạo, bồi dưỡng cán bộ tài nguyên và môi trường", "Vụ Hợp tác quốc tế",
                    "Vụ Khoa học và Công nghệ", "Vụ Môi trường", "Cục Bảo tồn thiên nhiên và Đa dạng sinh học",
                    "Cục Kiểm soát ô nhiễm môi trường", "Viện Chiến lược, Chính sách Tài nguyên và Môi trường",
                    "Trường Đại học Tài nguyên và Môi trường Hà Nội", "Trường Đại học Tài nguyên và Môi trường TP. HCM",
                    "Quỹ Bảo vệ môi trường Việt Nam"
                ]]
                st.rerun()

        st.markdown('<hr>', unsafe_allow_html=True)

    with col_viewer:
        if "example_pdf_url" not in st.session_state:
            st.session_state.example_pdf_url = ""
        if st.session_state.example_pdf_url:
            st.markdown('<hr>', unsafe_allow_html=True)
            st.markdown('<h4>📖 PDF Viewer</h4>', unsafe_allow_html=True)
            with st.spinner("📄 Loading PDF..."):
                pdf_data = requests.get(st.session_state.example_pdf_url, timeout=30).content
                base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                st.markdown(
                    f"""
                    <embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf">
                    """,
                    unsafe_allow_html=True
                )
            st.markdown('<hr>', unsafe_allow_html=True)
        else:
            st.markdown(
                """
                <div style='text-align: center;'>
                    <h4>📄 No PDF Selected</h4>
                    <p>Select an example to view the document here</p>
                </div>
                """,
                unsafe_allow_html=True
            )



##################################### chatbot

elif function_choice == "💬 Q&A Chatbot":
    # Session state initialization
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("selected_question", None)

    # Questions data with complete answers
    QUESTIONS = [
        {
            "icon": "🌱", 
            "title": "Tăng cường kiểm tra, giám sát môi trường và ứng dụng công nghệ xử lý rác", 
            "text": "Quick Question 1",
            "question": "Cử tri đề nghị Bộ Tài nguyên và Môi trường chỉ đạo tăng cường kiểm tra, giám sát chặt chẽ về môi trường làng nghề, doanh nghiệp xả thải lớn trên toàn quốc và có chiến lược nghiên cứu ứng dụng khoa học công nghệ xử lý rác thải đảm bảo môi trường để các địa phương đưa vào áp dụng xử lý tại chỗ đạt yêu cầu",
            "answer": """Việc tăng cường kiểm tra, giám sát chặt chẽ về môi trường đối với các doanh nghiệp xả thải lớn, làng nghề là trách nhiệm không chỉ của Bộ Tài nguyên và Môi trường mà còn của các địa phương, đã được quy định cụ thể trong các văn bản quy phạm pháp luật, văn bản chỉ đạo như Nghị định số 19/2015/NĐ-CP ngày 14/02/2015 của Chính phủ quy định chi tiết thi hành một số Điều của Luật bảo vệ môi trường, Chỉ thị số 25/CT-TTg ngày 31/8/2016 của Thủ tướng Chính phủ về một số nhiệm vụ, giải pháp cấp bách về bảo vệ môi trường. Hiện nay, Bộ Tài nguyên và Môi trường đã xây dựng Đề án kiểm soát đặc biệt đối với các nguồn thải lớn đã được Thủ tướng Chính phủ phê duyệt và sẽ tổ chức thực hiện trong năm 2018 và các năm tiếp theo. Đối với kiến nghị về chiến lược nghiên cứu ứng dụng khoa học công nghệ xử lý rác thải đảm bảo môi trường để các địa phương đưa vào áp dụng xử lý tại chỗ đạt yêu cầu: về cơ bản hiện nay ở Việt Nam đã có đầy đủ các công nghệ để xử lý mọi loại chất thải đặc thù phát sinh từ các hoạt động sản xuất, kinh doanh, dịch vụ cũng như các loại chất thải sinh hoạt. Với vai trò quản lý nhà nước về bảo vệ môi trường, Bộ Tài nguyên và Môi trường cũng đã ban hành Quy chuẩn kỹ thuật quốc gia về lò đốt chất thải rắn sinh hoạt (QCVN 61-MT:2016/BTNMT). Theo quy định tại Khoản i Mục 6 Điều 2 Nghị định số 20/2013/NĐ-CP ngày 26/2/2014 của Chính phủ quy định chức năng, nhiệm vụ, quyền hạn và cơ cấu tổ chức của Bộ Khoa học và Công nghệ; Khoản 3 Điều 27 Nghị định số 38/2015/NĐ-CP ngày 24/4/2015 của Chính phủ về quản lý chất thải và phế liệu, hiện nay Bộ Khoa học và Công nghệ là cơ quan được giao chủ trì hướng dẫn việc đánh giá, thẩm định công nghệ nói chung, thẩm định công nghệ xử lý chất thải rắn sinh hoạt mới được nghiên cứu và áp dụng lần đầu ở Việt Nam và đề xuất công nghệ xử lý chất thải rắn tiên tiến, hiệu quả để triển khai áp dụng nói riêng. Ngoài ra, tại Quyết định số 798/QĐ-TTg ngày 25/5/2011 của Thủ tướng Chính phủ phê duyệt Chương trình đầu tư xử lý chất thải rắn giai đoạn 2011 - 2020 trong đó giao Bộ Khoa học và Công nghệ rà soát, đánh giá, tổ chức nghiên cứu, đề xuất công nghệ xử lý chất thải rắn tiên tiến, hiệu quả để triển khai áp dụng."""
        },
        {
            "icon": "🏡", 
            "title": "Xử lý rác thải nông thôn, hỗ trợ địa phương và tăng chế tài xử phạt", 
            "text": "Quick Question 2",
            "question": "Tình trạng rác thải ở nông thôn rất lớn, không còn nơi chôn lấp, không có kinh phí để đầu tư công nghệ đốt, xử lý rác thải, gây ô nhiễm môi trường, ảnh hưởng đến sức khỏe của nhân dân. Đề nghị Chính phủ có phương án xử lý, khắc phục, thực hiện nghiêm túc quy trình xử lý rác thải; có cơ chế, chính sách hỗ trợ các địa phương trong việc xử lý rác thải; đồng thời, ban hành chế tài xử phạt vi phạm, ô nhiễm môi trường với xu hướng nghiêm khắc hơn, có tính răn đe cao để ngăn ngừa các hành vi vi phạm pháp luật môi trường tái diễn.",
            "answer": "Chính phủ đã ban hành Nghị định số 38/2015/NĐ-CP ngày 24/4/2015 về quản lý chất thải và phế liệu; Bộ Tài nguyên và Môi trường đã ban hành Quy chuẩn kỹ thuật quốc gia về nước thải bãi chôn lấp chất thải rắn (QCVN 25 :2009/BTNMT); Quy chuẩn kỹ thuật quốc gia về lò đốt chất thải rắn sinh hoạt (QCVN 61-MT: 2016/BTNMT);... Bên cạnh đó, Bộ Tài nguyên và Môi trường tham mưu, trình Chính phủ ban hành nhiều cơ chế, chính sách nhằm khuyến khích, ưu đãi, hỗ trợ dự án đầu tư xử lý chất thải rắn, cụ thể: - Nghị định số 19/2015/NĐ-CP ngày 14/02/2015 của Chính phủ quy định chi tiết thi hành một số điều của Luật bảo vệ môi trường đã quy định các chính sách hỗ trợ kinh phí cho hoạt động xử lý chất thải rắn (hỗ trợ về đầu tư xây dựng các công trình hạ tầng; ưu đãi về tiền thuê đất; hỗ trợ tiền bồi thường, giải phóng mặt bằng; ưu đãi về thuế thu nhập doanh nghiệp,…); - Nghị định số 15/2015/NĐ-CP ngày 14/02/2015 của Chính phủ về đầu tư theo hình thức đối tác công tư cũng quy định đối với lĩnh vực đầu tư vào hệ thống thu gom, xử lý nước thải, chất thải, các địa phương có thêm kênh thu hút vốn để tháo gỡ nút thắt trong các dự án đầu tư cơ sở xử lý chất thải rắn). Song song với các giải pháp về mặt chính sách, Bộ Tài nguyên và Môi trường đã triển khai thử nghiệm mô hình thu gom, vận chuyển và xử lý chất thải rắn sinh hoạt khu vực nông thôn; đã tổ chức các hoạt động truyền thông nâng cao nhận thức của người dân; đào tạo và tổ chức các khoá tập huấn cho doanh nghiệp về sản xuất sạch hơn, hoạt động giảm thiểu phát sinh chất thải rắn; quy trình thu gom, vận chuyển, xử lý, tái chế chất thải rắn theo đúng các quy định của pháp luật. Hàng năm, Bộ Tài nguyên và Môi trường chủ trì, phối hợp với UBND cấp tỉnh trình Thủ tướng Chính phủ phê duyệt nguồn kinh phí hỗ trợ từ ngân sách nhà nước đối với các cơ sở gây ô nhiễm môi trường nghiêm trọng. Ủy ban nhân dân cấp tỉnh đã ban hành quy hoạch quản lý chất thải rắn, quy định cụ thể về quản lý chất thải rắn sinh hoạt trên địa bàn cho phù hợp với thực tế của địa phương. Tỷ lệ thu gom, xử lý chất thải rắn tại các khu vực nông thôn tăng dần theo các năm. - Đối với kiến nghị “ban hành chế tài xử phạt vi phạm, ô nhiễm môi trường với xu hướng nghiêm khắc hơn, có tính răn đe cao để ngăn ngừa các hành vi vi phạm pháp luật môi trường tài diễn”: Bộ Tài nguyên và Môi trường đã tham mưu cho Chính phủ ban hành Nghị định số 155/2016/NĐ-CP ngày 18/11/2016 về xử phạt vi phạm hành chính trong lĩnh vực bảo vệ môi trường. Nghị định 155/2016/NĐ-CP được ban hành sẽ tác động mạnh mẽ đến ý thức và nhận thức của cá nhân, tổ chức trong công tác bảo vệ môi trường; buộc các cá nhân, tổ chức phải đầu tư kinh phí cho công tác bảo vệ môi trường trong quá trình hoạt động sản xuất, kinh doanh và dịch vụ trên lãnh thổ Việt Nam. Mức phạt tiền của Nghị định số 155/2016/NĐ-CP được xây dựng theo quy định của Luật Xử lý vi phạm hành chính. Hiện nay, mức phạt tiền đối với hành vi vi phạm hành chính về bảo vệ môi trường là cao nhất trong các lĩnh vực xử lý vi phạm hành chính ở Việt Nam (mức phạt tiền từ cảnh cáo đến 01 tỷ đồng đối với cá nhân và 02 tỷ đồng đối với tổ chức). Trước đây, Nghị định số 179/2013/NĐ-CP đã có tính răn đe cao, tuy nhiên Nghị định số 155/2016/NĐ-CP hiện nay còn có tính răn đe cao hơn đối với các hành vi cố ý gây ô nhiễm môi trường (như trước đây hành vi xả nước thải vượt quy chuẩn cho phép trên 10 lần với lưu lượng nước thải trên 10.000 m3/ngày đêm thì mức phạt tiền là tối đa, hiện nay chỉ cần xả nước thải vượt trên 10 lần với lưu lượng lớn hơn 5.000 m3/ngày.đêm nhưng dưới mức tội phạm môi trường theo quy định của Bộ luật Hình sự thì đã bị xử phạt ở mức tối đa). Bên cạnh hình thức phạt tiền, Nghị định số 155/2016/NĐ-CP còn quy định các hình thức xử phạt bổ sung (đình chỉ hoạt động, tước quyền sử dụng giấy phép môi trường, tịch thu tang vật vi phạm), biện pháp khắc phục hậu quả (buộc khắc phục lại tình trang ô nhiễm môi trường đã bị ô nhiễm và phục hồi môi trường bị ô nhiễm) và công khai thông tin đối với hành vi vi phạm nghiêm trọng, gây ô nhiễm môi trường hoặc tác động xấu đến xã hội,… Ngoài công cụ xử phạt vi phạm hành chính theo Nghị định 155/2016/NĐ-CP nêu trên, Quốc hội đã thông qua Bộ Luật hình sự số 100/2015/QH13 và Luật sửa đổi, bổ sung một số điều của Bộ luật hình sự năm 2015, trong đó đã định lượng các hành vi vi phạm gây ô nhiễm môi trường để xử lý trách nhiệm đối với cá nhân, tổ chức vi phạm. Đây là một công cụ hữu hiệu để răn đe cá nhân, tổ chức cố tình trốn tránh trách nhiệm để thực hiện các hành vi cố ý gây ô nhiễm môi trường."
        },
        {
            "icon": "🗺️", 
            "title": "Quy hoạch quỹ đất và sắp xếp khu dân cư cho đồng bào dân tộc", 
            "text": "Quick Question 3",
            "question": "Đề nghị Nhà nước quy hoạch quỹ đất, sắp xếp lại các khu dân cư đồng bào Mông, Dao, Khơ Mú hiện nay đang sống ở khu vực đồi, núi cao, nhỏ lẻ chuyển xuống khu vực thấp hơn sinh sống tập trung khoa học, hợp lý để khai hoang ruộng bậc thang cho đồng bào canh tác trồng lúa nước, trồng màu cạn, trồng rừng…để ổn định đời sống và có điều kiện phát triển.",
            "answer": "Để đáp ứng quỹ đất cho nhu cầu về nhà ở, đất sản xuất nông nghiệp, Bộ Tài nguyên và Môi trường đã trình Chính phủ để trình Quốc hội ban hành Nghị quyết số 134/2016/QH13 phê duyệt điều chỉnh quy hoạch sử dụng đất đến năm 2020 và kế hoạch sử dụng đất kỳ cuối (2016-2020) cấp quốc gia trong đó có bố trí quỹ ở, đất sản xuất nông nghiệp cho các nhu cầu phát triển kinh tế - xã hội cũng như giải quyết quỹ đất cho đồng bào dân tộc thiểu số. Đồng thời, Bộ cũng đã thẩm định trình Chính phủ xem xét phê duyệt điều chỉnh quy hoạch sử dụng đất đến năm 2020 và kế hoạch sử dụng đất kỳ cuối (2016-2020) tỉnh Thanh Hóa (Tờ trình số 93/TTR-BTNMT ngày 16/11/2017). Trên cơ sở, điều chỉnh quy hoạch sử dụng đất đến năm 2020 và kế hoạch sử dụng đất kỳ cuối (2016-2020) của tỉnh được phê duyệt, Ủy ban nhân dân tỉnh Thanh Hóa chỉ đạo Ủy ban nhân dân các huyện triển khai lập điều chỉnh quy hoạch, kế hoạch sử dụng đất cấp huyện làm căn cứ để thực hiện chính sách giao đất cho đồng bào Mông, Dao, Khơ Mú trên địa bàn."
        },
        {
            "icon": "📜", 
            "title": "Giao đất các nông trường cho người dân quản lý, sử dụng", 
            "text": "Quick Question 4",
            "question": "Các xã: Thành Vân, Vân Du, Thành Tâm huyện Thạch Thành, tỉnh Thanh Hóa đề nghị các ngành có liên quan giải quyết giao đất của các Nông trường Thành Vân, Vân Du, Thành Tâm cho người dân quản lý, sử dụng",
            "answer": "Theo quy định tại Điều 59 và Điều 66 Luật đất đai hiện hành thì vấn đề của tri kiến nghị thuộc thẩm quyền của Ủy ban nhân dân cấp tỉnh, cấp huyện. Đối với chỉ đạo của Trung ương, Bộ Tài nguyên và Môi trường báo cáo thêm như sau: Thực hiện Nghị quyết số 28-NQ/TW, Nghị định số 170/2004/NĐ-CP, Nghị định số 200/2004/NĐ-CP và Nghị định số 118/2014/NĐ-CP, các địa phương phải rà soát lại đất đai, bàn giao về địa phương phần diện tích đất sử dụng sai mục đích, kém hoặc không hiệu quả (bàn giao một phần đất hoặc toàn bộ - giải thể). Các địa phương phải xây dựng phương án sử dụng đất đối với diện tích đất này để để giao lại cho tổ chức, hộ gia đình, cá nhân hoặc chuyển thành BQL rừng... Đối với tỉnh Thanh Hóa, số liệu đất bàn giao hoặc dự kiến bàn giao về địa phương từ năm 2004 đến nay khoảng 14.675 ha (trong đó bao gồm phần diện tích đất các nông trường trên địa bàn huyện Thạch Thành bàn giao về địa phương), nhưng đến nay địa phương vẫn chưa xây dựng và tổ chức thực hiện phương án sử dụng quỹ đất này. Thực hiện Nghị quyết số 112/2015/NQ-QH13 của Quốc hội và Bộ Tài nguyên và Môi trường đã trình Thủ tướng Chính phủ ban hành Chỉ thị số 11/CT-TTg trong đó yêu cầu Ủy ban nhân dân các tỉnh, thành phố trực thuộc Trung ương tiếp nhận và có phương án đối với quỹ đất bàn giao lại cho các địa phương, đồng thời phải xây dựng và thực hiện Đề án “Tăng cường quản lý đối với đất đai có nguồn gốc từ các nông, lâm trường quốc doanh hiện do các công ty nông nghiệp, công ty lâm nghiệp không thuộc diện sắp xếp lại theo Nghị định số 118/2014/NĐ-CP, ban quản lý rừng và các tổ chức sự nghiệp khác, hộ gia đình, cá nhân sử dụng” (Đề án), trong đó bao gồm nội dung rà soát, xây dựng và thực hiện phương án sử dụng quỹ đất các nông, lâm trường bàn giao về địa phương. Bộ Tài nguyên và Môi trường đã trình Thủ tướng Chính phủ phê duyệt Đề án Tăng cường quản lý đối với đất đai có nguồn gốc từ các nông, lâm trường quốc doanh hiện do các công ty nông nghiệp, công ty lâm nghiệp không thuộc diện sắp xếp lại theo Nghị định số 118/2014/NĐ-CP, ban quản lý rừng và các tổ chức sự nghiệp khác, hộ gia đình, cá nhân sử dụng (Tờ trình số 21/TTR-BTNMT ngày 10/5/2017) và đã được Thủ tướng Chính phủ đồng ý về nội dung."
        }
    ]

    def send_message(text: str) -> None:
        """Send a message and fetch AI response."""
        if not text.strip():
            return
        
        st.session_state.messages.append({"role": "user", "content": text})
        
        payload = {
            "fallback_response": "Hiện mình chưa có đủ thông tin để trả lời yêu cầu của bạn. Bạn vui lòng mô tả thêm một chút nhé!",
            "query": text,
            "collection_name": "cb92553d-c21e-4921-b036-de0bb290a773",
            "history": [], "slots": [], "activate_slots": False, "activate_history": False
        }
        
        with st.spinner("🔍 AI is thinking..."):
            try:
                response = requests.post("http://1.53.58.232:5558/chatbot-answer/", json=payload, timeout=300)
                answer = response.json().get("message", "No response available") if response.status_code == 200 else f"⚠️ Service unavailable ({response.status_code})"
            except requests.RequestException:
                answer = "🔌 Connection issue. Please try again."
        
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.selected_question = None
        st.rerun()

    # Header
    total_conversations = len(st.session_state.messages) // 2
    st.markdown(f"""
    <div class="header">
        <h1>🤖 AI Q&A Assistant</h1>
        <p>Get intelligent answers to your questions instantly</p>
        <div class="stats">
            <div class="stat"><strong>{total_conversations}</strong><br>Conversations</div>
            <div class="stat"><strong>{len(st.session_state.messages)}</strong><br>Messages</div>
            <div class="stat"><strong>🟢</strong><br>Online</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Layout
    cols = [2, 1.5, 1] if st.session_state.selected_question is not None else [3, 1]
    col_chat, *other_cols = st.columns(cols)

    # Chat Section
    with col_chat:
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 💬 Chat Interface")
        with col2:
            if st.button("🗑️ Clear", key="clear_chat"):
                st.session_state.messages = []
                st.rerun()

        if st.session_state.messages:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        else:
            st.markdown('<div class="empty"><div style="font-size:3rem;margin-bottom:1rem">💭</div><h3>Welcome to AI Assistant!</h3><p>Ask me anything or try quick questions →</p></div>', unsafe_allow_html=True)

        if prompt := st.chat_input("💬 Ask your question here..."):
            send_message(prompt)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Preview (if question selected)
    if st.session_state.selected_question is not None:
        with other_cols[0]:
            q = QUESTIONS[st.session_state.selected_question]
            
            st.markdown('<div class="preview">', unsafe_allow_html=True)
            st.markdown("### 📋 Sample Q&A")
            
            st.markdown(f'<div style="background:white;padding:1rem;border-radius:10px;margin-bottom:1rem"><strong>{q["icon"]} {q["title"]}</strong><br><em>{q["question"]}</em></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="preview-answer"><strong>💡 Sample Answer</strong><br>{q["answer"]}</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Ask", key=f"ask_{st.session_state.selected_question}"):
                    send_message(q["question"])
            with col2:
                if st.button("❌ Close", key=f"close_{st.session_state.selected_question}"):
                    st.session_state.selected_question = None
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

    # Sidebar
    with other_cols[-1]:
        st.markdown('<div class="sidebar">', unsafe_allow_html=True)
        st.markdown("### ⚡ Quick Start")
        
        for i, q in enumerate(QUESTIONS):
            button_label = f"{q['icon']} {q['title']}\n{q['text']}"
            if st.button(button_label, key=f"quick_{i}"):
                if st.session_state.selected_question == i:
                    pass
                else:
                    st.session_state.selected_question = i
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)