import streamlit as st
import sqlite3
import os
import re
import fitz  # PyMuPDF
from foundry_local_sdk import Configuration, FoundryLocalManager

# 1. Sayfa Yapılandırması
st.set_page_config(
    page_title="DocFlow",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ÖZEL CSS
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stHeader"] {background-color: transparent !important;}
        [data-testid="stHeaderRight"] {display: none !important;}
        
        .stApp {
            background-color: #0b0f19 !important;
            color: #f8fafc !important;
        }
        
        section[data-testid="stSidebar"] {
            background-color: #0f172a !important;
            border-right: 1px solid #1e293b !important;
        }
        
        section[data-testid="stSidebar"] .stButton button {
            background-color: #a5b4fc !important;
            color: #0f172a !important;
            font-weight: 600 !important;
            border-radius: 10px !important;
            border: none !important;
            padding: 0.6rem 1rem !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 0 15px rgba(165, 180, 252, 0.25) !important;
        }
        section[data-testid="stSidebar"] .stButton button:hover {
            background-color: #818cf8 !important;
            color: #ffffff !important;
            box-shadow: 0 0 20px rgba(129, 140, 248, 0.4) !important;
        }

        [data-testid="stFileUploadDropzone"],
        [data-testid="stFileUploaderDropzone"] {
            border: 2px dashed #1e293b !important; 
            border-radius: 16px !important;
            background-color: transparent !important;
            padding: 40px 10px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            transition: all 0.3s ease-in-out !important;
        }
        
        [data-testid="stFileUploadDropzone"]:hover,
        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: #3b82f6 !important;
            background-color: rgba(59, 130, 246, 0.05) !important;
        }

        [data-testid="stFileUploadDropzone"] button,
        [data-testid="stFileUploaderDropzone"] button {
            display: none !important;
            opacity: 0 !important;
            visibility: hidden !important;
            position: absolute !important;
            z-index: -999 !important;
            width: 0px !important;
            height: 0px !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        [data-testid="stFileUploadDropzone"] > div > *,
        [data-testid="stFileUploaderDropzone"] > div > * {
            display: none !important;
        }
        
        [data-testid="stFileUploadDropzone"] > div,
        [data-testid="stFileUploaderDropzone"] > div {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            gap: 12px !important; 
        }

        [data-testid="stFileUploadDropzone"]::before,
        [data-testid="stFileUploaderDropzone"]::before {
            content: '📄';
            display: flex;
            align-items: center;
            justify-content: center;
            width: 55px;
            height: 55px;
            background-color: #1e293b;
            border-radius: 50%;
            font-size: 24px;
            margin-bottom: 15px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }

        [data-testid="stFileUploadDropzone"] > div::before,
        [data-testid="stFileUploaderDropzone"] > div::before {
            content: 'Belgenizi Buraya Sürükleyin veya Dosya Seçin';
            color: #94a3b8 !important; 
            font-size: 14px;
            font-weight: 500;
            text-align: center;
        }

        [data-testid="stFileUploadDropzone"] > div::after,
        [data-testid="stFileUploaderDropzone"] > div::after {
            content: 'Desteklenen formatlar: PDF, TXT';
            color: rgba(255, 255, 255, 0.8) !important; 
            font-size: 13px;
            font-weight: 400; 
            text-align: center;
        }

        .hero-container {
            text-align: center;
            margin-top: 50px;
            margin-bottom: 30px;
        }
        .hero-icon-box {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 68px;
            height: 68px;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #38bdf8;
            border-radius: 18px;
            margin-bottom: 20px;
            font-size: 30px;
            box-shadow: 0 0 25px rgba(56, 189, 248, 0.15);
        }
        .hero-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }
        .hero-subtitle {
            color: #94a3b8;
            font-size: 1.05rem;
        }

        .cards-grid {
            display: flex;
            gap: 20px;
            justify-content: center;
            max-width: 800px;
            margin: 35px auto;
        }
        .suggestion-card {
            background: linear-gradient(180deg, #111827 0%, #0d1321 100%);
            border: 1px solid #1f2937;
            border-radius: 16px;
            padding: 22px;
            flex: 1;
            text-align: left;
            transition: all 0.3s ease;
        }
        .suggestion-card:hover {
            border-color: #38bdf8;
            transform: translateY(-2px);
            box-shadow: 0 10px 25px -5px rgba(56, 189, 248, 0.1);
        }
        .card-icon {
            font-size: 1.5rem;
            margin-bottom: 12px;
            color: #38bdf8;
        }
        .card-title {
            font-size: 1rem;
            font-weight: 600;
            color: #f1f5f9;
            margin-bottom: 6px;
        }
        .card-desc {
            font-size: 0.85rem;
            color: #64748b;
            line-height: 1.5;
        }

        [data-testid="stChatInput"] {
            background-color: #111827 !important;
            border: 1px solid #1f2937 !important;
            border-radius: 14px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
            transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
        }
        
        [data-testid="stChatInput"]:hover,
        [data-testid="stChatInput"]:focus-within {
            border-color: #38bdf8 !important;
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.15), 0 4px 20px rgba(0, 0, 0, 0.3) !important;
        }

        [data-testid="stChatInput"] textarea:focus {
            outline: none !important;
            box-shadow: none !important;
        }

        .disclaimer-text {
            text-align: center;
            font-size: 0.75rem;
            color: #475569;
            margin-top: 25px;
        }
    </style>
""", unsafe_allow_html=True)

# 3. SDK ve Model Başlatma (Güvenli ve Kararlı CPU/Default Mod)
@st.cache_resource
def init_model():
    try:
        config = Configuration(app_name="local-rag-assistant")
        FoundryLocalManager.initialize(config)
    except Exception:
        pass
    manager = FoundryLocalManager.instance
    model = manager.catalog.get_model("phi-3.5-mini")
    model.download()
    model.load()
    return model

model = init_model()
chat_client = model.get_chat_client()

# 4. Veritabanı Kurulumu
def init_db():
    conn = sqlite3.connect("rag_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# 5. PDF ve TXT Okuma Fonksiyonları
def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        return text
    except Exception as e:
        st.error(f"PDF okunurken hata oluştu: {e}")
        return ""

def process_and_save_file(uploaded_file):
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    file_path = os.path.join(data_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    file_text = ""
    if uploaded_file.name.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            file_text = f.read()
    elif uploaded_file.name.endswith(".pdf"):
        doc = fitz.open(file_path)
        start_page = 2 if len(doc) > 3 else 0
        for page_num in range(start_page, len(doc)):
            file_text += doc[page_num].get_text() + "\n"
        
    if file_text:
        conn = sqlite3.connect("rag_database.db")
        cursor = conn.cursor()
        
        chunk_size = 1000
        overlap = 200
        chunks = []
        
        banned_titles = ["doç.dr", "öğr.gör", "prof.dr", "dr.öğr", "yazar", "editör", "türkçe:", "prof."]
        
        for i in range(0, len(file_text), chunk_size - overlap):
            chunk = file_text[i:i + chunk_size].strip()
            chunk_clean = chunk.lower().replace(" ", "")
            
            # İçinde unvan geçen parçaları veritabanına asla kaydetme
            if len(chunk) > 50 and not any(title in chunk_clean for title in banned_titles):
                chunks.append(chunk)
                
        for chunk in chunks:
            cursor.execute("INSERT INTO documents (source_file, content) VALUES (?, ?)", (uploaded_file.name, chunk))
        conn.commit()
        conn.close()
        return len(chunks)
    return 0

# Arama Fonksiyonu
def search_database(query):
    conn = sqlite3.connect("rag_database.db")
    cursor = conn.cursor()
    
    stop_words = {"neden", "nasıl", "niçin", "için", "gibi", "genelde", "çalışır", "kullanmaz", "veya", "bunun", "olan", "her", "aynı", "anda", "farklı", "göre", "nokta", "daha", "önce", "ayıran", "karşı", "özelliği", "olarak", "anlama", "gelir", "nedir", "nedir?"}
    keywords = [kw.strip("?,.!'\"") for kw in query.split() if len(kw) > 2 and kw.lower() not in stop_words]
    
    cursor.execute("SELECT id, content FROM documents")
    all_rows = cursor.fetchall()
    
    scored_results = []
    banned_terms = ["prof.", "doç.", "öğr.", "dr.", "yazar", "editör", "türkçe:"]
    
    for row_id, content in all_rows:
        content_lower = content.lower()
        if any(term in content_lower for term in banned_terms):
            continue
            
        score = 0
        for kw in keywords:
            if kw.lower() in content_lower:
                score += 1
                
        if score > 0:
            scored_results.append((score, content))
            
    scored_results.sort(key=lambda x: x[0], reverse=True)
    conn.close()
    
    unique_results = []
    for score, content in scored_results:
        if content not in unique_results:
            unique_results.append(content)
            
    return unique_results[0] if unique_results else ""

# 6. Sidebar
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 14px; padding: 15px 0 25px 0;">
            <div style="background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%); width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                    <path d="M2 17l10 5 10-5"></path>
                    <path d="M2 12l10 5 10-5"></path>
                </svg>
            </div>
            <span style="font-size: 1.8rem; font-weight: 800; background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.5px; padding-bottom: 2px;">DocFlow</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    uploaded_files = st.file_uploader("", accept_multiple_files=True, type=["txt", "pdf"])
    
    if uploaded_files:
        for f in uploaded_files:
            st.markdown(f"""
                <div style="background: #1e293b; border: 1px solid #334155; padding: 10px 14px; border-radius: 10px; margin-bottom: 10px;">
                    <div style="font-size: 0.85rem; font-weight: 600; color: #e2e8f0;">📄 {f.name[:20]}...</div>
                    <div style="font-size: 0.75rem; color: #38bdf8; margin-top: 4px;">SENKRONİZE EDİLDİ • HAZIR</div>
                </div>
            """, unsafe_allow_html=True)

        if st.button("Kaynak Yükle", use_container_width=True):
            with st.spinner("Dosyalar taranıyor ve veritabanına işleniyor..."):
                total_added = 0
                # Yeni veride eski unvanlar kalmasın diye önce db dosyasını sıfırlayalım
                if os.path.exists("rag_database.db"):
                    os.remove("rag_database.db")
                init_db()
                
                for file in uploaded_files:
                    count = process_and_save_file(file)
                    total_added += count
                st.success(f"Başarıyla işlendi! Toplam {total_added} parça eklendi.")

# 7. Ana Ekran
if "messages" not in st.session_state:
    st.session_state.messages = []

if len(st.session_state.messages) == 0:
    st.markdown("""
        <div class="hero-container">
            <div class="hero-icon-box">🤖</div>
            <div class="hero-title">Bugün size nasıl yardımcı olabilirim?</div>
            <div class="hero-subtitle">Sayfalarca belge okumak yerine, sadece aradığınızı sorun.</div>
        </div>
        
        <div class="cards-grid">
            <div class="suggestion-card">
                <div class="card-icon">📄</div>
                <div class="card-title">Belgeleri özetle</div>
                <div class="card-desc">Girisimcilik.pdf dosyasından önemli noktaları çıkar</div>
            </div>
            <div class="suggestion-card">
                <div class="card-icon">⇄</div>
                <div class="card-title">Kaynakları karşılaştır</div>
                <div class="card-desc">Araştırma taslakları arasındaki farkları analiz et</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# 8. Sohbet Geçmişi
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 9. Kullanıcı Mesaj Girişi
if user_query := st.chat_input("Yerel verileriniz hakkında bir şeyler sorun..."):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Bilgiler taranıyor ve yanıt hazırlanıyor..."):
            context_data = search_database(user_query)
            
            if not context_data:
                response_text = "Yüklediğiniz belgelerde bu soruyla ilgili bir bilgi bulamadım."
            else:
                messages_payload = [
                    {
                        "role": "system",
                        "content": (
                            "Sen yalnızca sana verilen 'Bilgi Bağlamı' içindeki metne sadık kalan akademik bir asistansın. "
                            "Kural 1: Asla 'Prof.', 'Doç.', 'Türkçe:' gibi unvanlar veya etiketler kullanma. "
                            "Kural 2: Kendi kendine sohbet etme, rol yapma, soruya doğrudan net ve açıklayıcı bir cümleyle yanıt ver."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Bilgi Bağlamı:\n{context_data}\n\nSoru: {user_query}"
                    }
                ]
                
                response = chat_client.complete_chat(messages_payload)
                response_text = response.choices[0].message.content.strip()

            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})

# 10. En Alttaki Yasal Uyarı
st.markdown("""
    <div class="disclaimer-text">
        AI tarafından oluşturulan içerik hatalı olabilir. Yerel yürütme doğrulandı.
    </div>
""", unsafe_allow_html=True)