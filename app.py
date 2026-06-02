import os
import json
import random
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

KEYWORDS = [
    "uigeadail",
    "ardbeg uigeadail",
    "ウーガダール",
    "アードベッグ"
]

STATE_FILE = "last_seen.json"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"
]


# ----------------------------
# Telegram
# ----------------------------
def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=15
        )
    except:
        pass


# ----------------------------
# state
# ----------------------------
def load_state():
    try:
        return json.load(open(STATE_FILE))
    except:
        return {}


def save_state(data):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, STATE_FILE)


# ----------------------------
# fetch (lightweight HTTP)
# ----------------------------
def fetch_latest(keyword):

    url = f"https://jp.mercari.com/search?keyword={keyword}&sort=created_time&order=desc"

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "ja,en;q=0.9"
    }

    for i in range(3):
        try:
            time.sleep(random.uniform(1.0, 2.5))  # anti-bot delay

            r = requests.get(url, headers=headers, timeout=10)

            if r.status_code != 200:
                continue

            soup = BeautifulSoup(r.text, "html.parser")

            a = soup.select_one("a[href*='/item/']")

            if not a:
                continue

            href = a.get("href")
            title = a.get_text(strip=True)

            if not href:
                continue

            return {
                "id": href.split("/")[-1],
                "title": title,
                "url": "https://jp.mercari.com" + href
            }

        except:
            time.sleep(2 ** i)

    return None


# ----------------------------
# worker
# ----------------------------
def process(keyword, state, new_state):

    latest = fetch_latest(keyword)

    if not latest:
        return

    old = state.get(keyword)

    if old is None:
        new_state[keyword] = latest["id"]
        return

    if latest["id"] != old:

        send_telegram(
            f"🚨 NEW ITEM\n\n"
            f"{keyword}\n"
            f"{latest['title']}\n\n"
            f"{latest['url']}"
        )

        new_state[keyword] = latest["id"]
    else:
        new_state[keyword] = old


# ----------------------------
# main
# ----------------------------
def main():

    state = load_state()
    new_state = state.copy()

    with ThreadPoolExecutor(max_workers=3) as ex:
        ex.map(lambda k: process(k, state, new_state), KEYWORDS)

    save_state(new_state)


if __name__ == "__main__":
    main()
