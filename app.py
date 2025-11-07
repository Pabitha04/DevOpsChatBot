from flask import Flask, request, jsonify, render_template
from datetime import datetime
import pytz
import requests
import os

app = Flask(__name__)

# Stores builds per project:
# { "user/repo": [ {commit, message, status, time} ] }
build_history = {}

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# Convert UTC → IST
def convert_to_ist(timestamp):
    utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    ist = pytz.timezone("Asia/Kolkata")
    return utc.astimezone(ist).strftime("%Y-%m-%d %H:%M:%S")

@app.route("/")
def home():
    return "✅ DevOps Chatbot running! Visit /ui to chat."

# ✅ Chat Endpoint
@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").lower()
    selected_project = request.json.get("project", None)

    if not selected_project or selected_project not in build_history:
        return jsonify({"reply": "❗ Select a project first from dropdown."})

    project_builds = build_history[selected_project]

    if "latest" in user_msg:
        latest = project_builds[-1]
        reply = (
            f"📌 Project: {selected_project}\n"
            f"Commit: {latest['commit']}\n"
            f"Message: {latest['message']}\n"
            f"Status: {latest['status']}\n"
            f"Time: {latest['time']} IST"
        )

    elif "history" in user_msg:
        reply = f"📜 Build history for {selected_project}:\n\n"
        for i, build in enumerate(project_builds[-5:], 1):
            reply += f"#{i} — {build['commit']} ({build['status']})\n"

    else:
        reply = (
            "🤖 Commands:\n"
            "👉 Show latest build\n"
            "👉 Show build history\n"
        )

    return jsonify({"reply": reply})


# ✅ GitHub Webhook (push event + status)
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    repo_name = data.get("repository", {}).get("full_name")
    if repo_name not in build_history:
        build_history[repo_name] = []

    # Handle push event → commit metadata
    if "head_commit" in data:
        commit = data["head_commit"]
        commit_id = commit["id"][:7]
        message = commit.get("message", "No message")
        timestamp = convert_to_ist(commit["timestamp"])
        build_history[repo_name].append({
            "commit": commit_id,
            "message": message,
            "status": "⏳ Build Triggered",
            "time": timestamp
        })
        return jsonify({"status": "Commit received"}), 200

    # ✅ Detect build completed (workflow_run)
    if data.get("workflow_run"):
        workflow = data["workflow_run"]
        commit_id = workflow["head_commit"]["id"][:7]
        status = "✅ Success" if workflow["conclusion"] == "success" else "❌ Failed"
        timestamp = convert_to_ist(workflow["updated_at"])

        build_history[repo_name].append({
            "commit": commit_id,
            "message": workflow["head_commit"]["message"],
            "status": status,
            "time": timestamp
        })

        return jsonify({"status": "Build status saved"}), 200

    return jsonify({"status": "Ignored"}), 200


# ✅ Send repo list to UI
@app.route("/projects")
def get_projects():
    return jsonify({"projects": list(build_history.keys())})


@app.route("/ui")
def ui():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
