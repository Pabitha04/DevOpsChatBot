from flask import Flask, request
import requests

app = Flask(__name__)

# Slack webhook URL will be added later
SLACK_WEBHOOK_URL = ""

@app.route('/notify', methods=['POST'])
def notify():
    data = request.json

    print("\n✅ Build Notification Received From Jenkins:")
    print(data)

    # Creating the message
    repo = data.get("repo", "Unknown Project")
    build_num = data.get("build_number", "N/A")
    status = data.get("status", "Unknown")

    message = f"🔔 Build Status: {status}\n📌 Project: {repo}\n🆔 Build Number: {build_num}"

    # If Slack webhook exists, send message
    if SLACK_WEBHOOK_URL:
        requests.post(SLACK_WEBHOOK_URL, json={"text": message})

    return {"message": "✅ Notification processed"}, 200


if __name__ == '__main__':
    app.run(port=5000)
