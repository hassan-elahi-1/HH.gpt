import os
import re
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
import streamlit as st
from PIL import Image

# --- Load environment variables ---
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    st.error("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")
    st.stop()

# --- Gemini OpenAI-compatible setup ---
external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# --- Custom CSS for styling ---
st.markdown("""
    <style>
    .welcome-title {
        font-size: 2.2rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .hh-text {
        color: #1f8e3f;
    }
    .welcome-text {
        color: #FFFFFF;
    }
    .chat-container {
        border: 1px solid #ddd;
        border-radius: 15px;
        padding: 1rem;
        background-color: #f9f9f9;
        margin-bottom: 1rem;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- Language detection helper ---
def detect_language(text):
    """Detect if input is Urdu script, English, or Roman Urdu."""
    urdu_chars = re.findall(r'[\u0600-\u06FF]', text)
    english_chars = re.findall(r'[A-Za-z]', text)

    if urdu_chars and not english_chars:
        return "urdu"
    elif english_chars:
        # Check if looks like Roman Urdu words
        roman_urdu_words = ["kaise", "ap", "mein", "ho", "kya", "acha", "nahi", "haan", "theek"]
        if any(word in text.lower() for word in roman_urdu_words):
            return "roman_urdu"
        else:
            return "english"
    return "english"

# --- Helper Functions ---
def login():
    username = st.session_state.login_username
    password = st.session_state.login_password
    if username and password:
        st.session_state.logged_in = True
        st.session_state.show_login = False
        st.session_state.username = username
    else:
        st.error("Invalid credentials. Please try again.")

def get_gemini_reply(prompt):
    """
    Generate reply based on detected language.
    """
    lang = detect_language(prompt)

    if lang == "urdu":
        system_prompt = (
            "آپ ایک ذہین اور دوستانہ چیٹ بوٹ ہیں۔ "
            "ہمیشہ اردو میں جواب دیں۔ انگریزی یا دیگر زبانوں کا استعمال نہ کریں۔"
        )
    elif lang == "roman_urdu":
        system_prompt = (
            "You are a friendly assistant. "
            "User is speaking Roman Urdu (Urdu written in English letters). "
            "Reply in Roman Urdu naturally, like a human conversation."
        )
    else:
        system_prompt = (
            "You are a professional and kind English-speaking assistant. "
            "Always reply in English."
        )

    async def fetch():
        response = await external_client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    return asyncio.run(fetch())

# --- Initialize session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "show_login" not in st.session_state:
    st.session_state.show_login = True
if "username" not in st.session_state:
    st.session_state.username = ""

# --- Welcome / Login ---
if st.session_state.logged_in:
    st.markdown(
        f"<h1 class='welcome-title'><span class='hh-text'>HH.gpt</span> <span class='welcome-text'>Welcome {st.session_state.username}!</span></h1>",
        unsafe_allow_html=True
    )

if st.session_state.show_login:
    with st.form("login_form"):
        st.header("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        login_button = st.form_submit_button("Login")
    if login_button:
        login()

# --- Chat Section ---
elif st.session_state.logged_in:
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    st.markdown("</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Thinking..."):
            reply = get_gemini_reply(prompt)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)
