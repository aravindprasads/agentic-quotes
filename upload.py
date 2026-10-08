import os
from dotenv import load_dotenv
from pinecone import Pinecone
from google import genai

load_dotenv()

print("Connecting to Pinecone and Gemini...")
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Added the 'source' field to all quotes!
quotes = [
  {"id": "1", "author": "Carl Jung", "source": "Analytical Psychology Notes", "text": "I am not what happened to me, I am what I choose to become.", "category": "empowerment"},
  {"id": "2", "author": "Albus Dumbledore", "source": "Harry Potter and the Prisoner of Azkaban", "text": "Happiness can be found, even in the darkest of times, if one only remembers to turn on the light.", "category": "hope"},
  {"id": "3", "author": "Marcus Aurelius", "source": "Meditations", "text": "You have power over your mind - not outside events. Realize this, and you will find strength.", "category": "strength"},
  {"id": "4", "author": "Charles Bukowski", "source": "Factotum", "text": "Sometimes you climb out of bed in the morning and you think, I'm not going to make it, but you laugh inside — remembering all the times you've felt that way.", "category": "overcoming"},
  {"id": "5", "author": "Robert Frost", "source": "A Servant to Servants", "text": "The only way out is through.", "category": "resilience"}
]

index = pc.Index('quotes') 

print("Processing quotes...")
vectors_to_upload = []

for q in quotes:
    response = client.models.embed_content(
        model='gemini-embedding-001',
        contents=q["text"]
    )
    
    # We now pass the 'source' into the metadata so Pinecone remembers it
    vectors_to_upload.append({
        "id": q["id"],
        "values": response.embeddings[0].values,
        "metadata": {"text": q["text"], "author": q["author"], "source": q["source"], "category": q["category"]}
    })

print("Uploading to Pinecone...")
index.upsert(vectors=vectors_to_upload)
print("✅ Success! Quotes updated with sources.")
