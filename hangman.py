# hangman.py
import streamlit as st
import random
import openai
import firebase_admin
import time
from firebase_admin import credentials, firestore
from string import ascii_uppercase
from functools import lru_cache

# --- Initialize Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate(st.secrets["FIREBASE_CONFIG"])
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Initialize Session State ---
if 'game' not in st.session_state:
    st.session_state.update({
        'game': {
            'word': '',
            'guessed_letters': [],
            'attempts': 6,
            'score': 0,
            'game_over': False,
            'hint_used': False,
            'fun_fact': ''
        },
        'show_leaderboard': False
    })

# --- Step 5: AI Hints & Fun Facts ---
@st.cache_data(ttl=300)
def get_ai_content(prompt, max_retries=3):
    for _ in range(max_retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                api_key=st.secrets["OPENAI_KEY"]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"AI service error: {str(e)}")
            time.sleep(2)
    return "Temporary hint unavailable. Try guessing letters!"

def get_ai_hint():
    prompt = f"Give a subtle hint about {st.session_state.game['word']} without revealing it. Max 10 words."
    return get_ai_content(prompt)

def get_fun_fact():
    prompt = f"Tell an interesting fact about {st.session_state.game['word']} in 15 words or less."
    return get_ai_content(prompt)

# --- Step 6: Leaderboard System ---
@st.cache_data(ttl=60)
def get_leaderboard(limit=10):
    try:
        scores_ref = db.collection("scores").order_by("score", direction=firestore.Query.DESCENDING).limit(limit)
        return [doc.to_dict() for doc in scores_ref.stream()]
    except Exception as e:
        st.error(f"Leaderboard error: {str(e)}")
        return []

def save_score(name, score):
    try:
        doc_ref = db.collection("scores").document()
        doc_ref.set({
            "name": name[:15],
            "score": score,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Failed to save score: {str(e)}")

# --- Enhanced Game Logic ---
def new_game(category, difficulty):
    word = get_ai_word(category, difficulty)  # Your existing word selection function
    st.session_state.game = {
        'word': word,
        'guessed_letters': [],
        'attempts': 6,
        'score': 0,
        'game_over': False,
        'hint_used': False,
        'fun_fact': get_fun_fact()
    }

def check_guess(letter):
    game = st.session_state.game
    if letter not in game['guessed_letters']:
        game['guessed_letters'].append(letter)
        if letter not in game['word']:
            game['attempts'] -= 1
    
    # Win/Lose conditions
    if game['attempts'] <= 0 or all(c in game['guessed_letters'] for c in game['word']):
        game['game_over'] = True
        if game['attempts'] > 0:
            game['score'] = game['attempts'] * 10 + (5 if not game['hint_used'] else 0)

# --- Enhanced UI Components ---
def show_game_over():
    game = st.session_state.game
    col1, col2 = st.columns(2)
    
    with col1:
        if game['attempts'] > 0:
            st.balloons()
            st.success(f"🎉 You Won! Score: {game['score']}")
            player_name = st.text_input("Enter your name for the leaderboard:", max_chars=15)
            if st.button("Submit Score") and player_name:
                save_score(player_name, game['score'])
        else:
            st.error(f"💀 Game Over! The word was: {game['word']}")
            st.write(f"Fun Fact: {game['fun_fact']}")
    
    with col2:
        st.subheader("🏆 Leaderboard")
        leaderboard = get_leaderboard()
        if leaderboard:
            for i, entry in enumerate(leaderboard, 1):
                st.write(f"{i}. {entry['name']} - {entry['score']}")
        else:
            st.write("No scores yet!")

# --- Add Hint Section to Main UI ---
def show_hint_section():
    if not st.session_state.game['game_over'] and not st.session_state.game['hint_used']:
        if st.button("💡 Get Hint (Costs 2 attempts)"):
            if st.session_state.game['attempts'] > 2:
                st.session_state.game['attempts'] -= 2
                st.session_state.game['hint_used'] = True
                st.info(f"Hint: {get_ai_hint()}")
            else:
                st.warning("Not enough attempts for a hint!")

# --- Main App Layout Updates ---
st.sidebar.header("Global Controls")
if st.sidebar.button("🏆 Show Leaderboard"):
    st.session_state.show_leaderboard = not st.session_state.show_leaderboard

if st.session_state.show_leaderboard:
    with st.expander("Global Leaderboard", expanded=True):
        leaderboard = get_leaderboard()
        if leaderboard:
            for i, entry in enumerate(leaderboard, 1):
                st.write(f"{i}. {entry['name']} - {entry['score']}")
        else:
            st.write("No scores yet!")
        st.button("Close Leaderboard", on_click=lambda: st.session_state.update({'show_leaderboard': False}))

# Add hint section to main game area
show_hint_section()

# Modify game over display
if st.session_state.game['game_over']:
    show_game_over()

# --- Step 7: Deployment Optimizations ---
# Add caching decorators to expensive functions
# Optimize Firebase queries with limit and ordering
# Add error boundaries and loading states

# Requirements.txt
"""
streamlit>=1.22
openai>=0.27
firebase-admin>=6.1
python-dotenv>=0.19
requests>=2.28
"""

# secrets.toml (for Streamlit sharing)
"""
[secrets]
OPENAI_KEY = "your_openai_key"
FIREBASE_CONFIG = "{...}"  # Paste your Firebase service account config
"""


# Replace old OpenAI imports with new structure
from openai import OpenAI

# Initialize client with your API key (update in your secrets)
client = OpenAI(api_key=st.secrets["OPENAI_KEY"])

# Update all ChatGPT completion calls from this:
# OLD VERSION (0.28)
# response = openai.ChatCompletion.create(
#     model="gpt-3.5-turbo",
#     messages=[...]
# )

# TO THIS NEW VERSION (1.0+)
@st.cache_data(ttl=300)
def get_ai_content(prompt, max_retries=3):
    for _ in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"AI service error: {str(e)}")
            time.sleep(2)
    return "Temporary hint unavailable. Try guessing letters!"

# Update your requirements.txt to specify:
openai>=1.0
