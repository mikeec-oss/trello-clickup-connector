import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ----------------------------
# Health check
# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "Trello ↔ ClickUp connector is running ✅"


# ----------------------------
# Register webhook in Trello
# ----------------------------
@app.route("/register-webhook", methods=["GET"])
def register_webhook():
    key = os.getenv("TRELLO_KEY")
    token = os.getenv("TRELLO_TOKEN")
    board_id = os.getenv("TRELLO_BOARD_ID")

    if not key or not token or not board_id:
        return jsonify({"error": "Missing TRELLO_KEY, TRELLO_TOKEN, or TRELLO_BOARD_ID in environment"}), 400

    callback_url = "https://trello-clickup-connector.onrender.com/trello-webhook"

    resp = requests.post(
        f"https://api.trello.com/1/webhooks/?key={key}&token={token}",
        json={
            "description": "Current Projects",
            "callbackURL": callback_url,
            "idModel": board_id
        }
    )

    return (resp.text, resp.status_code)


# ----------------------------
# Webhook endpoint Trello calls
# ----------------------------
@app.route("/trello-webhook", methods=["HEAD", "GET", "POST"])
def trello_webhook():
    if request.method == "HEAD":
        return "", 200  # Trello uses HEAD to validate
    # handle POST events here
    return "", 200

    data = request.json
    if not data:
        return jsonify({"status": "no data"}), 200

    # Look at Trello action type
    action = data.get("action", {})
    action_type = action.get("type")
    card = action.get("data", {}).get("card", {})

    if action_type == "createCard" and "onboarding" in card.get("name", "").lower():
        # Send to ClickUp
        CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY")
        list_id = os.getenv("CLICKUP_ONBOARDING_LIST_ID")

        if not clickup_token or not list_id:
            return jsonify({"error": "Missing CLICKUP_TOKEN or CLICKUP_ONBOARDING_LIST_ID"}), 400

        resp = requests.post(
            f"https://api.clickup.com/api/v2/list/{list_id}/task",
            headers={"Authorization": clickup_api_key, "Content-Type": "application/json"},
            json={"name": card["name"], "status": "to do"}
        )

        return jsonify({"trello": card, "clickup_response": resp.json()}), resp.status_code

    return jsonify({"status": "ignored"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
