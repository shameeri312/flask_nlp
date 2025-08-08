from flask import Flask, request, jsonify
import google.generativeai as genai
import speech_recognition as sr
from pydub import AudioSegment
from textblob import TextBlob
import pyttsx3
import os

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

# Initialize SpeechRecognition
recognizer = sr.Recognizer()

# Initialize pyttsx3 for TTS
tts_engine = pyttsx3.init()


def text_to_speech(text):
    """Convert text to speech and play it through the console."""
    tts_engine.say(text)
    tts_engine.runAndWait()


def analyze_text(text):
    """Analyze text input and generate a response."""
    if not text:
        return {"error": "No text provided"}, 400

    prompt = f"""
    As a compassionate mental health chatbot, respond empathetically in 2-3 concise sentences based on the user's input: "{text}". Maintain conversational continuity by remembering the user's stated problems and emotional patterns.

    **Contextual Awareness Protocol**
    1. **Problem State Tracking**:
    - Maintain memory of:
        - Specific issues mentioned (e.g., "work stress", "relationship conflict")
        - Frequency of negative emotion mentions
        - Previous coping strategies suggested

    2. **Escalation Thresholds**:
    - Yellow Flag: 3+ consecutive negative messages
    - Red Flag: Mentions of self-harm, suicide, or severe hopelessness

    **Response Guidelines**
    - **First Message**: 'Hello! I'm here to listen. What would you like to share today?'
    
    - **Subsequent Messages**:
    1. **Problem-Specific Responses**:
        - Reference stated issues: "I recall you mentioned family tensions..."
        - Acknowledge emotional patterns: "This seems similar to yesterday's work stress"

    2. **Severity-Based Actions**:
        - *Yellow Flag State*:
        "I notice you've been feeling low consistently. While I'm here to listen, consider speaking with a counselor for deeper support."
        + Show local mental health centers (integrate Google Maps API)
        
        - *Red Flag State*:
        "Your safety matters. Please contact the [National Suicide Hotline] at 1-800-273-8255 or visit the nearest hospital emergency room immediately."

    3. **Negative Sentiment**:
        - Tiered Suggestions:
        - Mild: "When I feel overwhelmed by [user's stated issue], I find journaling helps organize thoughts."
        - Moderate: "For [specific problem], progressive muscle relaxation might help. Let me guide you through it."
        - Severe: Escalate per above protocols

    4. **Positive/Negative Transition Tracking**:
        - If improvement: "I'm glad the breathing exercises helped with your exam anxiety!"
        - If regression: "The sleep issues seem to be resurfacing. Should we explore new strategies?"

    **Prohibited Actions**
    ❌ Never diagnose conditions
    ❌ Avoid generic "It gets better" phrases
    ❌ No medical advice beyond basic coping
    """

    try:
        response = model.generate_content(prompt)
        bot_response = response.text.strip()

        # Use Text Blob for sentiment analysis
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        sentiment = "Neutral"
        suggestion = None

        if polarity < 0:
            sentiment = "Negative"
            suggestion = (
                "Try deep breathing: inhale for 4 seconds, hold for 4, exhale for 4."
            )
        elif polarity > 0:
            sentiment = "Positive"
            suggestion = "That’s fantastic to hear! How about celebrating by doing something you love, like listening to your favorite music?"
        else:
            sentiment = "Neutral"

        lowered_text = text.lower()
        if "yes" in lowered_text and "youtube" in bot_response.lower():
            bot_response = "Search YouTube for guided meditations, nature soundscapes, or even calm music playlists. Finding something soothing can make a difference."
            suggestion = None

        print("---> Response:", bot_response)

        return {
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
        }, 200
    except Exception as e:
        print(e)
        return {"error": f"AI error: {str(e)}"}, 500


@app.route("/analyze", methods=["POST"])
def analyze_chat():
    """Handle text input from the Flutter app."""
    data = request.get_json()
    text = data.get("text", "").strip()
    result, status_code = analyze_text(text)
    return jsonify(result), status_code


@app.route("/analyze_audio", methods=["POST"])
def analyze_audio():
    """Handle audio input from the Flutter app."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return jsonify({"error": "No audio file selected"}), 400

    # Save the audio file temporarily
    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    audio_path = os.path.join(temp_dir, audio_file.filename)
    audio_file.save(audio_path)

    try:
        # Convert AAC to WAV using pydub
        wav_path = os.path.join(
            temp_dir, f"{os.path.splitext(audio_file.filename)[0]}.wav"
        )
        audio = AudioSegment.from_file(audio_path)
        audio.export(wav_path, format="wav")

        # Transcribe audio to text using SpeechRecognition
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            try:
                transcribed_text = recognizer.recognize_google(audio_data)
            except sr.UnknownValueError:
                return jsonify({"error": "No speech detected in audio"}), 400
            except sr.RequestError as e:
                return jsonify({"error": f"Speech recognition error: {str(e)}"}), 500

        # Print transcribed text to console using TTS
        print(f"---> User: {transcribed_text}")

        text_to_speech(transcribed_text)

        # Analyze the transcribed text
        result, status_code = analyze_text(transcribed_text)

        # Clean up temporary files
        os.remove(audio_path)
        os.remove(wav_path)

        return jsonify(result), status_code

    except Exception as e:
        print(e)
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        return jsonify({"error": f"Audio processing error: {str(e)}"}), 500


if __name__ == "__main__":
    ip_address = "0.0.0.0"  # Replace with your machine's IP
    app.run(host=ip_address, port=5000, debug=True)
