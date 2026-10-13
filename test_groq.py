
import os
from dotenv import load_dotenv
from groq import Groq

# Load the key from your existing Tensor Bots backend config
load_dotenv("backend/.env")

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY not found. Check backend/.env"
    )

client = Groq(api_key=api_key)

try:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": "Reply with: Groq API is working!"
            }
        ],
        max_completion_tokens=100,
    )

    print("SUCCESS: Groq API is connected!")
    print(response.choices[0].message.content)

except Exception as e:
    print("Groq API request failed.")
    print(type(e).__name__, str(e))
