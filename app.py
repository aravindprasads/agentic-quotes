import html
import os
import random
import time

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from google import genai
from pinecone import Pinecone

load_dotenv()

# --- PAGE CONFIG (keep this as the first Streamlit command) ---
st.set_page_config(
    page_title="Vibe & Verse",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# --- CLIENTS (created once, not on every rerun) ---
@st.cache_resource
def get_clients():
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    index = pc.Index("quotes")
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    return index, client


index, client = get_clients()

# --- STATE ---
st.session_state.setdefault("seen_quotes", [])
st.session_state.setdefault("mood_text", "")
st.session_state.setdefault("quote_result", None)
st.session_state.setdefault("scroll_to_result", False)

# --- CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Playfair+Display:ital,wght@1,700&display=swap');

    #MainMenu, footer, header { visibility: hidden; }

    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        font-family: 'Inter', sans-serif;
    }

    /* One layout for every screen: readable max width, centred on big monitors */
    [data-testid="stMainBlockContainer"], .block-container {
        padding: 1.5rem 1.5rem 3rem !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
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

    /* Text input (16px stops iOS Safari from zooming in on focus) */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 12px 16px !important;
        font-size: 16px !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6c63ff !important;
        box-shadow: 0 0 0 2px rgba(108,99,255,0.3) !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: rgba(255,255,255,0.3) !important;
    }

    /* Form container: no extra box, the page already has structure */
    [data-testid="stForm"] { border: none !important; padding: 0 !important; }

    /* Submit button */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #6c63ff, #4facfe) !important;
        color: white !important; border: none !important;
        border-radius: 12px !important; padding: 13px 32px !important;
        min-height: 48px !important;
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
        border-radius: 20px !important; padding: 6px 4px !important;
        font-size: 12px !important; color: rgba(255,255,255,0.65) !important;
        width: 100% !important; transition: all 0.2s ease !important;
        white-space: nowrap !important;
    }
    .stButton > button:hover {
        background: rgba(108,99,255,0.25) !important;
        border-color: #6c63ff !important; color: white !important;
    }

    /* Pills wrap into a grid instead of stacking one per row on phones.
       4 per row on desktop, 2 per row on small screens. */
    .st-key-pills [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important; gap: 0.5rem !important;
    }
    .st-key-pills [data-testid="stColumn"],
    .st-key-pills [data-testid="column"] {
        flex: 1 1 calc(25% - 0.5rem) !important;
        min-width: calc(25% - 0.5rem) !important;
        width: auto !important;
    }

    /* Loading spinner text stays readable on the dark background */
    .stSpinner, .stSpinner * { color: rgba(255,255,255,0.8) !important; }

    /* Quote card */
    .quote-card {
        background: rgba(255,255,255,0.06);
        border-radius: 20px; padding: 36px 32px;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        display: flex; flex-direction: column;
        justify-content: center; min-height: 420px;
        overflow-wrap: anywhere;
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
    .quote-attribution a { color: #8f88ff !important; text-decoration: none; }
    .quote-attribution a:hover { text-decoration: underline !important; }
    .divider { height: 1px; background: rgba(255,255,255,0.1); margin-bottom: 18px; }
    .insight-label {
        font-size: 11px; font-weight: 700; color: #8f88ff;
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
    .stat-number { font-size: 18px; font-weight: 700; color: #8f88ff; }
    .stat-label { font-size: 10px; color: rgba(255,255,255,0.4); margin-top: 2px; }

    /* Phones and small tablets. Streamlit already stacks the two columns at this
       width, so the form comes first and the quote card follows right below it. */
    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"], .block-container {
            padding: 0.75rem 0.75rem 2rem !important;
        }
        .app-title { font-size: 22px !important; }
        .st-key-pills [data-testid="stColumn"],
        .st-key-pills [data-testid="column"] {
            flex: 1 1 calc(50% - 0.5rem) !important;
            min-width: calc(50% - 0.5rem) !important;
        }
        .stButton > button { font-size: 14px !important; padding: 10px 6px !important; }
        .quote-card { min-height: unset !important; padding: 22px 18px !important; }
        .quote-text { font-size: 18px !important; }
        .quote-icon { font-size: 36px !important; margin-bottom: 12px !important; }
        .stats-row { display: none !important; }
    }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────
def esc(value) -> str:
    """Escape text before it goes into raw HTML (quotes, LLM output, metadata).
    '$' is escaped too so Markdown does not treat it as the start of a formula."""
    return html.escape(str(value or "")).replace("$", "&#36;")


def compact(markup: str) -> str:
    """Join HTML into one line so Markdown never mistakes indented lines for a code block."""
    return "".join(line.strip() for line in markup.splitlines())


def safe_url(url) -> str:
    url = str(url or "")
    return url if url.startswith(("http://", "https://")) else "#"


# ── Run the agent ──────────────────────────────────────────────────────
def run_agent(user_mood: str):
    emb_response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=user_mood,
    )
    query_vector = emb_response.embeddings[0].values

    search_results = index.query(
        vector=query_vector,
        top_k=10,
        include_metadata=True,
    )

    matches = list(search_results["matches"])
    random.shuffle(matches)

    chosen_match = next(
        (m for m in matches if m["id"] not in st.session_state.seen_quotes), None
    )
    if chosen_match is None:
        return {"exhausted": True}

    st.session_state.seen_quotes.append(chosen_match["id"])
    meta = chosen_match["metadata"]

    # The insight is a bonus: if the LLM is busy or rate-limited,
    # still show the quote instead of failing the whole request.
    insight = ""
    try:
        prompt = f"""
        The user's current vibe is: "{user_mood}"
        Here is a matching quote:
        "{meta['text']}" — {meta['author']}, {meta['source']}
        Write a powerful 2-sentence Deepstash-style insight explaining how
        this quote applies to their current mood. Be warm, direct and human.
        Only output the 2 sentences, nothing else.
        """
        agent_response = client.interactions.create(
            model="gemini-3.5-flash-lite",
            input=prompt,
        )
        insight = agent_response.output_text.strip()
    except Exception:
        insight = ""

    return {
        "text": meta["text"],
        "author": meta.get("author", ""),
        "source": meta.get("source", ""),
        "url": meta.get("url", "#"),
        "insight": insight,
    }


# ── Render: quote card ─────────────────────────────────────────────────
def render_empty_card():
    st.markdown(compact("""
        <div class="quote-card"><div class="empty-state">
            <div class="empty-icon">🎭</div>
            <div class="empty-title">Your verse will appear here</div>
            <div class="empty-sub">Tap a vibe or type your own,<br>then press Find My Verse.</div>
        </div></div>"""), unsafe_allow_html=True)


def render_quote_card(result):
    if not result:
        render_empty_card()
        return

    if result.get("exhausted"):
        st.markdown(compact("""
            <div class="quote-card"><div class="empty-state">
                <div class="empty-icon">🎉</div>
                <div class="empty-title">You've heard every verse for this vibe</div>
                <div class="empty-sub">Try a different vibe, or refresh the page to start over.</div>
            </div></div>"""), unsafe_allow_html=True)
        return

    insight_block = ""
    if result.get("insight"):
        insight_block = (
            '<div class="divider"></div>'
            '<div class="insight-label">💡 Your Insight</div>'
            f'<div class="insight-text">{esc(result["insight"])}</div>'
        )

    st.markdown(compact(f"""
        <div class="quote-card">
            <div class="quote-icon">"</div>
            <div class="quote-text">{esc(result['text'])}</div>
            <div class="quote-attribution">
                — {esc(result['author'])} &nbsp;·&nbsp;
                <a href="{esc(safe_url(result['url']))}" target="_blank" rel="noopener noreferrer">📚 {esc(result['source'])}</a>
            </div>
            {insight_block}
        </div>"""), unsafe_allow_html=True)


def scroll_to_card():
    """On phones the card sits below the form, so bring it into view after a new result."""
    components.html(
        f"""<script>/* {time.time()} */
        setTimeout(function () {{
            try {{
                var w = window.parent;
                if (w.innerWidth <= 768) {{
                    var el = w.document.querySelector('.quote-card');
                    if (el) el.scrollIntoView({{behavior: 'smooth', block: 'start'}});
                }}
            }} catch (e) {{}}
        }}, 300);
        </script>""",
        height=0,
    )


# ── Render: vibe pills + input form (rendered exactly once) ────────────
MOODS = [
    ("😟", "Anxious"), ("💪", "Motivated"), ("😔", "Sad"), ("🎯", "Focused"),
    ("😤", "Frustrated"), ("🌱", "Growing"), ("😌", "Peaceful"), ("🚀", "Ambitious"),
]


def pick_mood(mood: str):
    # Runs before the rerun, so the text box shows the chosen vibe
    st.session_state.mood_text = mood


def render_input_and_form() -> bool:
    st.markdown("""
        <div class="app-title">🎭 Vibe & Verse</div>
        <div class="app-subtitle">Find your quote. Feel your moment.</div>
        <div class="input-label">Try a vibe</div>
    """, unsafe_allow_html=True)

    try:
        pills_box = st.container(key="pills")  # needs a recent Streamlit
    except TypeError:
        pills_box = st.container()
    with pills_box:
        cols = st.columns(len(MOODS))
        for col, (emoji, mood) in zip(cols, MOODS):
            with col:
                st.button(
                    f"{emoji} {mood}",
                    key=f"pill_{mood}",
                    on_click=pick_mood,
                    args=(mood,),
                )

    st.markdown(
        '<div class="input-label" style="margin-top:16px;">What\'s your vibe?</div>',
        unsafe_allow_html=True,
    )

    with st.form("mood_form"):
        st.text_input(
            label="mood",
            label_visibility="collapsed",
            placeholder="e.g. stressed, need motivation, feeling lost...",
            key="mood_text",
        )
        submitted = st.form_submit_button("🎭  Find My Verse")

    return submitted


# ══════════════════════════════════════════════════
# SINGLE RESPONSIVE LAYOUT
#   Desktop: inputs on the left, quote on the right.
#   Phone:   Streamlit stacks the columns, inputs first, quote below.
# ══════════════════════════════════════════════════
quotes_seen = len(st.session_state.seen_quotes)

left_col, right_col = st.columns([1, 1.4], gap="large")

with left_col:
    submitted = render_input_and_form()
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
    if submitted:
        mood = st.session_state.mood_text.strip()
        if not mood:
            st.warning("Type how you feel or tap a vibe, then press Find My Verse.")
        else:
            with st.spinner("Matching your vibe to the perfect verse..."):
                try:
                    st.session_state.quote_result = run_agent(mood)
                    st.session_state.scroll_to_result = True
                except Exception:
                    st.error(
                        "The quote service didn't respond. "
                        "Wait a few seconds and press Find My Verse again."
                    )

    render_quote_card(st.session_state.quote_result)

    if st.session_state.scroll_to_result:
        st.session_state.scroll_to_result = False
        scroll_to_card()
