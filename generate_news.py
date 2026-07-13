import requests
from bs4 import BeautifulSoup
from gtts import gTTS
from datetime import datetime, timezone
import json
import os
import re


POLIMER_URL = "https://www.polimernews.com/"
PUTHIYA_URL = "https://www.puthiyathalaimurai.com/"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/150 Safari/537.36"
    )
}


def clean_text(text):
    text = " ".join(text.split())
    return text.strip()


def contains_tamil(text):
    return bool(re.search(r"[\u0B80-\u0BFF]", text))


def remove_duplicates(headlines):
    unique = []
    seen = set()

    for headline in headlines:
        headline = clean_text(headline)

        key = headline.casefold()

        if key not in seen:
            seen.add(key)
            unique.append(headline)

    return unique


def valid_headline(text):
    if not contains_tamil(text):
        return False

    if len(text) < 20:
        return False

    if len(text) > 250:
        return False

    blocked_words = [
        "முகப்பு",
        "வீடியோ",
        "லைவ்",
        "தேடல்",
        "தொடர்புக்கு",
        "எங்களை பற்றி",
        "privacy",
        "copyright"
    ]

    text_lower = text.casefold()

    for word in blocked_words:
        if word.casefold() in text_lower:
            return False

    return True


def extract_headlines(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    headlines = []

    for tag in soup.find_all(
        ["h1", "h2", "h3", "h4"]
    ):
        text = clean_text(
            tag.get_text(" ", strip=True)
        )

        if valid_headline(text):
            headlines.append(text)

    return remove_duplicates(headlines)


def create_speech(
    polimer_headlines,
    puthiya_headlines
):
    parts = []

    parts.append(
        "வணக்கம். இன்றைய செய்தித் தலைப்புகள்."
    )

    parts.append(
        "முதலில் பாலிமர் செய்திகள்."
    )

    for headline in polimer_headlines:
        parts.append(headline)

    parts.append(
        "இத்துடன் பாலிமர் செய்தித் தலைப்புகள் "
        "நிறைவடைந்தன."
    )

    parts.append(
        "அடுத்து புதிய தலைமுறை செய்திகள்."
    )

    for headline in puthiya_headlines:
        parts.append(headline)

    parts.append(
        "இத்துடன் இன்றைய செய்தித் தலைப்புகள் "
        "நிறைவடைந்தன."
    )

    return ". ".join(parts)


def main():
    print("Getting Polimer headlines...")

    polimer = extract_headlines(
        POLIMER_URL
    )

    print(
        "Polimer headlines:",
        len(polimer)
    )

    for headline in polimer:
        print("POLIMER:", headline)

    print(
        "\nGetting Puthiya Thalaimurai headlines..."
    )

    puthiya = extract_headlines(
        PUTHIYA_URL
    )

    print(
        "Puthiya headlines:",
        len(puthiya)
    )

    for headline in puthiya:
        print("PUTHIYA:", headline)

    speech = create_speech(
        polimer,
        puthiya
    )

    os.makedirs(
        "public",
        exist_ok=True
    )

    print("\nCreating Tamil MP3...")

    tts = gTTS(
        text=speech,
        lang="ta"
    )

    tts.save(
        "public/latest-news.mp3"
    )

    now = datetime.now(
        timezone.utc
    )

    feed = [
        {
            "uid": "tamil-news-latest",
            "updateDate": now.strftime(
                "%Y-%m-%dT%H:%M:%S.0Z"
            ),
            "titleText": "Tamil News Headlines",
            "streamUrl": (
                "https://Dhanushyan2508.github.io/"
                "tamil-alexa-news/"
                "latest-news.mp3"
            ),
            "redirectionUrl": (
                "https://www.polimernews.com/"
            )
        }
    ]

    with open(
        "public/feed.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            feed,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\nCompleted successfully.")


if __name__ == "__main__":
    main()
