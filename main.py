import sqlite3
import os
from pypdf import PdfReader
from foundry_local_sdk import Configuration, FoundryLocalManager

def extract_text_from_pdf(pdf_path):
    """PDF dosyasının içindeki tüm metinleri güvenli bir şekilde okur"""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        print(f"Uyarı: {pdf_path} okunurken hata oluştu ({e}).")
        return ""

def setup_database_from_files():
    """data klasöründeki tüm txt ve pdf dosyalarını okur, veritabanına kaydeder"""
    conn = sqlite3.connect("rag_database.db")
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS documents")
    cursor.execute("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT,
            content TEXT
        )
    """)
    
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        return

    total_chunks = 0
    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)
        file_text = ""
        
        if filename.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                file_text = f.read()
                
        elif filename.endswith(".pdf"):
            print(f"-> PDF okunuyor: {filename}...")
            file_text = extract_text_from_pdf(file_path)
            
        if file_text:
            chunks = [chunk.strip() for chunk in file_text.split(".") if len(chunk.strip()) > 10]
            for chunk in chunks:
                cursor.execute("INSERT INTO documents (source_file, content) VALUES (?, ?)", (filename, chunk))
                total_chunks += 1
            print(f"-> {filename} başarıyla işlendi ({len(chunks)} parça eklendi).")
            
    conn.commit()
    conn.close()
    print(f"Toplam {total_chunks} adet belge parçası veritabanına senkronize edildi.\n")

def search_database(query_keyword):
    """SQLite veritabanından anahtar kelimeye göre bilgi arar"""
    conn = sqlite3.connect("rag_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM documents WHERE content LIKE ?", ('%' + query_keyword + '%',))
    results = cursor.fetchall()
    conn.close()
    
    context = "\n".join([row[0] for row in results])
    return context

def main():
    print("1. Veritabanı ve Dosyalar taranıyor...")
    setup_database_from_files()
    
    print("2. Sistem ve Model Hazırlanıyor...")
    config = Configuration(app_name="local-rag-assistant")
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance
    
    model = manager.catalog.get_model("qwen2.5-0.5b")
    model.load()
    chat_client = model.get_chat_client()
    
    user_query = "Fırat Üniversitesinde hangi konular işleniyor?"
    print(f"Kullanıcı Sorusu: {user_query}")
    
    context_data = search_database("Fırat")
    print(f"Veritabanından Bulunan Bilgi (Bağlam): {context_data}\n")
    
    # Few-shot (Örnekli) Prompt ile modele tam olarak nasıl cevap vermesi gerektiğini öğretiyoruz
    prompt = f"""Sadece aşağıdaki bilgiyi kullanarak soruya kısa ve net bir şekilde cevap ver. Asla ekleme yapma.

Bilgi: {context_data}
Soru: {user_query}
Cevap:"""

    response = chat_client.complete_chat([
        {"role": "user", "content": prompt}
    ])
    
    print("Asistanın Yanıtı:")
    print(response.choices[0].message.content)
    
    model.unload()

if __name__ == "__main__":
    main()