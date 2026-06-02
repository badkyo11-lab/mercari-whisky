import os
import json
import requests
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
KEYWORD = os.environ.get("KEYWORD", "uigeadail")

SEEN_FILE = "seen_items.json"


def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )


def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def check_mercari():
    seen = load_seen()

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
            f"https://jp.mercari.com/search?keyword={KEYWORD}",
            wait_until="domcontentloaded",
            timeout=120000
        )

        page.wait_for_timeout(10000)

        links = page.locator("a[href*='/item/']").all()

        for link in links[:20]:
            href = link.get_attribute("href")

            if not href:
                continue

            item_id = href.split("/")[-1]

            if item_id in seen:
                continue

            title = link.inner_text().strip()

            if not title:
                title = "Mercari Item"

            send_telegram(
                f"🚨 Mercari 신규 등록\n\n"
                f"{title}\n\n"
                f"https://jp.mercari.com{href}"
            )

            seen.add(item_id)

        browser.close()

    save_seen(seen)


if __name__ == "__main__":
    check_mercari()
