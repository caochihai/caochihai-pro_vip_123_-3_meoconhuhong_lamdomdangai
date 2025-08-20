import streamlit as st
import requests
import base64
from requests.exceptions import RequestException, Timeout, ConnectionError
import nltk
from underthesea import word_tokenize
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
import re
import json
import os

def clean_text(text: str) -> str:
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # remove bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # remove italic
    text = re.sub(r'#+\s*', '', text)               # remove headers
    text = re.sub(r'[^\w\s]', ' ', text)            # remove punctuation
    text = re.sub(r'\s+', ' ', text)                # normalize spaces
    return text.strip()

st.set_page_config(
    page_title="AI Document Processor",   # Tiêu đề trang (hiển thị trên tab trình duyệt)
    page_icon="📄",                       # Biểu tượng tab
    layout="wide",                        # Giao diện toàn màn hình (wide mode)
    initial_sidebar_state="expanded",     # Thanh sidebar mở mặc định
)

# 🎨 Tuỳ chỉnh CSS để kiểm soát tỷ lệ hiển thị
st.markdown(
    """
    <style>
        /* Điều chỉnh tỷ lệ tổng thể của nội dung (1.0 = giữ nguyên mặc định) */
        .block-container {
            transform: scale(1.0);
            transform-origin: top left; /* Điểm neo để scale */
        }
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_data
def load_sample_data():
    """Load sample summaries from JSON file"""
    json_file_path = "sample_summaries.json"
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"❌ File {json_file_path} not found. Please make sure the JSON file exists.")
        return {"examples": {}}

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
#st.markdown('<h1 class="main-header">📄 Document Processor</h1>', unsafe_allow_html=True)

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
    st.markdown('<h1 class="main-header">📝 Text Summarization</h1>', unsafe_allow_html=True)
    # Create tabs for URL and File Upload
    tab1, tab2 = st.tabs(["🔗 PDF from URL", "📁 Upload PDF File"])
    
    with tab1:
        # 1. SINGLE URL input – top of page
        pdf_url = st.text_input(
            "🔗 Enter PDF URL:",
            value=st.session_state.get("pdf_url", ""),
            placeholder="Paste your PDF link here...",
            help="Enter a direct link to your PDF file",
            key="unique_pdf_url_input",
        )
        st.session_state.pdf_url = pdf_url

        # --- Đường kẻ phân cách 1 (ngay dưới URL) ---
        st.markdown('<hr style="margin:0.5rem 0 1.5rem 0;">', unsafe_allow_html=True)

        # --- Layout: controls + comparison | viewer ----------------------
        col_controls, col_viewer = st.columns([1, 1.6], gap="large")

        # --- LEFT: controls & summaries --------------------------------
        with col_controls:
            # A. Generate button for URL - UNIFIED ENDPOINT
            if st.button("✨ Generate Summary", use_container_width=True, type="primary", key="url_summary"):
                if pdf_url:
                    with st.spinner("📄 Processing PDF…"):
                        try:
                            # Use correct endpoint for URL-based PDFs
                            resp = requests.post(
                                "http://1.53.58.232:8521/summarize_pdf",
                                json={"pdf_url": pdf_url},
                                timeout=300,
                            )
                            st.session_state.model_summary = (
                                resp.json().get("summary", "No summary data available.")
                                if resp.status_code == 200
                                else f"Error: {resp.status_code}"
                            )
                        except Exception as e:
                            st.session_state.model_summary = f"Error: {e}"
                else:
                    st.warning("⚠️ Please enter a PDF URL first")

            # B. Examples with Individual Sample Summaries
            st.markdown('<h3 class="section-header" style="margin-top:2rem;">📌 Examples</h3>', unsafe_allow_html=True)
            
            # Define sample summaries for each example
            sample_summaries = {
                "example1": """
**TÓM TẮT VĂN BẢN** \n
Tên văn bản: Thông tư số …/2025/TT-BTNMT ban hành Quy chuẩn kỹ thuật quốc gia về nước thải sinh hoạt và nước thải đô thị, khu dân cư tập trung (QCVN 14:2025/BTNMT).
Cơ quan ban hành: Bộ Tài nguyên và Môi trường.
Thời điểm ban hành: Năm 2025.
Người ký: Thứ trưởng Lê Công Thành.

1. **Phạm vi và đối tượng áp dụng** \n
Quy định giá trị giới hạn cho phép của các thông số ô nhiễm trong nước thải sinh hoạt, nước thải đô thị, khu dân cư tập trung khi xả ra nguồn tiếp nhận.
Áp dụng cho mọi cơ quan, tổ chức, cá nhân có hoạt động xả thải (trừ trường hợp có công trình xử lý tại chỗ).

2. **Hiệu lực và thay thế** \n
Có hiệu lực từ năm 2025 (ngày cụ thể chưa điền).
Thay thế QCVN 14:2008/BTNMT.
Giai đoạn chuyển tiếp:
Các dự án, cơ sở đã được phê duyệt hoặc nộp hồ sơ trước thời điểm hiệu lực vẫn áp dụng QCVN 14:2008/BTNMT và QCVN 40:2011/BTNMT đến hết 31/12/2031.
Từ 01/01/2032: bắt buộc áp dụng QCVN 14:2025/BTNMT.

3. **Quy định kỹ thuật** \n
Đưa ra giá trị giới hạn thông số ô nhiễm (pH, BOD5, COD/TOC, TSS, Amoni, Nitơ tổng, Photpho tổng, Coliform, Sunfua, dầu mỡ, chất hoạt động bề mặt…) tại Bảng 1 và Bảng 2.
Phân loại theo cột A, B, C tùy theo chức năng nguồn tiếp nhận nước thải (cấp nước sinh hoạt, cải thiện chất lượng môi trường, hoặc nguồn khác) và quy mô lưu lượng xả thải.

4. **Phương pháp xác định**\n
Thực hiện theo TCVN, SMEWW, ISO, US EPA Method.
Có quy định phương pháp trọng tài trong trường hợp có tranh chấp kết quả.

5. **Quản lý và tuân thủ**\n
Thông số giới hạn phải ghi rõ trong báo cáo ĐTM, giấy phép môi trường, văn bản đăng ký môi trường.
Kiểm soát thêm Clo, Chloroform nếu dùng Clo khử trùng; thông số đặc trưng khác nếu có đấu nối nước thải công nghiệp.
Quan trắc và báo cáo phải do đơn vị có giấy chứng nhận dịch vụ quan trắc môi trường thực hiện.

6. **Trách nhiệm**\n
Chủ cơ sở, dự án: đảm bảo nước thải đạt chuẩn trước khi xả; xác định đúng thông số ô nhiễm cần kiểm soát.
Cơ quan quản lý: thẩm định, cấp phép, kiểm tra giám sát.
UBND cấp tỉnh: rà soát, điều chỉnh quy chuẩn địa phương phù hợp với QCVN mới.

7. **Phụ lục kèm theo**\n
Phụ lục 1: Danh mục loại hình kinh doanh, dịch vụ được quản lý như nước thải sinh hoạt (khách sạn, nhà nghỉ, ký túc xá, cơ sở y tế, dịch vụ ăn uống, giặt là, massage, trường học, doanh trại, khu chung cư, siêu thị, công viên, bến xe, v.v.).
Phụ lục 2: Phương pháp lấy mẫu, phân tích các thông số ô nhiễm trong nước thải.\n

Thông tư 2025/TT-BTNMT ban hành QCVN 14:2025/BTNMT quy định giới hạn các thông số ô nhiễm trong nước thải sinh hoạt và nước thải đô thị, thay thế QCVN 14:2008/BTNMT. Văn bản đưa ra lộ trình áp dụng đến 2032, quy định chi tiết về giới hạn kỹ thuật, phương pháp quan trắc, trách nhiệm của cơ quan quản lý và cơ sở xả thải, đồng thời kèm phụ lục về loại hình áp dụng và phương pháp thử nghiệm.
                """,
                
                "example2": """
**TÓM TẮT VĂN BẢN**\n
Tên văn bản: Thông tư số …/2025/TT-BTNMT quy định chi tiết phạm vi điều tra cơ bản về tài nguyên điện năng lượng tái tạo và năng lượng mới.
Cơ quan ban hành: Bộ Tài nguyên và Môi trường.
Người ký: Thứ trưởng Lê Minh Ngân.
Hiệu lực: Năm 2025.

1. **Phạm vi và đối tượng áp dụng**\n
Quy định về điều tra cơ bản các dạng điện năng lượng tái tạo và năng lượng mới:
Điện mặt trời, điện gió, địa nhiệt, sóng biển, thủy triều, chất thải rắn, sinh khối, thủy điện.
Áp dụng cho cơ quan quản lý, tổ chức, cá nhân liên quan đến điều tra nguồn điện tái tạo.

2. **Nguyên tắc và yêu cầu**\n
Thu thập dữ liệu phục vụ quy hoạch điện lực và quy hoạch tỉnh.
Ưu tiên vùng có tiềm năng cao, hạ tầng lưới điện thuận lợi, khu vực thiếu điện.
Dữ liệu phải chính xác, cập nhật, tuân thủ quy chuẩn kỹ thuật.
Kinh phí từ ngân sách và nguồn hợp pháp khác.

3. **Nội dung điều tra chính**\n
Điện mặt trời: đo bức xạ, số giờ nắng, ưu tiên nơi bức xạ > 4 kWh/m²/ngày.
Điện gió: khảo sát tốc độ, hướng gió, tập trung ở ven biển, cao nguyên.
Địa nhiệt: nghiên cứu mạch nước nóng, đứt gãy địa chất.
Sóng biển: đo chiều cao, chu kỳ, mật độ năng lượng sóng.
Thủy triều: đo mực nước, biên độ triều, ưu tiên cửa sông, vịnh lớn.
Chất thải rắn: thống kê khối lượng, thành phần, ưu tiên đô thị lớn > 500 tấn/ngày.
Sinh khối: khảo sát phụ phẩm nông nghiệp, chăn nuôi, chế biến.
Thủy điện: điều tra thủy văn, sông suối, hồ chứa.

4. **Kết quả điều tra**\n
Báo cáo tổng hợp.
Bản đồ phân bố tiềm năng.
Bộ dữ liệu giấy và số hóa, lưu trữ tại Bộ Tài nguyên và Môi trường.

5. **Tổ chức thực hiện**\n
Bộ, ngành, địa phương, tổ chức, cá nhân liên quan có trách nhiệm triển khai.
Vướng mắc báo cáo Bộ TN&MT để xử lý.

Thông tư 2025/TT-BTNMT quy định chi tiết phạm vi điều tra cơ bản về tài nguyên điện năng lượng tái tạo và năng lượng mới (mặt trời, gió, địa nhiệt, sóng biển, thủy triều, chất thải, sinh khối, thủy điện). Điều tra nhằm phục vụ quy hoạch điện lực, an ninh năng lượng, phát triển bền vững, với kết quả là báo cáo, bản đồ phân bố tiềm năng và cơ sở dữ liệu quốc gia.
                """,
                
                "example3": """
**TÓM TẮT VĂN BẢN**\n
Tên văn bản: Thông tư số …/2025/TT-BNNMT sửa đổi, bổ sung Thông tư số 25/2024/TT-BNNPTNT ngày 16/12/2024.
Cơ quan ban hành: Bộ Nông nghiệp và Môi trường.
Người ký: Thứ trưởng Hoàng Trung.
Hiệu lực: Năm 2025 (ngày cụ thể sẽ ghi trong văn bản chính thức).

1. **Nội dung sửa đổi, bổ sung**\n
Điều chỉnh thông tin về tên thương phẩm và tổ chức, cá nhân đăng ký:
39 hoạt chất, 44 tên thương phẩm thay đổi thông tin tổ chức/cá nhân đăng ký.
01 hoạt chất, 01 tên thương phẩm thay đổi tên thương phẩm.
Bổ sung danh mục thuốc bảo vệ thực vật được phép sử dụng tại Việt Nam:
Thuốc trừ sâu: 132 hoạt chất, 189 tên thương phẩm.
Thuốc trừ bệnh: 112 hoạt chất, 136 tên thương phẩm.
Thuốc trừ cỏ: 32 hoạt chất, 60 tên thương phẩm.
Thuốc điều hòa sinh trưởng: 05 hoạt chất, 07 tên thương phẩm.
Thuốc trừ chuột: 05 hoạt chất, 07 tên thương phẩm.
Thuốc trừ ốc: 01 hoạt chất, 02 tên thương phẩm.
Thuốc trừ mối: 03 hoạt chất, 03 tên thương phẩm.
Thuốc khử trùng kho: 01 hoạt chất, 01 tên thương phẩm.
Thuốc bảo quản nông sản: 01 hoạt chất, 01 tên thương phẩm.
Mã số HS của các loại thuốc trên được thực hiện theo Phụ lục I của Thông tư 01/2024/TT-BNNPTNT.

2. **Hiệu lực và thi hành**
Thông tư có hiệu lực từ năm 2025.
Cục Trồng trọt và Bảo vệ thực vật, các đơn vị thuộc Bộ, Sở Nông nghiệp và Môi trường các tỉnh/thành phố, cùng tổ chức/cá nhân liên quan có trách nhiệm thi hành.
Nếu có khó khăn, vướng mắc thì phản ánh về Bộ Nông nghiệp và Môi trường để giải quyết.

Thông tư 2025/TT-BNNMT sửa đổi, bổ sung Danh mục thuốc bảo vệ thực vật theo Thông tư 25/2024, gồm điều chỉnh thông tin 40 thương phẩm/hoạt chất, bổ sung gần 300 hoạt chất với hơn 400 tên thương phẩm mới được phép sử dụng, đồng thời quy định áp dụng mã số HS thống nhất.
                """
            }
            
            ex1, ex2, ex3 = st.columns(3)
            with ex1:
                if st.button("📌 Example 1", use_container_width=True, key="ex1_url"):
                    st.session_state.pdf_url = "https://vbpl.vn/FileData/TW/Lists/vbpq/Attachments/176983/VanBanGoc_645029.pdf"
                    st.session_state.pdf_summary = sample_summaries["example1"]
                    st.rerun()
            with ex2:
                if st.button("📌 Example 2", use_container_width=True, key="ex2_url"):
                    st.session_state.pdf_url = "https://vbpl.vn/FileData/TW/Lists/vbpq/Attachments/175320/VanBanGoc_2025.%20TT%20Dieutra%20dien%20NL%20tai%20tao.pdf"
                    st.session_state.pdf_summary = sample_summaries["example2"]
                    st.rerun()
            with ex3:
                if st.button("📌 Example 3", use_container_width=True, key="ex3_url"):
                    st.session_state.pdf_url = "https://vbpl.vn/FileData/TW/Lists/vbpq/Attachments/177810/VanBanGoc_03-bnnmt.pdf"
                    st.session_state.pdf_summary = sample_summaries["example3"]
                    st.rerun()

            # --- Đường kẻ phân cách 2 (ngay dưới ví dụ) ---
            st.markdown('<hr style="margin:2rem 0;">', unsafe_allow_html=True)

            # C. Summary comparison (scrollable) for URL tab
            if st.session_state.get("pdf_summary") or st.session_state.get("model_summary"):
                st.markdown('<h3 class="section-header">📝 Summary Comparison</h3>', unsafe_allow_html=True)
                g, m = st.columns(2)
                with g:
                    st.markdown(
                        '<div style="border-left:4px solid #007bff;padding:1rem;border-radius:8px;'
                        'background:#f8f9fa;max-height:60vh;overflow-y:auto;">'
                        "<h4>Sample Summary</h4><pre style='white-space:pre-wrap;font-size:0.95rem'>"
                        f"{st.session_state.get('pdf_summary','📋 Select an example')}</pre></div>",
                        unsafe_allow_html=True,
                    )
                with m:
                    st.markdown(
                        '<div style="border-left:4px solid #28a745;padding:1rem;border-radius:8px;'
                        'background:#f0fff4;max-height:60vh;overflow-y:auto;">'
                        "<h4>Model Generated</h4><pre style='white-space:pre-wrap;font-size:0.95rem'>"
                        f"{st.session_state.get('model_summary','🤖 Click Generate Summary')}</pre></div>",
                        unsafe_allow_html=True,
                    )

                # --- SCORING SECTION ---
                if st.session_state.get("pdf_summary") and st.session_state.get("model_summary"):
                    if st.button("📊 Evaluate Summary"):
                        import re, math
                        from collections import Counter
                        
                        def tokenize(text):
                            return re.findall(r'[a-zA-ZÀ-ỹ0-9]+', re.sub(r'\*\*(.*?)\*\*', r'\1', text).lower())
                        
                        def bleu_n(ref, cand, n):
                            if len(cand) < n: return 0.0
                            ref_ng = Counter([tuple(ref[i:i+n]) for i in range(len(ref)-n+1)])
                            cand_ng = Counter([tuple(cand[i:i+n]) for i in range(len(cand)-n+1)])
                            matches = sum(min(cand_ng[ng], ref_ng[ng]) for ng in cand_ng)
                            return matches / sum(cand_ng.values()) if sum(cand_ng.values()) else 0.0
                        
                        def rouge_n(ref, cand, n):
                            if len(ref) < n: return 0.0
                            ref_ng = Counter([tuple(ref[i:i+n]) for i in range(len(ref)-n+1)])
                            cand_ng = Counter([tuple(cand[i:i+n]) for i in range(len(cand)-n+1)])
                            matches = sum(min(ref_ng[ng], cand_ng[ng]) for ng in ref_ng)
                            return matches / sum(ref_ng.values())
                        
                        def rouge_l(ref, cand):
                            m, n = len(ref), len(cand)
                            L = [[0]*(n+1) for _ in range(m+1)]
                            for i in range(1, m+1):
                                for j in range(1, n+1):
                                    if ref[i-1] == cand[j-1]:
                                        L[i][j] = L[i-1][j-1] + 1
                                    else:
                                        L[i][j] = max(L[i-1][j], L[i][j-1])
                            lcs = L[m][n]
                            if m == 0 or n == 0: return 0.0
                            recall = lcs / m
                            precision = lcs / n
                            return (2 * recall * precision) / (recall + precision) if (recall + precision) else 0.0
                        
                        ref_tokens = tokenize(st.session_state.pdf_summary)
                        cand_tokens = tokenize(st.session_state.model_summary)
                        
                        # Calculate all scores
                        b1 = bleu_n(ref_tokens, cand_tokens, 1)
                        b2 = bleu_n(ref_tokens, cand_tokens, 2)
                        b3 = bleu_n(ref_tokens, cand_tokens, 3)
                        b4 = bleu_n(ref_tokens, cand_tokens, 4)
                        r1 = rouge_n(ref_tokens, cand_tokens, 1)
                        r2 = rouge_n(ref_tokens, cand_tokens, 2)
                        rl = rouge_l(ref_tokens, cand_tokens)
                        
                        # Simple evaluation
                        avg_score = (b1 + b2 + b3 + b4 + r1 + r2 + rl) / 7
                        
                        if avg_score >= 0.3:
                            quality = "✅ Good"
                            color = "green"
                        elif avg_score >= 0.15:
                            quality = "⚠️ Average"  
                            color = "orange"
                        else:
                            quality = "❌ Poor"
                            color = "red"
                        
                        # Display results
                        st.markdown(f"**Summary Quality: <span style='color:{color}'>{quality}</span>** (Score: {avg_score:.3f})", unsafe_allow_html=True)
                        
                        # BLEU scores (top row)
                        col1, col2, col3, col4 = st.columns(4)
                        with col1: st.metric("BLEU-1", f"{b1:.3f}")
                        with col2: st.metric("BLEU-2", f"{b2:.3f}")
                        with col3: st.metric("BLEU-3", f"{b3:.3f}")
                        with col4: st.metric("BLEU-4", f"{b4:.3f}")
                        
                        # ROUGE scores (bottom row)  
                        col5, col6, col7, col8 = st.columns([1,1,1,1])
                        with col5: st.metric("ROUGE-1", f"{r1:.3f}")
                        with col6: st.metric("ROUGE-2", f"{r2:.3f}")
                        with col7: st.metric("ROUGE-L", f"{rl:.3f}")
                        with col8: st.write("")  # Empty space


        # --- RIGHT: PDF viewer -------------------------------------------
        with col_viewer:
            st.markdown('<h2 class="section-header">📖 PDF Viewer</h2>', unsafe_allow_html=True)
            if pdf_url:
                try:
                    with st.spinner("📄 Loading PDF…"):
                        pdf_data = requests.get(pdf_url, timeout=30).content
                        b64 = base64.b64encode(pdf_data).decode()
                    st.markdown(
                        f"""
                        <div style="border:1px solid #dee2e6;border-radius:8px;overflow:hidden;">
                            <iframe src="data:application/pdf;base64,{b64}"
                                    width="100%" height="1000" style="border:none;"></iframe>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                except Exception:
                    st.error("❌ Unable to load PDF. Check the URL and try again.")
            else:
                st.markdown(
                    """
                    <div style="text-align:center;padding:4rem;">
                        <div style="font-size:4rem;margin-bottom:1rem;">📄</div>
                        <h3 style="color:#666;margin-bottom:1rem;">No PDF Selected</h3>
                        <p style="color:#999;">Enter a PDF URL to view the document</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab2:
        # File upload section
        uploaded_file = st.file_uploader(
            "📁 Choose a PDF file:",
            type=['pdf'],
            help="Upload a PDF file from your computer",
            key="pdf_file_uploader"
        )
        
        # --- Đường kẻ phân cách ---
        st.markdown('<hr style="margin:0.5rem 0 1.5rem 0;">', unsafe_allow_html=True)

        # --- Layout: controls + comparison | viewer ----------------------
        col_controls_upload, col_viewer_upload = st.columns([1, 1.6], gap="large")

        # --- LEFT: controls & summaries for uploaded file --------------------------------
        with col_controls_upload:
            # A. Generate button for uploaded file - UNIFIED ENDPOINT
            if st.button("✨ Generate Summary", use_container_width=True, type="primary", key="file_summary"):
                if uploaded_file is not None:
                    with st.spinner("📄 Processing uploaded PDF…"):
                        try:
                            # Reset file pointer
                            uploaded_file.seek(0)
                            
                            # Prepare the file for upload to correct API endpoint
                            files = {"file": (uploaded_file.name, uploaded_file.read(), "application/pdf")}
                            
                            # Send to correct file upload endpoint
                            resp = requests.post(
                                "http://1.53.58.232:8521/summarize_pdf_file",
                                files=files,
                                timeout=150,
                            )
                            
                            if resp.status_code == 200:
                                st.session_state.model_summary_upload = resp.json().get("summary", "No summary data available.")
                            else:
                                st.session_state.model_summary_upload = f"Error: {resp.status_code} - {resp.text}"
                                
                        except Exception as e:
                            st.session_state.model_summary_upload = f"Error: {e}"
                        finally:
                            # Reset file pointer again
                            uploaded_file.seek(0)
                else:
                    st.warning("⚠️ Please upload a PDF file first")

            # B. File info
            if uploaded_file is not None:
                st.markdown('<h3 class="section-header" style="margin-top:2rem;">📄 File Info</h3>', unsafe_allow_html=True)
                file_details = {
                    "📋 Filename": uploaded_file.name,
                    "📊 File size": f"{uploaded_file.size / 1024:.1f} KB",
                    "🏷️ File type": uploaded_file.type
                }
                
                for label, value in file_details.items():
                    st.markdown(f"**{label}:** {value}")

            # --- Đường kẻ phân cách 2 (ngay dưới file info) ---
            st.markdown('<hr style="margin:2rem 0;">', unsafe_allow_html=True)

            # C. Summary display for uploaded file
            if st.session_state.get("model_summary_upload"):
                st.markdown('<h3 class="section-header">📝 Generated Summary</h3>', unsafe_allow_html=True)
                st.markdown(
                    '<div style="border-left:4px solid #28a745;padding:1rem;border-radius:8px;'
                    'background:#f0fff4;max-height:60vh;overflow-y:auto;">'
                    "<h4>Model Generated Summary</h4><pre style='white-space:pre-wrap;font-size:0.95rem'>"
                    f"{st.session_state.get('model_summary_upload','')}</pre></div>",
                    unsafe_allow_html=True,
                )
            
            # D. Clear results button
            if st.session_state.get("model_summary_upload"):
                if st.button("🗑️ Clear Results", use_container_width=True, key="clear_upload_results"):
                    if "model_summary_upload" in st.session_state:
                        del st.session_state.model_summary_upload
                    st.rerun()

        # --- RIGHT: PDF viewer for uploaded file ---
        with col_viewer_upload:
            st.markdown('<h2 class="section-header">📖 PDF Viewer</h2>', unsafe_allow_html=True)
            if uploaded_file is not None:
                try:
                    # Display the uploaded PDF
                    pdf_bytes = uploaded_file.read()
                    b64 = base64.b64encode(pdf_bytes).decode()
                    st.markdown(
                        f"""
                        <div style="border:1px solid #dee2e6;border-radius:8px;overflow:hidden;">
                            <iframe src="data:application/pdf;base64,{b64}"
                                    width="100%" height="1000" style="border:none;"></iframe>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    # Reset file pointer for later use
                    uploaded_file.seek(0)
                except Exception as e:
                    st.error(f"❌ Unable to display PDF: {str(e)}")
            else:
                st.markdown(
                    """
                    <div style="text-align:center;padding:4rem;">
                        <div style="font-size:4rem;margin-bottom:1rem;">📁</div>
                        <h3 style="color:#666;margin-bottom:1rem;">No PDF Uploaded</h3>
                        <p style="color:#999;">Upload a PDF file to view the document</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                    
############################## phan loai



elif function_choice == "🏷️ Document Classification":
    st.markdown('<h1 class="main-header">🏷️ Document Classification</h3></h1>', unsafe_allow_html=True)
    #st.markdown('<h3>🏷️ Document Classification</h3>', unsafe_allow_html=True)
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
        col1, col2 = st.columns(2)

        # Example 2: Agriculture Strategy
        with col1:
            if st.button("Exemple 1", use_container_width=True):
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
        with col2:
            if st.button("Exemple 2", use_container_width=True):
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
    #st.markdown('<h1 class="main-header">🤖 Q&A Chatbot</h1>', unsafe_allow_html=True)
    # Session state initialization
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("selected_question", None)
    st.session_state.setdefault("gold_answer", "")
    st.session_state.setdefault("model_answer", "")

    # Questions data with complete answers
    QUESTIONS = [
        {
            "icon": "🌱", 
            "title": "Tăng cường kiểm tra môi trường", 
            "question": "Cử tri đề nghị Bộ Tài nguyên và Môi trường chỉ đạo tăng cường kiểm tra, giám sát chặt chẽ về môi trường làng nghề, doanh nghiệp xả thải lớn trên toàn quốc và có chiến lược nghiên cứu ứng dụng khoa học công nghệ xử lý rác thải đảm bảo môi trường để các địa phương đưa vào áp dụng xử lý tại chỗ đạt yêu cầu",
            "answer": """Việc tăng cường kiểm tra, giám sát chặt chẽ về môi trường đối với các doanh nghiệp xả thải lớn, làng nghề là trách nhiệm không chỉ của Bộ Tài nguyên và Môi trường mà còn của các địa phương, đã được quy định cụ thể trong các văn bản quy phạm pháp luật, văn bản chỉ đạo như Nghị định số 19/2015/NĐ-CP ngày 14/02/2015 của Chính phủ quy định chi tiết thi hành một số Điều của Luật bảo vệ môi trường, Chỉ thị số 25/CT-TTg ngày 31/8/2016 của Thủ tướng Chính phủ về một số nhiệm vụ, giải pháp cấp bách về bảo vệ môi trường. Hiện nay, Bộ Tài nguyên và Môi trường đã xây dựng Đề án kiểm soát đặc biệt đối với các nguồn thải lớn đã được Thủ tướng Chính phủ phê duyệt và sẽ tổ chức thực hiện trong năm 2018 và các năm tiếp theo."""
        },
        {
            "icon": "🗺️", 
            "title": "Quy hoạch quỹ đất dân tộc", 
            "question": "Đề nghị Nhà nước quy hoạch quỹ đất, sắp xếp lại các khu dân cư đồng bào Mông, Dao, Khơ Mú hiện nay đang sống ở khu vực đồi, núi cao, nhỏ lẻ chuyển xuống khu vực thấp hơn sinh sống tập trung khoa học, hợp lý để khai hoang ruộng bậc thang cho đồng bào canh tác trồng lúa nước, trồng màu cạn, trồng rừng…để ổn định đời sống và có điều kiện phát triển.",
            "answer": "Để đáp ứng quỹ đất cho nhu cầu về nhà ở, đất sản xuất nông nghiệp, Bộ Tài nguyên và Môi trường đã trình Chính phủ để trình Quốc hội ban hành Nghị quyết số 134/2016/QH13 phê duyệt điều chỉnh quy hoạch sử dụng đất đến năm 2020 và kế hoạch sử dụng đất kỳ cuối (2016-2020) cấp quốc gia trong đó có bố trí quỹ ở, đất sản xuất nông nghiệp cho các nhu cầu phát triển kinh tế - xã hội cũng như giải quyết quỹ đất cho đồng bào dân tộc thiểu số."
        },
        {
            "icon": "📜", 
            "title": "Giao đất nông trường", 
            "question": "Các xã: Thành Vân, Vân Du, Thành Tâm huyện Thạch Thành, tỉnh Thanh Hóa đề nghị các ngành có liên quan giải quyết giao đất của các Nông trường Thành Vân, Vân Du, Thành Tâm cho người dân quản lý, sử dụng",
            "answer": "Theo quy định tại Điều 59 và Điều 66 Luật đất đai hiện hành thì vấn đề của cử tri kiến nghị thuộc thẩm quyền của Ủy ban nhân dân cấp tỉnh, cấp huyện. Đối với chỉ đạo của Trung ương, Bộ Tài nguyên và Môi trường báo cáo thêm: Thực hiện Nghị quyết số 28-NQ/TW, Nghị định số 170/2004/NĐ-CP, Nghị định số 200/2004/NĐ-CP và Nghị định số 118/2014/NĐ-CP, các địa phương phải rà soát lại đất đai, bàn giao về địa phương phần diện tích đất sử dụng sai mục đích, kém hoặc không hiệu quả."
        }
    ]

    def send_message(text: str, is_example: bool = False, example_index: int = None) -> None:
        """Send a message and fetch AI response."""
        if not text.strip():
            return
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": text})
        
        # If this is an example question, set the gold answer
        if is_example and example_index is not None:
            st.session_state.gold_answer = QUESTIONS[example_index]["answer"]
        else:
            st.session_state.gold_answer = ""
        
        # API call to get model response
        payload = {
            "fallback_response": "Hiện mình chưa có đủ thông tin để trả lời yêu cầu của bạn. Bạn vui lòng mô tả thêm một chút nhé!",
            "query": text,
            "collection_name": "cb92553d-c21e-4921-b036-de0bb290a773",
            "history": [], "slots": [], "activate_slots": False, "activate_history": False
        }
        
        with st.spinner("🤖 AI đang suy nghĩ..."):
            try:
                response = requests.post("http://1.53.58.232:5558/chatbot-answer/", json=payload, timeout=300)
                answer = response.json().get("message", "No response available") if response.status_code == 200 else f"⚠️ Service unavailable ({response.status_code})"
            except requests.RequestException:
                answer = "🔌 Connection issue. Please try again."
        
        # Store model answer and add to messages
        st.session_state.model_answer = answer
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.selected_question = None
        st.rerun()

    # Beautiful Header
    st.markdown("""
    <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding:2rem;border-radius:15px;margin-bottom:2rem;color:white;text-align:center;">
        <h1 style="margin:0;font-size:2.5rem;">🤖 AI Q&A Assistant</h1>
        <p style="margin:0.5rem 0 0 0;font-size:1.2rem;opacity:0.9;">
            Hỏi đáp thông minh với AI
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Main Layout: Chat + Question Selection
    col_chat, col_sidebar = st.columns([2.5, 1])

    # === CHAT SECTION ===
    with col_chat:
        # Chat header with stats
        chat_header_col1, chat_header_col2 = st.columns([3, 1])
        with chat_header_col1:
            st.markdown("### 💬 Cuộc hội thoại")
        with chat_header_col2:
            if st.button("🗑️ Xóa hết", key="clear_all", use_container_width=True):
                st.session_state.messages = []
                st.session_state.gold_answer = ""
                st.session_state.model_answer = ""
                st.session_state.selected_question = None
                st.rerun()

        # Chat messages container
        chat_container = st.container(height=400)
        with chat_container:
            if st.session_state.messages:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
            else:
                st.markdown("""
                <div style="text-align:center;padding:3rem;color:#666;">
                    <div style="font-size:4rem;margin-bottom:1rem;">💭</div>
                    <h3>Chào mừng đến với AI Assistant!</h3>
                    <p>Hãy đặt câu hỏi hoặc chọn câu hỏi mẫu bên phải →</p>
                </div>
                """, unsafe_allow_html=True)

        # Chat input
        if prompt := st.chat_input("💬 Đặt câu hỏi của bạn..."):
            send_message(prompt)

    # === SIDEBAR: Question Selection ===
    with col_sidebar:
        st.markdown("### ⚡ Chọn câu hỏi mẫu")
        
        # Create selectbox options
        question_options = ["-- Chọn câu hỏi --"] + [f"{q['icon']} {q['title']}" for q in QUESTIONS]
        
        selected_index = st.selectbox(
            "Danh sách câu hỏi:",
            options=range(len(question_options)),
            format_func=lambda x: question_options[x],
            index=0,
            key="question_selectbox"
        )
        
        # Update selected question when selectbox changes
        if selected_index > 0:
            st.session_state.selected_question = selected_index - 1
        else:
            st.session_state.selected_question = None
        
        # Question preview and action section
        if st.session_state.selected_question is not None:
            q = QUESTIONS[st.session_state.selected_question]
            
            # Enhanced question display box with fixed height and scroll
            st.markdown("### 📋 Chi tiết câu hỏi")
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                        border: 2px solid #2196f3;
                        border-radius: 12px;
                        padding: 1.5rem;
                        margin: 1rem 0;
                        height: 250px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        display: flex;
                        flex-direction: column;">
                <div style="display: flex; align-items: center; margin-bottom: 1rem; flex-shrink: 0;">
                    <span style="font-size: 2rem; margin-right: 0.5rem;">{q['icon']}</span>
                    <h4 style="margin: 0; color: #1565c0; font-weight: bold;">{q['title']}</h4>
                </div>
                <div style="background: rgba(255,255,255,0.7); 
                           padding: 1rem; 
                           border-radius: 8px;
                           border-left: 4px solid #2196f3;
                           color: #0d47a1;
                           line-height: 1.6;
                           font-size: 0.95rem;
                           flex: 1;
                           overflow-y: auto;">
                    <strong>Câu hỏi:</strong><br>
                    {q['question']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action button
            if st.button("🚀 Gửi câu hỏi này", key=f"ask_{st.session_state.selected_question}", use_container_width=True, type="primary"):
                send_message(q["question"], is_example=True, example_index=st.session_state.selected_question)

    # === ANSWER COMPARISON SECTION ===
    if st.session_state.get("gold_answer") and st.session_state.get("model_answer"):
        st.markdown("---")
        st.markdown("### 📊 So sánh câu trả lời")
        
        col_gold, col_model = st.columns(2)
        
        with col_gold:
            st.markdown("""
            <div style="border: 2px solid #ff9800;
                        border-radius: 12px;
                        background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
                        height: 400px;
                        overflow-y: auto;
                        box-shadow: 0 4px 8px rgba(255,152,0,0.2);">
                <div style="padding: 1.5rem;">
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <span style="font-size: 1.5rem; margin-right: 0.5rem;">🏆</span>
                        <h4 style="margin: 0; color: #e65100; font-weight: bold;">Câu trả lời chuẩn</h4>
                    </div>
                    <div style="background: rgba(255,255,255,0.8);
                               padding: 1rem;
                               border-radius: 8px;
                               border-left: 4px solid #ff9800;
                               color: #bf360c;
                               line-height: 1.6;
                               white-space: pre-wrap;
                               font-size: 0.9rem;">""" + 
                f"{st.session_state.gold_answer}" + 
                """</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_model:
            st.markdown("""
            <div style="border: 2px solid #4caf50;
                        border-radius: 12px;
                        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
                        height: 400px;
                        overflow-y: auto;
                        box-shadow: 0 4px 8px rgba(76,175,80,0.2);">
                <div style="padding: 1.5rem;">
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <span style="font-size: 1.5rem; margin-right: 0.5rem;">🤖</span>
                        <h4 style="margin: 0; color: #2e7d32; font-weight: bold;">AI Generated</h4>
                    </div>
                    <div style="background: rgba(255,255,255,0.8);
                               padding: 1rem;
                               border-radius: 8px;
                               border-left: 4px solid #4caf50;
                               color: #1b5e20;
                               line-height: 1.6;
                               white-space: pre-wrap;
                               font-size: 0.9rem;">""" + 
                f"{st.session_state.model_answer}" + 
                """</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Enhanced comparison actions
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("📋 Copy Câu trả lời chuẩn", use_container_width=True, type="secondary"):
                st.code(st.session_state.gold_answer, language="text")
        
        with col2:
            if st.button("🤖 Copy AI Answer", use_container_width=True, type="secondary"):
                st.code(st.session_state.model_answer, language="text")
        
        with col3:
            if st.button("🗑️ Xóa so sánh", use_container_width=True):
                st.session_state.gold_answer = ""
                st.session_state.model_answer = ""

                st.rerun()
