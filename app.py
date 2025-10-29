from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

latest_status = "No build info yet"

@app.route("/")
def home():
    return "✅ DevOps Chatbot is running! Visit /ui to open the chat interface."

@app.route("/ui")
def ui():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global latest_status
    user_msg = request.json.get("message", "").lower()
    if "status" in user_msg:
        reply = f"Latest Build Status: {latest_status}"
    else:
        reply = "Ask me: 'What is the build status?'"
    return jsonify({"reply": reply})

@app.route("/webhook", methods=["POST"])
def webhook():
    global latest_status
    data = request.json or {}
    latest_status = data.get("status", "unknown")
    print(f"✅ Webhook received! Build Status = {latest_status}")
    return jsonify({"message": "Webhook received"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)


from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

latest_status = "No build info yet"

@app.route("/")
def home():
    return "✅ DevOps Chatbot is running! Visit /ui to open the chat interface."

@app.route("/ui")
def ui():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global latest_status
    user_msg = request.json.get("message", "").lower()
    if "status" in user_msg:
        reply = f"Latest Build Status: {latest_status}"
    else:
        reply = "Ask me: 'What is the build status?'"
    return jsonify({"reply": reply})

@app.route("/webhook", methods=["POST"])
def webhook():
    global latest_status
    data = request.json or {}
    latest_status = data.get("status", "unknown")
    print(f"✅ Webhook received! Build Status = {latest_status}")
    return jsonify({"message": "Webhook received"}), 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)