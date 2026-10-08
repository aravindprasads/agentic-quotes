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

# --- MEMORY & STATE ---
if 'seen_quotes' not in st.session_state:
    st.session_state.seen_quotes = []
if 'mood_input' not in st.session_state:
    st.session_state.mood_input = ''

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Vibe & Verse",
    page_icon="🎭",
    layout="wide"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Playfair+Display:ital,wght@1,700&display=swap');

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        font-family: 'Inter', sans-serif;
    }

    .app-title {
        font-family: 'Inter', sans-serif;
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 4px;
    }

    .app-subtitle {
        font-size: 14px;
        color: rgba(255,255,255,0.5);
        margin-bottom: 28px;
    }

    .input-label {
        font-size: 13px;
        font-weight: 600;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }

    /* Text input styling */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 14px 18px !important;
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

    /* Submit button (inside form) */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #6c63ff, #4facfe) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 14px 32px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        width: 100% !important;
        margin-top: 8px !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
    }

    .stFormSubmitButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(108,99,255,0.4) !important;
    }

    /* Pill buttons (outside form) — styled to look like tags */
    .stButton > button {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 20px !important;
        padding: 4px 10px !important;
        font-size: 12px !important;
        color: rgba(255,255,255,0.65) !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
    }

    .stButton > button:hover {
        background: rgba(108,99,255,0.25) !important;
        border-color: #6c63ff !important;
        color: white !important;
        transform: translateY(-1px) !important;
    }

    /* Quote card */
    .quote-card {
        background: rgba(255, 255, 255, 0.06);
        border-radius: 24px;
        padding: 48px 40px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 500px;
    }

    .quote-icon {
        font-size: 60px;
        color: rgba(108,99,255,0.4);
        line-height: 1;
        margin-bottom: 24px;
        font-family: 'Playfair Display', serif;
    }

    .quote-text {
        font-family: 'Playfair Display', serif;
        font-size: 26px;
        font-style: italic;
        color: #ffffff;
        line-height: 1.6;
        margin-bottom: 24px;
    }

    .quote-attribution {
        font-size: 14px;
        color: rgba(255,255,255,0.5);
        margin-bottom: 32px;
    }

    .quote-attribution a {
        color: #6c63ff !important;
        text-decoration: none;
    }

    .divider {
        height: 1px;
        background: rgba(255,255,255,0.1);
        margin-bottom: 24px;
    }

    .insight-label {
        font-size: 11px;
        font-weight: 700;
        color: #6c63ff;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 12px;
    }

    .insight-text {
        font-size: 15px;
        color: rgba(255,255,255,0.75);
        line-height: 1.7;
    }

    .empty-state {
        text-align: center;
        padding: 60px 20px;
    }

    .empty-icon { font-size: 64px; margin-bottom: 16px; }
    .empty-title { font-size: 20px; font-weight: 600; color: rgba(255,255,255,0.8); margin-bottom: 8px; }
    .empty-sub { font-size: 14px; color: rgba(255,255,255,0.4); }

    .stats-row {
        display: flex;
        gap: 12px;
        margin-top: 24px;
    }

    .stat-box {
        flex: 1;
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.08);
    }

    .stat-number { font-size: 20px; font-weight: 700; color: #6c63ff; }
    .stat-label { font-size: 11px; color: rgba(255,255,255,0.4); margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

# --- LAYOUT ---
left_col, right_col = st.columns([1, 1.4], gap="large")

# =====================
# LEFT PANEL
# =====================
with left_col:
    st.markdown("""
        <div class="app-title">🎭 Vibe & Verse</div>
        <div class="app-subtitle">Find your quote. Feel your moment.</div>
    """, unsafe_allow_html=True)

    # --- CLICKABLE MOOD PILLS ---
    st.markdown('<div class="input-label">Try a vibe</div>', unsafe_allow_html=True)

    moods = [
        ("😟", "Anxious"),
        ("💪", "Motivated"),
        ("😔", "Sad"),
        ("🎯", "Focused"),
        ("😤", "Frustrated"),
        ("🌱", "Growing"),
        ("😌", "Peaceful"),
        ("🚀", "Ambitious"),
    ]

    # Render pills as real buttons in a 4-column grid
    pill_cols = st.columns(4)
    for i, (emoji, mood) in enumerate(moods):
        with pill_cols[i % 4]:
            if st.button(f"{emoji} {mood}", key=f"pill_{mood}"):
                # When clicked, auto-fill the text input via session state
                st.session_state.mood_input = mood

    st.markdown('<div class="input-label" style="margin-top:20px;">What\'s your vibe?</div>', unsafe_allow_html=True)

    # --- FORM WITH PRE-FILLED INPUT ---
    with st.form("mood_form"):
        user_mood = st.text_input(
            label="mood",
            label_visibility="collapsed",
            placeholder="e.g. stressed, need motivation, feeling lost...",
            value=st.session_state.mood_input  # ← This is the magic line!
        )
        submitted = st.form_submit_button("🎭  Find My Verse")

    # Stats
    quotes_seen = len(st.session_state.seen_quotes)
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
        </div>
    """, unsafe_allow_html=True)

# =====================
# RIGHT PANEL
# =====================
with right_col:
    if submitted and user_mood:
        with st.spinner("Matching your vibe to the perfect verse..."):

            # 1. Embed the mood
            emb_response = client.models.embed_content(
                model='gemini-embedding-001',
                contents=user_mood
            )
            query_vector = emb_response.embeddings[0].values

            # 2. Search Pinecone
            search_results = index.query(
                vector=query_vector,
                top_k=10,
                include_metadata=True
            )

            matches = search_results['matches']
            random.shuffle(matches)

            # 3. Filter seen quotes
            chosen_match = None
            for match in matches:
                if match['id'] not in st.session_state.seen_quotes:
                    chosen_match = match
                    break

            if chosen_match is None:
                st.markdown("""
                    <div class="quote-card">
                        <div class="empty-state">
                            <div class="empty-icon">🎉</div>
                            <div class="empty-title">You've heard every verse!</div>
                            <div class="empty-sub">Refresh the page to reset,<br>or try a completely different vibe.</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.session_state.seen_quotes.append(chosen_match['id'])
                meta = chosen_match['metadata']
                url = meta.get('url', '#')

                # 4. Agent Synthesis
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

                insight = agent_response.output_text.strip()

                st.markdown(f"""
                    <div class="quote-card">
                        <div class="quote-icon">"</div>
                        <div class="quote-text">{meta['text']}</div>
                        <div class="quote-attribution">
                            — {meta['author']} &nbsp;·&nbsp; <a href="{url}" target="_blank">📚 {meta['source']}</a>
                        </div>
                        <div class="divider"></div>
                        <div class="insight-label">💡 Your Insight</div>
                        <div class="insight-text">{insight}</div>
                    </div>
                """, unsafe_allow_html=True)

    else:
        st.markdown("""
            <div class="quote-card">
                <div class="empty-state">
                    <div class="empty-icon">🎭</div>
                    <div class="empty-title">Your verse will appear here</div>
                    <div class="empty-sub">Click a vibe above or type your own,<br>then hit Find My Verse.</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
