import os
import json
import requests
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

KEYWORDS = [
    "uigeadail",
    "ardbeg uigeadail",
    "ウーガダール",
    "アードベッグ"
]

STATE_FILE = "last_seen.json"


def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )


def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_state(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)


def get_latest_item(keyword):

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox"
            ]
        )

        page = browser.new_page()

        page.goto(
            f"https://jp.mercari.com/search?keyword={keyword}&sort=created_time&order=desc",
            wait_until="domcontentloaded",
            timeout=120000
        )

        page.wait_for_timeout(5000)

        links = page.locator("a[href*='/item/']").all()

        if len(links) == 0:
            browser.close()
            return None

        href = links[0].get_attribute("href")

        title = links[0].inner_text().strip()

        browser.close()

        return {
            "id": href.split("/")[-1],
            "title": title,
            "url": f"https://jp.mercari.com{href}"
        }


def main():

    state = load_state()

    for keyword in KEYWORDS:

        latest = get_latest_item(keyword)

        if not latest:
            continue

        old_id = state.get(keyword)

        if old_id is None:
            state[keyword] = latest["id"]
            continue

        if latest["id"] != old_id:

            send_telegram(
                f"🚨 신규 등록 감지\n\n"
                f"키워드: {keyword}\n"
                f"{latest['title']}\n\n"
                f"{latest['url']}"
            )

            state[keyword] = latest["id"]

    save_state(state)


if __name__ == "__main__":
    main()
