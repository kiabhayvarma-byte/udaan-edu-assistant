import os
import io
import re
import streamlit as st
from groq import Groq
from gtts import gTTS
from audio_recorder_streamlit import audio_recorder

st.set_page_config(
    page_title="Udaan - Ek Nayi Soch AI Mentor",
    page_icon="🚀",
    layout="wide"
)

# -------------------------------------------------------------------
# Groq API Configuration
# -------------------------------------------------------------------
GROQ_API_KEY = "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"

@st.cache_resource
def get_groq_client():
    return Groq(api_key=GROQ_API_KEY.strip())

client = get_groq_client()

# -------------------------------------------------------------------
# Auto-Detect Active Models (Zero 400/404 Errors)
# -------------------------------------------------------------------
@st.cache_data(ttl=1800)
def fetch_active_models():
    default_priority = [
        "llama-3.3-70b-versatile",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768"
    ]
    try:
        remote_models = client.models.list()
        live_ids = {m.id for m in remote_models.data if getattr(m, 'active', True)}
        valid_models = [m for m in default_priority if m in live_ids]
        if valid_models:
            return valid_models
        general_text = [
            m for m in live_ids
            if "whisper" not in m.lower() and "vision" not in m.lower()
        ]
        return general_text if general_text else default_priority
    except Exception:
        return default_priority

ACTIVE_MODELS = fetch_active_models()

SYSTEM_PROMPT = """
You are 'Udaan - Ek Nayi Soch AI Mentor', an expert, highly practical educational trainer.
You specialize in 6 core pedagogy pillars:
1. Digital & Traditional Learning
2. Teaching Learning Material (TLM)
3. Low-Cost Smart Class
4. Inclusive Education
5. Activity Based Learning (ABL)
6. Eco-Friendly School

Strict Guidelines:
- Give practical, direct, classroom-ready solutions.
- Never output markdown code blocks, JSON schemas, heavy bulleting, or asterisk symbols.
- Produce clean, spoken-word sentences so text-to-speech audio sounds fluid and clear.
"""

st.title("🚀 Udaan - Ek Nayi Soch")
active_engine = ACTIVE_MODELS[0] if ACTIVE_MODELS else "Auto-Select"
st.caption(f"Educational AI Mentor | Active Engine: `{active_engine}`")

col_lang, col_clear = st.columns([3, 1])
with col_lang:
    selected_lang = st.radio(
        "Bhasha Chuniye (Select Language):",
        ["Shuddh Hindi (शुद्ध हिन्दी)", "Bhojpuri (भोजपुरी)", "Indian English"],
        horizontal=True
    )
with col_clear:
    if st.button("🧹 Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("audio"):
            st.audio(msg["audio"], format="audio/mp3")

st.write("🎙️ **Bol kar poochhein:**")
audio_bytes = audio_recorder(
    text="Mic click karke bolein",
    recording_color="#e53935",
    neutral_color="#1e88e5",
    icon_name="microphone",
    icon_size="2x"
)

user_text = ""
if audio_bytes:
    with st.spinner("Aapki aawaz sun raha hoon..."):
        try:
            audio_buf = io.BytesIO(audio_bytes)
            audio_buf.name = "input.wav"
            transcription = client.audio.transcriptions.create(
                file=audio_buf,
                model="whisper-large-v3",
                response_format="text"
            )
            if transcription.strip():
                user_text = transcription.strip()
                st.info(f"🗣️ Aapne kaha: {user_text}")
        except Exception as e:
            st.error(f"Voice Recognition Error: {e}")

typed_text = st.chat_input("Apna sawaal yahan likhein ya mic use karein...")
if typed_text:
    user_text = typed_text.strip()

def auto_healing_inference(chat_history):
    errors_encountered = []
    for model_name in ACTIVE_MODELS:
        try:
            res = client.chat.completions.create(
                model=model_name,
                messages=chat_history,
                temperature=0.5,
                max_tokens=300
            )
            return res.choices[0].message.content
        except Exception as err:
            errors_encountered.append(f"{model_name}: {str(err)}")
            continue
    raise RuntimeError(f"All models failed: {'; '.join(errors_encountered)}")

def clean_for_natural_voice(text):
    text = re.sub(r'[*#_`~>]', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.write(user_text)

    if selected_lang == "Shuddh Hindi (शुद्ध हिन्दी)":
        lang_directive = (
            "उत्तर केवल शुद्ध, स्पष्ट, सरल और व्यावहारिक हिन्दी में दें। "
            "कक्षा में उपयोगी, सहज और प्रेरणादायक भाषा का प्रयोग करें।"
        )
    elif selected_lang == "Bhojpuri (भोजपुरी)":
        lang_directive = (
            "रउआ के केवल शुद्ध, स्वाभाविक अउर मीठ भोजपुरी (Devanagari) में उत्तर देवे के बा। "
            "नियम:\n"
            "- 'मैं' भा 'मीं' कबो मत लिखीं, हमेशा 'हम' लिखीं (जइसे: 'हम एकदम ठीक बानी')।\n"
            "- 'आप' खातिर 'रउआ' भा 'अपने' लिखीं।\n"
            "- 'है/हैं' खातिर 'बा' / 'बानी' / 'बाटे' लिखीं।\n"
            "- 'और' खातिर 'अउर' लिखीं, 'आर' मत लिखीं।\n"
            "- बनावटी भा गलत शब्द मत बनाईं, एकदम घरेलू अउर आदरभाव वाली बोली बोलीं।"
        )
    else:
        lang_directive = (
            "Respond strictly in clear, practical, natural Indian English tailored for educators."
        )

    full_payload = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n{lang_directive}"}
    ]
    for m in st.session_state.messages:
        full_payload.append({"role": m["role"], "content": m["content"]})

    with st.chat_message("assistant"):
        with st.spinner("Uttar taiyar ho raha hai..."):
            try:
                ai_reply = auto_healing_inference(full_payload)
                st.write(ai_reply)

                generated_audio = None
                try:
                    speech_ready_text = clean_for_natural_voice(ai_reply)
                    if selected_lang == "Indian English":
                        tts = gTTS(text=speech_ready_text, lang='en', tld='co.in', slow=False)
                    else:
                        tts = gTTS(text=speech_ready_text, lang='hi', slow=False)

                    voice_buffer = io.BytesIO()
                    tts.write_to_fp(voice_buffer)
                    voice_buffer.seek(0)
                    generated_audio = voice_buffer.read()
                    st.audio(generated_audio, format="audio/mp3", autoplay=True)
                except Exception:
                    pass

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": ai_reply,
                    "audio": generated_audio
                })
            except Exception as e:
                st.error(f"Auto-Healing Error: {e}")