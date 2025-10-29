from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

# Store build history
build_history = []

@app.route("/")
def home():
    return "✅ DevOps Chatbot is running! Visit /ui to chat."

# --- Chatbot Route ---
@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").lower()

    if "latest" in user_msg or "status" in user_msg:
        if not build_history:
            reply = "🚫 No build data available yet."
        else:
            latest = build_history[-1]
            reply = (
                f"✅ Latest Build Info\n"
                f"Commit: {latest['commit']}\n"
                f"Author: {latest['author']}\n"
                f"Message: {latest['message']}\n"
                f"Status: {latest['status']}\n"
                f"Time: {latest['time']}"
            )

    elif "history" in user_msg or "previous" in user_msg:
        if not build_history:
            reply = "📭 No builds recorded yet."
        else:
            reply = "🧾 Build History:\n\n"
            for i, build in enumerate(build_history[-5:], 1):
                reply += (
                    f"#{i} — {build['commit']} by {build['author']}\n"
                    f"   Message: {build['message']}\n"
                    f"   Status: {build['status']}\n"
                    f"   Time: {build['time']}\n\n"
                )

    else:
        reply = (
            "Hi! I'm your CI/CD assistant.\n\n"
            "Ask me:\n"
            "👉 'Show latest build'\n"
            "👉 'Show build history'"
        )

    return jsonify({"reply": reply})

# --- GitHub Webhook Route ---
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if data is None:
        return jsonify({"error": "Invalid payload"}), 400

    # GitHub sends 'ping' when you first add the webhook
    if 'zen' in data:
        print("🔔 Received GitHub ping event")
        return jsonify({"status": "Ping received"}), 200

    # Handle actual push event
    if 'head_commit' in data:
        latest_commit = data['head_commit']
        commit_id = latest_commit.get('id', 'unknown')[:7]
        author = latest_commit.get('author', {}).get('name', 'unknown')
        message = latest_commit.get('message', 'No message')
        timestamp = latest_commit.get('timestamp', datetime.utcnow().isoformat())

        build_entry = {
            "commit": commit_id,
            "author": author,
            "message": message,
            "status": "Build Successful ✅",
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

        build_history.append(build_entry)
        print(f"✅ Build recorded: {build_entry}")
        return jsonify({"status": "Build recorded"}), 200

    return jsonify({"status": "Ignored event"}), 200

# --- UI Route ---
@app.route("/ui")
def ui():
    return render_template("index.html")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
