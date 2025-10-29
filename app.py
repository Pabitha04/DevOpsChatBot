from flask import Flask, request, jsonify, render_template
import os

app = Flask(__name__)

# Store build status
latest_status = "No build info yet"

@app.route("/")
def home():
    return "✅ DevOps Chatbot is running! Visit /ui to open the chat interface."

# Chat route
@app.route("/chat", methods=["POST"])
def chat():
    global latest_status
    user_msg = request.json.get("message", "").lower()
    if "status" in user_msg:
        reply = f"Latest Build Status: {latest_status}"
    else:
        reply = "Ask me: 'What is the build status?'"
    return jsonify({"reply": reply})

# Webhook route (for GitHub Actions or CI tools)
@app.route("/webhook", methods=["POST"])
def webhook():
    global latest_status
    data = request.json or {}
    status = data.get("status", "unknown")
    latest_status = status
    print(f"✅ Webhook received! Build Status = {status}")
    return jsonify({"message": "Webhook received"}), 200

# Simple UI for the chatbot
@app.route("/ui")
def ui():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render provides dynamic PORT
    app.run(host="0.0.0.0", port=port)
