import os
import random
import streamlit as st
from pinecone import Pinecone
from google import genai
from dotenv import load_dotenv

load_dotenv()
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index = pc.Index('quotes')
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# --- STATE ---
if 'seen_quotes' not in st.session_state:
    st.session_state.seen_quotes = []
if 'mood_input' not in st.session_state:
    st.session_state.mood_input = ''
if 'quote_result' not in st.session_state:
    st.session_state.quote_result = None

# --- PAGE CONFIG ---
st.set_page_config(page_title="Vibe & Verse", page_icon="🎭", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Playfair+Display:ital,wght@1,700&display=swap');

    #MainMenu, footer, header { visibility: hidden; }

    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        font-family: 'Inter', sans-serif;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }

    .app-title {
        font-size: 28px; font-weight: 700;
        color: #ffffff; margin-bottom: 2px;
    }
    .app-subtitle {
        font-size: 13px; color: rgba(255,255,255,0.5);
        margin-bottom: 20px;
    }
    .input-label {
        font-size: 12px; font-weight: 600;
        color: rgba(255,255,255,0.6);
        text-transform: uppercase; letter-spacing: 1px;
        margin-bottom: 6px; margin-top: 4px;
    }

    /* Text input */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6c63ff !important;
        box-shadow: 0 0 0 2px rgba(108,99,255,0.3) !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: rgba(255,255,255,0.3) !important;
    }

    /* Submit button */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #6c63ff, #4facfe) !important;
        color: white !important; border: none !important;
        border-radius: 12px !important; padding: 13px 32px !important;
        font-size: 15px !important; font-weight: 600 !important;
        width: 100% !important; margin-top: 8px !important;
        cursor: pointer !important; transition: all 0.3s ease !important;
    }
    .stFormSubmitButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(108,99,255,0.4) !important;
    }

    /* Pill buttons */
    .stButton > button {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 20px !important; padding: 4px 6px !important;
        font-size: 11px !important; color: rgba(255,255,255,0.65) !important;
        width: 100% !important; transition: all 0.2s ease !important;
        white-space: nowrap !important;
    }
    .stButton > button:hover {
        background: rgba(108,99,255,0.25) !important;
        border-color: #6c63ff !important; color: white !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.05) !important;
        border-radius: 12px !important;
        padding: 4px !important; gap: 4px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        color: rgba(255,255,255,0.5) !important;
        font-weight: 600 !important; font-size: 14px !important;
        padding: 8px 20px !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6c63ff, #4facfe) !important;
        color: white !important;
    }
    .stTabs [data-baseweb="tab-border"] { display: none !important; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 16px !important; }

    /* Quote card */
    .quote-card {
        background: rgba(255,255,255,0.06);
        border-radius: 20px; padding: 36px 32px;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        display: flex; flex-direction: column;
        justify-content: center; min-height: 420px;
    }
    .quote-icon {
        font-size: 48px; color: rgba(108,99,255,0.4);
        line-height: 1; margin-bottom: 18px;
        font-family: 'Playfair Display', serif;
    }
    .quote-text {
        font-family: 'Playfair Display', serif;
        font-size: 22px; font-style: italic;
        color: #ffffff; line-height: 1.6; margin-bottom: 18px;
    }
    .quote-attribution {
        font-size: 13px; color: rgba(255,255,255,0.5); margin-bottom: 24px;
    }
    .quote-attribution a { color: #6c63ff !important; text-decoration: none; }
    .quote-attribution a:hover { text-decoration: underline !important; }
    .divider { height: 1px; background: rgba(255,255,255,0.1); margin-bottom: 18px; }
    .insight-label {
        font-size: 11px; font-weight: 700; color: #6c63ff;
        text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px;
    }
    .insight-text {
        font-size: 14px; color: rgba(255,255,255,0.75); line-height: 1.7;
    }

    /* Empty state */
    .empty-state { text-align: center; padding: 40px 20px; }
    .empty-icon { font-size: 52px; margin-bottom: 12px; }
    .empty-title { font-size: 18px; font-weight: 600; color: rgba(255,255,255,0.8); margin-bottom: 6px; }
    .empty-sub { font-size: 13px; color: rgba(255,255,255,0.4); line-height: 1.6; }

    /* Stats */
    .stats-row { display: flex; gap: 10px; margin-top: 18px; }
    .stat-box {
        flex: 1; background: rgba(255,255,255,0.05);
        border-radius: 10px; padding: 10px; text-align: center;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .stat-number { font-size: 18px; font-weight: 700; color: #6c63ff; }
    .stat-label { font-size: 10px; color: rgba(255,255,255,0.4); margin-top: 2px; }

    /* Desktop: show columns, hide tabs */
    @media (min-width: 769px) {
        .mobile-only { display: none !important; }
    }

    /* Mobile: hide columns, show tabs */
    @media (max-width: 768px) {
        .desktop-only { display: none !important; }
        .block-container {
            padding-top: 0.75rem !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }
        .app-title { font-size: 22px !important; }
        .quote-card { min-height: unset !important; padding: 22px 18px !important; }
        .quote-text { font-size: 18px !important; }
        .quote-icon { font-size: 36px !important; margin-bottom: 12px !important; }
        .stats-row { display: none !important; }
    }
</style>
""", unsafe_allow_html=True)


# ── Reusable: run the agent ────────────────────────────────────────────
def run_agent(user_mood):
    emb_response = client.models.embed_content(
        model='gemini-embedding-001',
        contents=user_mood
    )
    query_vector = emb_response.embeddings[0].values

    search_results = index.query(
        vector=query_vector,
        top_k=10,
        include_metadata=True
    )

    matches = search_results['matches']
    random.shuffle(matches)

    chosen_match = None
    for match in matches:
        if match['id'] not in st.session_state.seen_quotes:
            chosen_match = match
            break

    if chosen_match is None:
        return None

    st.session_state.seen_quotes.append(chosen_match['id'])
    meta = chosen_match['metadata']

    prompt = f"""
    The user's current vibe is: "{user_mood}"
    Here is a matching quote:
    "{meta['text']}" — {meta['author']}, {meta['source']}
    Write a powerful 2-sentence Deepstash-style insight explaining how
    this quote applies to their current mood. Be warm, direct and human.
    Only output the 2 sentences, nothing else.
    """

    agent_response = client.interactions.create(
        model='gemini-3.5-flash-lite',
        input=prompt
    )

    return {
        "text": meta['text'],
        "author": meta['author'],
        "source": meta['source'],
        "url": meta.get('url', '#'),
        "insight": agent_response.output_text.strip()
    }


# ── Reusable: render quote card ────────────────────────────────────────
def render_quote_card(result):
    if result is None:
        st.markdown("""
            <div class="quote-card"><div class="empty-state">
                <div class="empty-icon">🎉</div>
                <div class="empty-title">You've heard every verse!</div>
                <div class="empty-sub">Refresh to reset,<br>or try a different vibe.</div>
            </div></div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="quote-card">
                <div class="quote-icon">"</div>
                <div class="quote-text">{result['text']}</div>
                <div class="quote-attribution">
                    — {result['author']} &nbsp;·&nbsp;
                    <a href="{result['url']}" target="_blank">📚 {result['source']}</a>
                </div>
                <div class="divider"></div>
                <div class="insight-label">💡 Your Insight</div>
                <div class="insight-text">{result['insight']}</div>
            </div>""", unsafe_allow_html=True)


def render_empty_card():
    st.markdown("""
        <div class="quote-card"><div class="empty-state">
            <div class="empty-icon">🎭</div>
            <div class="empty-title">Your verse will appear here</div>
            <div class="empty-sub">Click a vibe or type your own,<br>then hit Find My Verse.</div>
        </div></div>""", unsafe_allow_html=True)


# ── Reusable: render pill buttons + form ──────────────────────────────
# KEY FIX: suffix is passed into every button key so desktop
# and mobile buttons never share the same widget ID.
def render_input_and_form(suffix):
    st.markdown("""
        <div class="app-title">🎭 Vibe & Verse</div>
        <div class="app-subtitle">Find your quote. Feel your moment.</div>
        <div class="input-label">Try a vibe</div>
    """, unsafe_allow_html=True)

    moods = [
        ("😟", "Anxious"), ("💪", "Motivated"),
        ("😔", "Sad"),     ("🎯", "Focused"),
        ("😤", "Frustrated"), ("🌱", "Growing"),
        ("😌", "Peaceful"), ("🚀", "Ambitious"),
    ]

    pill_cols = st.columns(4)
    for i, (emoji, mood) in enumerate(moods):
        with pill_cols[i % 4]:
            # ✅ Unique key per layout using suffix
            if st.button(f"{emoji} {mood}", key=f"pill_{mood}_{suffix}"):
                st.session_state.mood_input = mood

    st.markdown('<div class="input-label" style="margin-top:16px;">What\'s your vibe?</div>',
                unsafe_allow_html=True)

    with st.form(f"mood_form_{suffix}"):
        user_mood = st.text_input(
            label="mood", label_visibility="collapsed",
            placeholder="e.g. stressed, need motivation, feeling lost...",
            value=st.session_state.mood_input
        )
        submitted = st.form_submit_button("🎭  Find My Verse")

    return user_mood, submitted


quotes_seen = len(st.session_state.seen_quotes)

# ══════════════════════════════════════════════════
# DESKTOP LAYOUT
# ══════════════════════════════════════════════════
st.markdown('<div class="desktop-only">', unsafe_allow_html=True)

left_col, right_col = st.columns([1, 1.4], gap="large")

with left_col:
    user_mood_d, submitted_d = render_input_and_form("desktop")
    st.markdown(f"""
        <div class="stats-row">
            <div class="stat-box">
                <div class="stat-number">{quotes_seen}</div>
                <div class="stat-label">Verses Seen</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">300+</div>
                <div class="stat-label">In Library</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">AI</div>
                <div class="stat-label">Powered</div>
            </div>
        </div>""", unsafe_allow_html=True)

with right_col:
    if submitted_d and user_mood_d:
        with st.spinner("Matching your vibe to the perfect verse..."):
            st.session_state.quote_result = run_agent(user_mood_d)
        render_quote_card(st.session_state.quote_result)
    elif st.session_state.quote_result:
        render_quote_card(st.session_state.quote_result)
    else:
        render_empty_card()

st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# MOBILE LAYOUT (tabs)
# ══════════════════════════════════════════════════
st.markdown('<div class="mobile-only">', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🎭 Find My Verse", "💬 My Quote"])

with tab1:
    user_mood_m, submitted_m = render_input_and_form("mobile")
    if submitted_m and user_mood_m:
        with st.spinner("Finding your verse..."):
            st.session_state.quote_result = run_agent(user_mood_m)
        st.success("✅ Done! Tap 'My Quote' to see your verse →")

with tab2:
    if st.session_state.quote_result:
        render_quote_card(st.session_state.quote_result)
    else:
        render_empty_card()

st.markdown('</div>', unsafe_allow_html=True)
