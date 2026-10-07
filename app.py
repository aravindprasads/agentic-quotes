import os
import streamlit as st
from pinecone import Pinecone
from google import genai
from dotenv import load_dotenv

# Load API keys
load_dotenv()
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index = pc.Index('quotes')
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# --- UI DESIGN ---
st.set_page_config(page_title="Deepstash AI", page_icon="💡")
st.title("💡 AI Quote Curation")
st.write("Tell me how you're feeling, and I'll find the perfect quote and insight for you.")

# User Input
user_mood = st.text_input("How are you feeling right now? (e.g., 'stressed about work', 'need motivation')")

# --- AGENT LOGIC ---
if st.button("Get Insight"):
    if user_mood:
        with st.spinner("Analyzing mood & searching knowledge base..."):
            
            # 1. Turn the user's mood into a math vector
            emb_response = client.models.embed_content(
                model='gemini-embedding-001',
                contents=user_mood
            )
            query_vector = emb_response.embeddings[0].values

            # 2. Search Pinecone for the 2 most mathematically similar quotes
            search_results = index.query(
                vector=query_vector,
                top_k=2,
                include_metadata=True
            )
            
            # Format the retrieved quotes into a readable string for the Agent
            context = ""
            for match in search_results['matches']:
                context += f"- \"{match['metadata']['text']}\" (Author: {match['metadata']['author']})\n"

            # 3. Agentic Synthesis: Ask Gemini to act as a curator
            prompt = f"""
            The user is feeling: "{user_mood}"
            
            Here are some relevant quotes from our database:
            {context}
            
            Pick the BEST quote from the list above. Then, write a short, 2-sentence 'Deepstash-style' insight explaining how this quote applies to their current mood to help them out.
            
            Format your response exactly like this:
            **"The Quote"** - Author Name
            
            💡 **Insight:** Your 2-sentence advice/insight here.
            """

            # Call Gemini to format the final UI card
            agent_response = client.interactions.create(
                model='gemini-3.8-flash', 
                input=prompt
            )

            # --- DISPLAY RESULT ---
            st.success("Found the perfect insight!")
            st.info(agent_response.output_text)
    else:
        st.warning("Please enter a mood first!")
