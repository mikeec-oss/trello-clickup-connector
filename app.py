import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load environment variables
TRELLO_KEY = os.getenv("TRELLO_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID")

CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY")
CLICKUP_ONBOARDING_LIST_ID = os.getenv("CLICKUP_ONBOARDING_LIST_ID")

# Home route
@app.route("/", methods=["GET"])
def home():
    return "Trello → ClickUp Connector is running!"

# Trello webhook route
@app.route("/trello-webhook", methods=["HEAD", "POST"])
def trello_webhook():
    if request.method == "HEAD":
        # Trello webhook verification
        return "", 200

    if request.method == "POST":
        data = request.json
        print("Webhook received:", json.dumps(data))

        # Check if it's a card creation event
        action = data.get("action", {})
        if action.get("type") == "createCard":
            card = action.get("data", {}).get("card", {})
            card_name = card.get("name")
            card_desc = card.get("desc", "")

            if card_name:
                # Send to ClickUp
                url = f"https://api.clickup.com/api/v2/list/{CLICKUP_ONBOARDING_LIST_ID}/task"
                headers = {
                    "Authorization": CLICKUP_API_KEY,
                    "Content-Type": "application/json",
                }
                payload = {
                    "name": card_name,
                    "description": card_desc
                }

                response = requests.post(url, headers=headers, json=payload)
                print("ClickUp API response:", response.status_code, response.text)

        return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
