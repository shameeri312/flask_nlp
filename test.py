import google.generativeai as genai
from textblob import TextBlob
import os

# Configure Gemini API (requires GEMINI_API_KEY set in environment)
genai.configure(api_key="")

# Initialize Gemini model
model = genai.GenerativeModel(
    "gemini-2.0-flash-lite",
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ],
    generation_config={"temperature": 0.7, "max_output_tokens": 500},
)

print("🤖 Gemini Chatbot (type 'exit' to quit)\n")

while True:
    user_input = input("You: ").strip()
    if user_input.lower() == "exit":
        print("Goodbye! 👋")
        break

    try:
        # Get AI response
        response = model.generate_content(user_input)
        bot_reply = response.text.strip()

        # Analyze sentiment

        print(f"\nBot: {bot_reply}")
        print()

    except Exception as e:
        print(f"❌ Error: {e}\n")
