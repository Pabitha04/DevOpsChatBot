from flask import Flask, request, jsonify, render_template
from datetime import datetime
import pytz
import requests
import os

app = Flask(__name__)

# Stores builds per project temporarily (RAM)
# { "user/repo": [ {commit, message, status, time} ] }
build_history = {}

# Read GitHub credentials from environment variables (Render / OS)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = os.getenv("GITHUB_USER")     # Example: "Pabitha04"
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}


# ✅ Convert UTC to IST
def convert_to_ist(timestamp):
    utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    ist = pytz.timezone("Asia/Kolkata")
    return utc.astimezone(ist).strftime("%Y-%m-%d %H:%M:%S IST")


# ✅ Fetch build history from GitHub (Not DB)
def fetch_builds_from_github(project):
    owner, repo = project.split("/")
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"

    response = requests.get(url, headers=HEADERS)
    runs = response.json().get("workflow_runs", [])[:5]

    formatted = []
    for run in runs:
        timestamp = convert_to_ist(run["created_at"])
        commit_msg = run.get("head_commit", {}).get("message", "No commit message")

        formatted.append({
            "commit": run["head_sha"][:7],
            "message": commit_msg,
            "status": "✅ Success" if run["conclusion"] == "success"
                      else ("❌ Failed" if run["conclusion"] == "failure" else "⏳ Build Triggered"),
            "time": timestamp
        })

    return formatted


@app.route("/")
def home():
    return "✅ DevOps Chatbot is running! Visit /ui to chat."


# ✅ Chat endpoint used by UI
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_msg = data.get("message", "").lower()
    selected_project = data.get("project")

    if not selected_project:
        return jsonify({"reply": "❗ Select a project first from dropdown."})

    # ALWAYS fetch latest builds from GitHub instead of DB
    builds = fetch_builds_from_github(selected_project)

    if not builds:
        return jsonify({"reply": f"📭 No builds available for {selected_project}."})

    # ✅ Latest build
    if "latest" in user_msg:
        build = builds[0]
        reply = (
            f"📌 Project: {selected_project}\n"
            f"🔹 Commit: {build['commit']}\n"
            f"🔹 Message: {build['message']}\n"
            f"🔹 Status: {build['status']}\n"
            f"🕒 Time: {build['time']}"
        )
        return jsonify({"reply": reply})

    # ✅ Build History
    elif "history" in user_msg:
        reply = f"📜 Build history for {selected_project}:\n\n"
        for build in builds:
            reply += (
                f"📌 Project: {selected_project}\n"
                f"🔹 Commit: {build['commit']}\n"
                f"🔹 Message: {build['message']}\n"
                f"🔹 Status: {build['status']}\n"
                f"🕒 Time: {build['time']}\n\n"
            )
        return jsonify({"reply": reply})

    else:
        return jsonify({"reply": "🤖 Try: 'show latest build' or 'show build history'"})



# ✅ Receives GitHub webhook (push + workflow events)
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    repo_name = data.get("repository", {}).get("full_name")

    if not repo_name:
        return jsonify({"status": "Ignored"}), 200

    # Only store minimal build tracking in memory, not full history
    if repo_name not in build_history:
        build_history[repo_name] = []

    # Push event → store commit
    if "head_commit" in data:
        commit = data["head_commit"]
        build_history[repo_name].append({
            "commit": commit["id"][:7],
            "message": commit.get("message", "No commit message"),
            "status": "⏳ Build Triggered",
            "time": convert_to_ist(commit["timestamp"])
        })

    # Workflow completion → update latest state
    if data.get("workflow_run"):
        workflow = data["workflow_run"]
        build_history[repo_name].append({
            "commit": workflow["head_commit"]["id"][:7],
            "message": workflow["head_commit"]["message"],
            "status": "✅ Success" if workflow["conclusion"] == "success" else "❌ Failed",
            "time": convert_to_ist(workflow["updated_at"])
        })

    return jsonify({"status": "Webhook processed"}), 200



# ✅ Send repo list to UI dropdown
@app.route("/projects")
def get_projects():
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
