from flask import Flask, request, jsonify
from textblob import TextBlob
import google.generativeai as genai

app = Flask(__name__)

# Configure Gemini API (replace with your API key)
API_KEY = "AIzaSyC-FKaJcE_LYP7MvugAWsRZ5cQkmXtwwmA"
genai.configure(api_key=API_KEY)

# Define the model with safety settings
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


@app.route("/analyze", methods=["POST"])
def analyze_chat():
    data = request.get_json()
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    prompt = f"""
    As a compassionate mental health chatbot, respond empathetically in 2-3 concise sentences based on the user's input: "{text}".

    **Contextual Awareness:** Pay attention to the user's recent messages and avoid repeating the exact same coping strategy or exercise suggestion if they have consistently expressed negative feelings or made similar requests.

    - **If this is the user's first message:** Respond with: 'Hello! How may I help you today?'
    - For subsequent input:
        - Infer the user's mood.
        - If the mood appears negative (e.g., contains words like 'sad', 'unhappy', 'down', 'discouraged', 'lost', 'hopeless'):
            - Offer a brief supportive message.
            - Suggest a simple coping strategy. **Vary the suggestion if the user has received the deep breathing suggestion recently.** Consider alternatives like:
                - 'Perhaps try focusing on your senses for a moment. What do you see, hear, or feel?'
                - 'Sometimes a short walk can help shift your perspective.'
                - 'Have you tried listening to calming music?'
            - If the user continues to express negative feelings after a suggestion, acknowledge their feelings and offer continued support without immediately repeating a coping strategy (e.g., 'I understand you're still feeling down. I'm here to listen.').
        - If the user expresses positive sentiment (e.g., contains 'yes', 'thanks', 'feeling better'):
            - Offer a brief positive and encouraging response (e.g., 'That's wonderful to hear!', 'Keep up the great work!').
        - If the user requests specific exercises (e.g., 'Suggest Deep Breathing exercises for me'):
            - Identify the type of exercise requested (e.g., 'Deep Breathing', 'Mindful Walking', 'Progressive Muscle Relaxation').
            - Suggest 1-2 specific exercises tailored to the requested type. For example:
                - For 'Deep Breathing': 'Try the 4-7-8 technique: inhale for 4 seconds, hold for 7, exhale for 8.'
                - For 'Mindful Walking': 'Take a 5-minute walk, focusing on the sensation of each step and your breathing.'
                - For 'Progressive Muscle Relaxation': 'Start by tensing and relaxing your toes for 5 seconds each, then move up to your calves.'
            - **Vary the exercise suggestions** if the user requests the same type of exercise multiple times (e.g., for a second 'Deep Breathing' request, suggest: 'Try diaphragmatic breathing: place a hand on your belly, inhale deeply to expand it, then exhale slowly.').
        - For neutral or unclear input, provide a general empathetic response.
    - Ensure your response is solely focused on user support, without any code, explanations, or internal reasoning.
    """

    try:
        response = model.generate_content(prompt)
        bot_response = response.text.strip()

        # Use TextBlob for sentiment analysis
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # Get the polarity score (-1.0 to 1.0)

        sentiment = "Neutral"
        suggestion = None

        # Determine sentiment based on polarity
        if polarity < 0:  # Negative sentiment
            sentiment = "Negative"
            suggestion = (
                "Try deep breathing: inhale for 4 seconds, hold for 4, exhale for 4."
            )
        elif polarity > 0:  # Positive sentiment
            sentiment = "Positive"
            suggestion = "That’s fantastic to hear! How about celebrating by doing something you love, like listening to your favorite music?"
        else:  # Neutral sentiment (polarity ≈ 0)
            sentiment = "Neutral"

        # Special case: Handle "yes" and YouTube-related responses
        lowered_text = text.lower()
        if "yes" in lowered_text and "youtube" in bot_response.lower():
            bot_response = "Search YouTube for guided meditations, nature soundscapes, or even calm music playlists. Finding something soothing can make a difference."
            suggestion = None

        return jsonify(
            {
                "sender": "You",
                "message": text,
                "receiver": "NLP Bot",
                "response": bot_response,
                "sentiment": sentiment,
                "suggestion": suggestion,
                "video": (
                    "https://www.youtube.com/watch?v=5qap5aO4i9A"
                    if sentiment == "Negative"
                    else None
                ),
            }
        )

    except Exception as e:
        print(e)
        return jsonify({"error": f"AI error: {str(e)}"}), 500


if __name__ == "__main__":
    ip_address = "192.168.100.35"  # Replace with your machine's IP
    app.run(host=ip_address, port=5000, debug=True)
