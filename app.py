from flask import Flask, request, jsonify
from textblob import TextBlob
import os

app = Flask(__name__)

# Define greeting keywords
greetings = ["hi", "hello", "hey", "hola", "greetings"]


@app.route("/analyze", methods=["POST"])
def analyze_sentiment():
    data = request.get_json()
    text = data.get("text", "").lower().strip()  # Normalize text
    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Check for greetings
    if any(greeting in text for greeting in greetings):
        return jsonify(
            {
                "response": "How may I help you today?",
                "sentiment": "Neutral",
                "suggestion": None,
            }
        )

    # Perform sentiment analysis
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    sentiment = (
        "Negative" if polarity < -0.1 else "Positive" if polarity > 0.1 else "Neutral"
    )

    # Dynamic response based on sentiment
    response = {
        "Positive": "That’s great to hear! Keep nurturing your positivity. Would you like a fun activity?",
        "Neutral": "You’re feeling neutral today. I’m here to help if you need a boost. Any thoughts?",
        "Negative": "I’m sorry you’re feeling this way. You’re not alone—would you like a relaxation tip?",
    }.get(sentiment, "I couldn’t analyze your mood properly. Please try again.")

    # Suggestions based on sentiment
    suggestion = {
        "Positive": "Try a gratitude journal or a short dance break!",
        "Neutral": "Consider a mindfulness exercise or a nature walk.",
        "Negative": "Try deep breathing: inhale for 4 seconds, hold for 4, exhale for 4. Or call 1-800-273-8255 (US).",
    }.get(sentiment, "Ensure the server is running.")

    return jsonify(
        {
            "response": response,
            "sentiment": sentiment,
            "suggestion": suggestion,
            "resource": "Negative" if sentiment == "Negative" else None,
        }
    )


if __name__ == "__main__":
    # Get your machine's IP address (e.g., 192.168.x.x)
    # Use 'ifconfig' (Linux/Mac) or 'ipconfig' (Windows) to find it
    ip_address = "192.168.100.35"  # Replace with your machine's IP
    app.run(host=ip_address, port=5000, debug=True)
