from flask import Flask, request, jsonify, render_template
from datetime import datetime
import pytz
import requests
import os

app = Flask(__name__)

# Stores builds per project:
# { "user/repo": [ {commit, message, status, time} ] }
build_history = {}

# Read GitHub credentials from environment variables (Render / OS)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = os.getenv("GITHUB_USER")     # <--- e.g., "Pabitha04"

HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}


# Convert UTC → IST
def convert_to_ist(timestamp):
    utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    ist = pytz.timezone("Asia/Kolkata")
    return utc.astimezone(ist).strftime("%Y-%m-%d %H:%M:%S")


@app.route("/")
def home():
    return "✅ DevOps Chatbot is running! Visit /ui to chat."


# ✅ Chat Endpoint (UI → Chatbot)
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_msg = data.get("message", "").lower()
    selected_project = data.get("project")

    if not selected_project:
        return jsonify({"reply": "❗ Select a project from dropdown first."})

    if selected_project not in build_history or len(build_history[selected_project]) == 0:
        return jsonify({"reply": f"📭 No builds yet for {selected_project}."})

    project_builds = build_history[selected_project]

    if "latest" in user_msg:
        latest = project_builds[-1]
        reply = (
            f"📌 Project: {selected_project}\n"
            f"🔹 Commit: {latest['commit']}\n"
            f"🔹 Message: {latest['message']}\n"
            f"🔹 Status: {latest['status']}\n"
            f"🕒 Time: {latest['time']} IST"
        )

    elif "history" in user_msg:
        reply = f"📜 Build history for {selected_project}:\n\n"
        for i, build in enumerate(project_builds[-5:], 1):
            reply += f"{i}. {build['commit']} — {build['status']}\n"

    else:
        reply = (
            "🤖 Available commands:\n"
            "👉 Show latest build\n"
            "👉 Show build history"
        )

    return jsonify({"reply": reply})


# ✅ GitHub Webhook (push event + workflow status)
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    repo_name = data.get("repository", {}).get("full_name")
    if not repo_name:
        return jsonify({"status": "No repo info"}), 200

    if repo_name not in build_history:
        build_history[repo_name] = []

    # Handle PUSH event → commit detected
    if "head_commit" in data:
        commit = data["head_commit"]
        commit_id = commit["id"][:7]
        message = commit.get("message", "No commit message")
        timestamp = convert_to_ist(commit["timestamp"])

        build_history[repo_name].append({
            "commit": commit_id,
            "message": message,
            "status": "⏳ Build Triggered",
            "time": timestamp
        })

        return jsonify({"status": "Commit received"}), 200

    # Handle WORKFLOW_RUN → build completed
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


# ✅ Fetch project list from GitHub for dropdown
@app.route("/projects")
def get_projects():
    if not GITHUB_USER:
        return jsonify({"projects": []})

    url = f"https://api.github.com/users/{GITHUB_USER}/repos"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        repos = [repo["full_name"] for repo in response.json()]
        return jsonify({"projects": repos})

    return jsonify({"projects": []})


@app.route("/ui")
def ui():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
