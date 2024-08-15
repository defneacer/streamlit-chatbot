import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import pyodbc

# MSSQL veritabanı bağlantısı
def connect_to_database():
    connection = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=DEFNE\SQLEXPRESS;'  # Sunucu adınız
        'DATABASE=Chatbot;'  # Kullandığınız veritabanı adı
        'Trusted_Connection=yes;'  # Windows Authentication kullanımı
    )
    return connection

# Veritabanından bilgi çekme
def fetch_information(query):
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("SELECT TOP 1 column2 FROM [Chatbot].[dbo].[amazon_qa_pairs] WHERE column1 LIKE ? ORDER BY column1", ('%' + query + '%',))
    result = cursor.fetchone()
    connection.close()
    return result[0] if result else None

# Türkçe model yükleniyor
tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-base-turkish-cased")
model = AutoModelForCausalLM.from_pretrained("dbmdz/bert-base-turkish-cased")
turkish_generator = pipeline('text-generation', model=model, tokenizer=tokenizer)

# Mesaj gönderme işlemi
def send_message():
    user_input = st.session_state.input_text
    if user_input:
        # Kullanıcı sorusunu kaydet
        st.session_state.conversation.append({"role": "user", "text": user_input})

        # Önce veritabanında arama yap
        retrieved_info = fetch_information(user_input)
        if retrieved_info:
            response = retrieved_info  # Veritabanı yanıtı kullan
        else:
            response = generate_response(user_input)  # Veritabanında bulunamazsa model yanıtı kullan
        
        # Bot yanıtını kaydet
        st.session_state.conversation.append({"role": "bot", "text": response})

        # Kullanıcı girişini temizle
        st.session_state.input_text = ""  # Girişi temizleme

# Sohbet geçmişini temizleme işlemi
def clear_conversation():
    if st.button("Sohbeti Temizle"):
        st.session_state.show_confirmation = True

    if st.session_state.show_confirmation:
        st.warning("Bu işlem, mevcut sohbet geçmişini silecek. Devam etmek istediğinize emin misiniz?")
        if st.button("Evet, Temizle"):
            st.session_state.conversation = []
            st.session_state.show_confirmation = False
            st.success("Sohbet geçmişi temizlendi.")
        if st.button("Hayır, İptal"):
            st.session_state.show_confirmation = False

# Streamlit arayüzü
def main():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #1e1e1e;
            color: white;
        }
        .message-container {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            margin-bottom: 20px;
        }
        .message-box {
            padding: 10px;
            margin: 5px 0;
            border-radius: 10px;
            max-width: 70%;
        }
        .user-message {
            background-color: #4caf50;
            color: white;
            text-align: right;
        }
        .bot-message {
            background-color: #444444;
            color: white;
            text-align: left;
            align-self: flex-start;
        }
        .sender-label {
            background-color: #333333;
            color: white;
            padding: 5px 10px;
            border-radius: 10px;
            font-weight: bold;
            margin-bottom: -10px;
        }
        .user-label {
            align-self: flex-end;
        }
        .bot-label {
            align-self: flex-start;
        }
        .stButton > button {
            background-color: #4caf50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
        }
        .stButton > button:hover {
            background-color: #45a049;
        }
        </style>
        """, unsafe_allow_html=True
    )

    st.title("Emsbay Handel - Chatbot")

    # Sohbet geçmişi
    if "conversation" not in st.session_state:
        st.session_state.conversation = []

    # Onay penceresi gösterimi
    if "show_confirmation" not in st.session_state:
        st.session_state.show_confirmation = False

    # Sohbet geçmişini göster
    for message in st.session_state.conversation:
        if message["role"] == "user":
            st.markdown(f'<div class="message-container"><div class="sender-label user-label">Siz</div><div class="message-box user-message">{message["text"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="message-container"><div class="sender-label bot-label">Bot</div><div class="message-box bot-message">{message["text"]}</div></div>', unsafe_allow_html=True)

    # Kullanıcı girişi ve gizli buton
    user_input = st.text_input("Sorunuzu girin:", key="input_text", on_change=send_message)

    # Sohbet geçmişini temizle butonu ve onay penceresi
    clear_conversation()

if __name__ == "__main__":
    main()
