from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# In-memory store for build info
build_history = []


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Chatbot responses for build info."""
    user_message = request.json.get("message", "").lower()

    if "history" in user_message:
        if not build_history:
            return jsonify(reply="📭 No builds recorded yet.")
        history_text = "\n\n".join(
            [
                f"🧱 Build #{i+1}\n"
                f"Commit: {b['commit']}\n"
                f"Author: {b['author']}\n"
                f"Message: {b['message']}\n"
                f"Status: {b['status']}\n"
                f"Time: {b['time']}"
                for i, b in enumerate(reversed(build_history[-5:]))  # Show last 5 builds
            ]
        )
        return jsonify(reply=f"📜 Recent Build History:\n\n{history_text}")

    elif "latest" in user_message or "status" in user_message:
        if not build_history:
            return jsonify(reply="🚫 No build data available yet.")
        latest = build_history[-1]
        reply = (
            f"✅ Latest Build Info\n"
            f"Commit: {latest['commit']}\n"
            f"Author: {latest['author']}\n"
            f"Message: {latest['message']}\n"
            f"Status: {latest['status']}\n"
            f"Time: {latest['time']}"
        )
        return jsonify(reply=reply)

    else:
        return jsonify(reply="💬 Try asking: 'Show latest build' or 'Show build history'")


@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint for GitHub or CI tools."""
    data = request.json

    try:
        commit_id = data["head_commit"]["id"][:7]
        author = data["head_commit"]["author"]["name"]
        message = data["head_commit"]["message"]
    except Exception:
        # fallback for manual testing or different payload format
        commit_id = data.get("commit", "unknown")[:7]
        author = data.get("author", "unknown")
        message = data.get("message", "No message")

    status = "Build Successful ✅"  # You can later make this dynamic from CI

    build_history.append({
        "commit": commit_id,
        "author": author,
        "message": message,
        "status": status,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    print(f"[Webhook] ✅ Build recorded: {commit_id} by {author}")
    return jsonify({"message": "Build recorded successfully"}), 200


if __name__ == "__main__":
    # Render assigns a dynamic port — this ensures compatibility
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
