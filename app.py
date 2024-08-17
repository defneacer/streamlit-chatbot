import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import pyodbc
from dataclasses import dataclass
from typing import Literal
import streamlit.components.v1 as components
import os
import base64

# Mesaj sınıfı
@dataclass
class Message:
    """Class for keeping track of a chat message."""
    origin: Literal["human", "ai"]
    message: str

# CSS yükleme fonksiyonu
def load_css():
    with open("static/styles.css", "r") as f:
        css = f"<style>{f.read()}</style>"
        st.markdown(css, unsafe_allow_html=True)

# Resimleri Base64'e çevirme fonksiyonu
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Veritabanı bağlantısı
def connect_to_database():
    connection = pyodbc.connect(
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=localhost\SQLEXPRESS;'  # Sunucu adı
        r'DATABASE=Chatbot;'  # Veritabanı adı
        r'UID=defne2;'  # SQL Server kullanıcı adı
        r'PWD=Ac12345;'  # SQL Server şifresi
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

# Türkçe model yükleme
tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-base-turkish-cased")
model = AutoModelForCausalLM.from_pretrained("dbmdz/bert-base-turkish-cased")
turkish_generator = pipeline('text-generation', model=model, tokenizer=tokenizer)

# Session state başlangıç durumu
def initialize_session_state():
    if "history" not in st.session_state:
        st.session_state.history = []
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
    if "human_prompt" not in st.session_state:
        st.session_state.human_prompt = ""

# Mesaj gönderme callback fonksiyonu
def on_click_callback():
    user_input = st.session_state.human_prompt.strip()  # Girilen metni kontrol et
    if user_input:  # Boş değilse devam et
        st.session_state.history.append(Message("human", user_input))

        # Önce veritabanında arama yap
        retrieved_info = fetch_information(user_input)
        if retrieved_info:
            response = retrieved_info  # Veritabanı yanıtı
        else:
            response = turkish_generator(user_input, max_length=50)[0]["generated_text"]  # Model yanıtı

        st.session_state.history.append(Message("ai", response))
        st.session_state.human_prompt = ""  # Giriş temizleme

# Sohbet geçmişini temizleme fonksiyonu
def clear_conversation():
    st.session_state.history = []  # Sohbet geçmişini temizler

# Arayüz oluşturma fonksiyonu
def main():
    load_css()
    initialize_session_state()

    st.title("Emsbay Handel - Chatbot 🤖")

    chat_placeholder = st.container()
    prompt_placeholder = st.form("chat-form")

    # Base64 olarak resimleri yükleyin
    ai_icon_base64 = get_base64_image("static/ai_icon.png")
    user_icon_base64 = get_base64_image("static/user1.png")

    with chat_placeholder:
        for chat in st.session_state.history:
            icon_base64 = ai_icon_base64 if chat.origin == "ai" else user_icon_base64
            div = f"""
            <div class="chat-row 
                {'' if chat.origin == 'ai' else 'row-reverse'}">
                <img class="chat-icon" src="data:image/png;base64,{icon_base64}"
                     width=32 height=32>
                <div class="chat-bubble
                {'ai-bubble' if chat.origin == 'ai' else 'human-bubble'}">
                    &#8203;{chat.message}
                </div>
            </div>
            """
            st.markdown(div, unsafe_allow_html=True)

    with prompt_placeholder:
        cols = st.columns((6, 1))
        with cols[0]:
            st.text_input(
                "Chat",
                value="",
                label_visibility="collapsed",
                key="human_prompt",
            )
        with cols[1]:
            st.form_submit_button(
                "Submit", 
                type="primary", 
                on_click=on_click_callback, 
            )

    # Sohbet geçmişini temizleme fonksiyonu
    st.button("Sohbeti Temizle", on_click=clear_conversation)

    components.html("""
    <script>
    const streamlitDoc = window.parent.document;

    const buttons = Array.from(
        streamlitDoc.querySelectorAll('.stButton > button')
    );
    const submitButton = buttons.find(
        el => el.innerText === 'Submit'
    );

    streamlitDoc.addEventListener('keydown', function(e) {
        switch (e.key) {
            case 'Enter':
                submitButton.click();
                break;
        }
    });
    </script>
    """, 
    height=0,
    width=0,
    )

if __name__ == "__main__":
    main()
