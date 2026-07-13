import requests
from bs4 import BeautifulSoup
from gtts import gTTS
from datetime import datetime, timezone
from urllib.parse import urljoin
import json
import os
import re


POLIMER_URL = "https://www.polimernews.com/"

AUDIO_URL = (
    "https://Dhanushyan2508.github.io/"
    "tamil-alexa-news/latest-news.mp3"
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/150 Safari/537.36"
    )
}


# Categories Alexa should read.
# Website label -> Alexa spoken introduction

CATEGORIES = {
    "தமிழ்நாடு": "தமிழ்நாடு செய்திகள்",
    "இந்தியா": "இந்திய செய்திகள்",
    "அரசியல்": "அரசியல் செய்திகள்",
    "மாவட்டம்": "மாவட்ட செய்திகள்",
    "உலகம்": "உலக செய்திகள்",
    "விளையாட்டு": "விளையாட்டு செய்திகள்",
    "சினிமா": "சினிமா செய்திகள்",
    "வர்த்தகம்": "வர்த்தக செய்திகள்",
    "கல்வி": "கல்வி செய்திகள்",
    "வேலைவாய்ப்பு": "வேலைவாய்ப்பு செய்திகள்",
    "சுற்றுசூழல்": "சுற்றுச்சூழல் செய்திகள்",
    "டெக்னாலஜி": "தொழில்நுட்ப செய்திகள்",
}


def clean_text(text):

    text = " ".join(
        text.split()
    )

    return text.strip()


def contains_tamil(text):

    return bool(
        re.search(
            r"[\u0B80-\u0BFF]",
            text
        )
    )


def clean_for_speech(text):

    text = clean_text(text)

    quotation_marks = [
        "“",
        "”",
        "‘",
        "’",
        "‟"
    ]

    for mark in quotation_marks:
        text = text.replace(
            mark,
            ""
        )

    text = text.replace(
        "|",
        ". "
    )

    text = re.sub(
        r"\.{2,}",
        ".",
        text
    )

    text = re.sub(
        r"!+",
        ".",
        text
    )

    text = re.sub(
        r"\?+",
        "?",
        text
    )

    text = re.sub(
        r"\s+([.,?!])",
        r"\1",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip(
        " ."
    )


def valid_headline(text):

    if not contains_tamil(text):
        return False

    if len(text) < 20:
        return False

    if len(text) > 250:
        return False

    blocked = [
        "முகப்பு",
        "livetv",
        "privacy",
        "copyright",
        "எங்களை பற்றி",
        "தொடர்புக்கு"
    ]

    text_lower = text.casefold()

    for word in blocked:

        if word.casefold() in text_lower:
            return False

    return True


def remove_duplicates(headlines):

    unique = []

    seen = set()

    for headline in headlines:

        headline = clean_for_speech(
            headline
        )

        key = headline.casefold()

        if key not in seen:

            seen.add(key)

            unique.append(
                headline
            )

    return unique


def get_category_links():

    print(
        "Getting Polimer category links..."
    )

    response = requests.get(
        POLIMER_URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    category_links = {}

    for link in soup.find_all(
        "a",
        href=True
    ):

        text = clean_text(
            link.get_text(
                " ",
                strip=True
            )
        )

        if text in CATEGORIES:

            category_links[text] = urljoin(
                POLIMER_URL,
                link["href"]
            )

    return category_links


def extract_category_headlines(
    category,
    url
):

    print(
        f"\nGetting {category} headlines..."
    )

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
            tag.get_text(
                " ",
                strip=True
            )
        )

        if valid_headline(text):

            if text not in CATEGORIES:

                headlines.append(
                    text
                )

    headlines = remove_duplicates(
    headlines
)

# Keep only the latest 5 headlines
return headlines[:5]


def collect_polimer_news():

    category_links = get_category_links()

    news = {}

    for category in CATEGORIES:

        if category not in category_links:

            print(
                f"WARNING: Category not found: "
                f"{category}"
            )

            continue

        headlines = extract_category_headlines(
            category,
            category_links[category]
        )

        news[category] = headlines

        print(
            f"{category}: "
            f"{len(headlines)} headlines"
        )

        for number, headline in enumerate(
            headlines,
            1
        ):

            print(
                f"{category} {number}:",
                headline
            )

    return news


def create_speech(news):

    parts = []

    parts.append(
        "வணக்கம்."
    )

    parts.append(
        "பாலிமர் செய்தித் தலைப்புகள்."
    )

    first_category = True

    for category, spoken_name in CATEGORIES.items():

        headlines = news.get(
            category,
            []
        )

        if not headlines:
            continue

        if first_category:

            parts.append(
                f"முதலில் {spoken_name}."
            )

            first_category = False

        else:

            parts.append(
                f"அடுத்து {spoken_name}."
            )

        for headline in headlines:

            parts.append(
                headline
            )

    parts.append(
        "இத்துடன் பாலிமர் "
        "செய்தித் தலைப்புகள் "
        "நிறைவடைந்தன."
    )

    parts.append(
        "நன்றி."
    )

    return ". ".join(
        parts
    )


def create_audio(speech):

    os.makedirs(
        "docs",
        exist_ok=True
    )

    print(
        "\nCreating Tamil audio..."
    )

    tts = gTTS(
        text=speech,
        lang="ta",
        slow=False
    )

    tts.save(
        "docs/latest-news.mp3"
    )


def create_feed():

    now = datetime.now(
        timezone.utc
    )

    feed = [
        {
            "uid": "polimer-category-news",
            "updateDate": now.strftime(
                "%Y-%m-%dT%H:%M:%S.0Z"
            ),
            "titleText": (
                "Polimer News Headlines"
            ),
            "mainText": "",
            "streamUrl": AUDIO_URL,
            "redirectionUrl": POLIMER_URL
        }
    ]

    with open(
        "docs/feed.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            feed,
            file,
            ensure_ascii=False,
            indent=2
        )


def main():

    news = collect_polimer_news()

    total_headlines = sum(
        len(headlines)
        for headlines in news.values()
    )

    print(
        "\nTOTAL POLIMER HEADLINES:",
        total_headlines
    )

    if total_headlines == 0:

        raise RuntimeError(
            "No Polimer headlines found"
        )

    speech = create_speech(
        news
    )

    print(
        "Total speech characters:",
        len(speech)
    )

    create_audio(
        speech
    )

    create_feed()

    print(
        "\nCompleted successfully."
    )

    print(
        "Audio:",
        AUDIO_URL
    )


if __name__ == "__main__":
    main()
