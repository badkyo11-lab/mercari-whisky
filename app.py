import os
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

def send_telegram(message):
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )
    print(r.text)

def check_keyword(keyword):
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
            f"https://jp.mercari.com/search?keyword={keyword}",
            wait_until="domcontentloaded",
            timeout=120000
        )

        page.wait_for_timeout(5000)

        links = page.locator("a[href*='/item/']").all()

        print(f"{keyword}: {len(links)} items")

        if len(links) > 0:
            href = links[0].get_attribute("href")

            if href:
                send_telegram(
                    f"🔍 검색 확인\n"
                    f"키워드: {keyword}\n"
                    f"https://jp.mercari.com{href}"
                )

        browser.close()

if __name__ == "__main__":
    try:
        for keyword in KEYWORDS:
            check_keyword(keyword)

    except Exception as e:
        send_telegram(f"❌ 오류 발생\n{str(e)}")
