from flask import Flask
import requests
import os
import time
import threading

app = Flask(__name__)

# Env variables
TRELLO_KEY = os.getenv("TRELLO_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_LIST_ID = os.getenv("TRELLO_LIST_ID")
CLICKUP_TOKEN = os.getenv("CLICKUP_TOKEN")
CLICKUP_LIST_ID = os.getenv("CLICKUP_ONBOARDING_LIST_ID")

# Store last seen card IDs
seen_cards = set()

def poll_trello():
    global seen_cards
    while True:
        url = f"https://api.trello.com/1/lists/{TRELLO_LIST_ID}/cards?key={TRELLO_KEY}&token={TRELLO_TOKEN}"
        resp = requests.get(url)
        if resp.status_code == 200:
            cards = resp.json()
            for card in cards:
                if card["id"] not in seen_cards:
                    seen_cards.add(card["id"])
                    create_clickup_task(card["name"], card.get("desc", ""))
        time.sleep(30)  # poll every 30s

def create_clickup_task(name, description):
    url = f"https://api.clickup.com/api/v2/list/{CLICKUP_LIST_ID}/task"
    headers = {"Authorization": CLICKUP_TOKEN, "Content-Type": "application/json"}
    payload = {"name": name, "description": description}
    resp = requests.post(url, headers=headers, json=payload)
    print("Created ClickUp task:", resp.status_code, resp.text)

@app.route("/")
def home():
    return "Trello → ClickUp sync running!", 200

if __name__ == "__main__":
    # Start polling in background
    t = threading.Thread(target=poll_trello, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000)
