from flask import Flask, request, jsonify
import requests, os, logging, json, hmac, hashlib, base64

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY")
CLICKUP_ONBOARDING_LIST_ID = os.getenv("CLICKUP_ONBOARDING_LIST_ID")
CLICKUP_HEADERS = {"Authorization": CLICKUP_API_KEY, "Content-Type": "application/json"}

TRELLO_APP_SECRET = os.getenv("TRELLO_APP_SECRET")  # optional

@app.route("/", methods=["GET"])
def health():
    return "Trello → ClickUp connector alive!", 200

@app.route("/trello-webhook", methods=["HEAD", "POST"])
def trello_webhook():
    if request.method == "HEAD":
        return "", 200

    payload = request.get_json(force=True, silent=True) or {}
    app.logger.info("Trello payload: %s", json.dumps(payload)[:1000])

    if TRELLO_APP_SECRET:
        header = request.headers.get("x-trello-webhook")
        raw_body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        signed = hmac.new(
            TRELLO_APP_SECRET.encode("utf-8"),
            (raw_body + request.url).encode("utf-8"),
            hashlib.sha1
        ).digest()
        expected = base64.b64encode(signed).decode()
        if not header or not hmac.compare_digest(expected, header):
            return jsonify({"error": "bad signature"}), 403

    action = payload.get("action", {})
    if action.get("type") == "createCard":
        card = action.get("data", {}).get("card", {})
        task_payload = {"name": card.get("name", "Trello Card"), "content": card.get("desc", "")}
        url = f"https://api.clickup.com/api/v2/list/{CLICKUP_ONBOARDING_LIST_ID}/task"
        r = requests.post(url, headers=CLICKUP_HEADERS, json=task_payload, timeout=15)
        return jsonify(r.json()), r.status_code

    return jsonify({"ignored": True}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
