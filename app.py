import os
import random
import streamlit as st
from pinecone import Pinecone
from google import genai
from dotenv import load_dotenv

# Load API keys
load_dotenv()
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index = pc.Index('quotes')
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# --- INITIALIZE MEMORY ---
if 'seen_quotes' not in st.session_state:
    st.session_state.seen_quotes = []

# --- UI DESIGN ---
st.set_page_config(page_title="Deepstash AI", page_icon="💡")
st.title("💡 AI Quote Curation")
st.write("Tell me how you're feeling, and I'll find the perfect quote and insight for you.")

# FIX 1: We put the input and button inside a "Form" to stop UI glitches
with st.form("mood_form"):
    user_mood = st.text_input("How are you feeling right now? (e.g., 'stressed about work', 'need motivation')")
    submitted = st.form_submit_button("Get Insight")

# --- AGENT LOGIC ---
if submitted:
    if user_mood:
        with st.spinner("Analyzing mood & searching knowledge base..."):
            
            # 1. Turn the user's mood into a math vector
            emb_response = client.models.embed_content(
                model='gemini-embedding-001',
                contents=user_mood
            )
            query_vector = emb_response.embeddings[0].values

            # 2. Search Pinecone for the top matches
            search_results = index.query(
                vector=query_vector,
                top_k=5, 
                include_metadata=True
            )
            
            # Extract matches and shuffle
            matches = search_results['matches']
            random.shuffle(matches)
            
            # 3. Filter out quotes the user has already seen
            chosen_match = None
            for match in matches:
                if match['id'] not in st.session_state.seen_quotes:
                    chosen_match = match
                    break 
            
            if chosen_match is None:
                st.warning("You've seen all the quotes we have for this mood! Close the tab to reset your history, or wait for the database to finish updating.")
            else:
                st.session_state.seen_quotes.append(chosen_match['id'])

                url = chosen_match['metadata'].get('url', '#')
                context = f"- \"{chosen_match['metadata']['text']}\" (Author: {chosen_match['metadata']['author']}, Source: {chosen_match['metadata']['source']}, URL: {url})"

                # 4. Agentic Synthesis
                prompt = f"""
                The user is feeling: "{user_mood}"
                
                Here is a quote from our database that fits their mood:
                {context}
                
                Write a short, 2-sentence 'Deepstash-style' insight explaining how this quote applies to their current mood to help them out.
                
                Format your response exactly like this:
                **"The Quote"** 
                — *Author Name, [Source Name](URL)*
                
                💡 **Insight:** Your 2-sentence advice/insight here.
                """

                # FIX 2: We changed the model to 'flash-lite' for maximum speed
                agent_response = client.interactions.create(
                    model='gemini-3.5-flash-lite', 
                    input=prompt
                )

                # --- DISPLAY RESULT ---
                st.success("Found a fresh insight just for you!")
                st.info(agent_response.output_text)
                
    else:
        st.warning("Please enter a mood first!")
