import os
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# 🔑 API keys & IDs from environment
TRELLO_KEY = os.getenv("TRELLO_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_LIST_ID = os.getenv("TRELLO_LIST_ID")

CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY")
CLICKUP_LIST_ID = os.getenv("CLICKUP_ONBOARDING_LIST_ID")

# To remember last synced cards
synced_cards = set()

def sync_trello_to_clickup():
    url = f"https://api.trello.com/1/lists/{TRELLO_LIST_ID}/cards?key={TRELLO_KEY}&token={TRELLO_TOKEN}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("❌ Trello error:", response.text)
        return

    cards = response.json()
    for card in cards:
        card_id = card["id"]
        card_name = card["name"]

        if card_id not in synced_cards:
            # ✅ Create new ClickUp task
            clickup_url = f"https://api.clickup.com/api/v2/list/{CLICKUP_LIST_ID}/task"
            headers = {"Authorization": CLICKUP_API_KEY, "Content-Type": "application/json"}
            data = {"name": card_name}
            r = requests.post(clickup_url, headers=headers, json=data)

            if r.status_code == 200:
                print(f"✅ Synced: {card_name}")
                synced_cards.add(card_id)
            else:
                print("❌ ClickUp error:", r.text)

# 🔁 Schedule job every 2 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(func=sync_trello_to_clickup, trigger="interval", minutes=2)
scheduler.start()

@app.route("/")
def home():
    return "Trello → ClickUp sync is running 🚀"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
