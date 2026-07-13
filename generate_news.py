import os
import re
import json
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from gtts import gTTS


# ============================================================
# CONFIGURATION
# ============================================================

POLIMER_URL = "https://www.polimernews.com/"

AUDIO_URL = (
    "https://Dhanushyan2508.github.io/"
    "tamil-alexa-news/latest-news.mp3"
)

MAX_HEADLINES_PER_CATEGORY = 5


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/150.0.0.0 Safari/537.36"
    )
}


# ============================================================
# POLIMER NEWS CATEGORIES
# ============================================================

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


# ============================================================
# TEXT FUNCTIONS
# ============================================================

def clean_text(text):
    """
    Remove unnecessary spaces from text.
    """

    text = " ".join(text.split())

    return text.strip()


def contains_tamil(text):
    """
    Check whether text contains Tamil characters.
    """

    return bool(
        re.search(
            r"[\u0B80-\u0BFF]",
            text
        )
    )


def clean_for_speech(text):
    """
    Clean headline text for Tamil text-to-speech.
    """

    text = clean_text(text)

    quotation_marks = [
        "“",
        "”",
        "‘",
        "’",
        "‟",
        '"'
    ]

    for mark in quotation_marks:
        text = text.replace(mark, "")

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

    return text.strip(" .")


def valid_headline(text):
    """
    Validate whether text looks like a Tamil news headline.
    """

    if not text:
        return False

    if not contains_tamil(text):
        return False

    if len(text) < 20:
        return False

    if len(text) > 300:
        return False

    blocked_words = [
        "முகப்பு",
        "livetv",
        "live tv",
        "privacy",
        "copyright",
        "எங்களை பற்றி",
        "தொடர்புக்கு",
        "facebook",
        "twitter",
        "instagram",
        "youtube"
    ]

    text_lower = text.casefold()

    for word in blocked_words:
        if word.casefold() in text_lower:
            return False

    return True


def remove_duplicates(headlines):
    """
    Remove duplicate headlines.
    """

    unique_headlines = []

    seen = set()

    for headline in headlines:

        headline = clean_for_speech(
            headline
        )

        if not headline:
            continue

        key = headline.casefold()

        if key in seen:
            continue

        seen.add(key)

        unique_headlines.append(
            headline
        )

    return unique_headlines


# ============================================================
# GET CATEGORY LINKS
# ============================================================

def get_category_links():
    """
    Find category links from the Polimer News homepage.
    """

    print(
        "\nGetting Polimer category links..."
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

            category_url = urljoin(
                POLIMER_URL,
                link["href"]
            )

            category_links[text] = (
                category_url
            )

    print(
        "\nCategory links found:",
        len(category_links)
    )

    for category, url in category_links.items():

        print(
            f"CATEGORY: {category}"
        )

        print(
            f"URL: {url}"
        )

    return category_links


# ============================================================
# EXTRACT CATEGORY HEADLINES
# ============================================================

def extract_category_headlines(category, url):
    """
    Extract maximum 5 headlines from one category.
    """

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

        if not valid_headline(text):
            continue

        if text in CATEGORIES:
            continue

        headlines.append(
            text
        )

    headlines = remove_duplicates(
        headlines
    )

    # Maximum 5 headlines per category
    headlines = headlines[
        :MAX_HEADLINES_PER_CATEGORY
    ]

    return headlines


# ============================================================
# COLLECT POLIMER NEWS
# ============================================================

def collect_polimer_news():
    """
    Collect headlines category by category.
    """

    category_links = get_category_links()

    news = {}

    for category in CATEGORIES:

        if category not in category_links:

            print(
                "\nWARNING:"
            )

            print(
                f"Category not found: {category}"
            )

            continue

        category_url = category_links[
            category
        ]

        try:

            headlines = (
                extract_category_headlines(
                    category,
                    category_url
                )
            )

        except Exception as error:

            print(
                f"\nERROR getting {category}:"
            )

            print(error)

            continue

        news[category] = headlines

        print(
            f"\n{category}: "
            f"{len(headlines)} headlines"
        )

        for number, headline in enumerate(
            headlines,
            start=1
        ):

            print(
                f"{category} {number}: "
                f"{headline}"
            )

    return news


# ============================================================
# CREATE TAMIL SPEECH
# ============================================================

def create_speech(news):
    """
    Build category-wise Tamil speech.
    """

    speech_parts = []

    speech_parts.append(
        "வணக்கம்"
    )

    speech_parts.append(
        "பாலிமர் செய்தித் தலைப்புகள்"
    )

    first_category = True

    for category, spoken_name in (
        CATEGORIES.items()
    ):

        headlines = news.get(
            category,
            []
        )

        if not headlines:
            continue

        if first_category:

            speech_parts.append(
                f"முதலில் {spoken_name}"
            )

            first_category = False

        else:

            speech_parts.append(
                f"அடுத்து {spoken_name}"
            )

        for headline in headlines:

            speech_parts.append(
                headline
            )

    speech_parts.append(
        "இத்துடன் பாலிமர் "
        "செய்தித் தலைப்புகள் "
        "நிறைவடைந்தன"
    )

    speech_parts.append(
        "நன்றி"
    )

    speech = ". ".join(
        speech_parts
    )

    return speech


# ============================================================
# CREATE TAMIL AUDIO
# ============================================================

def create_audio(speech):
    """
    Generate Tamil MP3 using gTTS.
    """

    os.makedirs(
        "docs",
        exist_ok=True
    )

    print(
        "\nCreating Tamil audio..."
    )

    print(
        "Speech characters:",
        len(speech)
    )

    tts = gTTS(
        text=speech,
        lang="ta",
        slow=False
    )

    tts.save(
        "docs/latest-news.mp3"
    )

    audio_size = os.path.getsize(
        "docs/latest-news.mp3"
    )

    print(
        "Audio generated successfully."
    )

    print(
        "Audio size:",
        audio_size,
        "bytes"
    )


# ============================================================
# CREATE ALEXA FLASH BRIEFING FEED
# ============================================================

def create_feed():
    """
    Generate Alexa Flash Briefing JSON feed.
    """

    now = datetime.now(
        timezone.utc
    )

    feed = [
        {
            "uid": (
                "polimer-category-news"
            ),
            "updateDate": now.strftime(
                "%Y-%m-%dT%H:%M:%S.0Z"
            ),
            "titleText": (
                "Polimer News Headlines"
            ),
            "mainText": "",
            "streamUrl": AUDIO_URL,
            "redirectionUrl": (
                POLIMER_URL
            )
        }
    ]

    os.makedirs(
        "docs",
        exist_ok=True
    )

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

    print(
        "\nAlexa feed generated successfully."
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print(
        "================================"
    )

    print(
        "POLIMER CATEGORY NEWS GENERATOR"
    )

    print(
        "================================"
    )

    news = collect_polimer_news()

    total_headlines = sum(
        len(headlines)
        for headlines in news.values()
    )

    categories_with_news = sum(
        1
        for headlines in news.values()
        if headlines
    )

    print(
        "\n================================"
    )

    print(
        "NEWS SUMMARY"
    )

    print(
        "================================"
    )

    print(
        "Categories with news:",
        categories_with_news
    )

    print(
        "Total Polimer headlines:",
        total_headlines
    )

    print(
        "Maximum headlines per category:",
        MAX_HEADLINES_PER_CATEGORY
    )

    if total_headlines == 0:

        raise RuntimeError(
            "No Polimer headlines found."
        )

    speech = create_speech(
        news
    )

    print(
        "\nTotal speech characters:",
        len(speech)
    )

    create_audio(
        speech
    )

    create_feed()

    print(
        "\n================================"
    )

    print(
        "COMPLETED SUCCESSFULLY"
    )

    print(
        "================================"
    )

    print(
        "Audio URL:"
    )

    print(
        AUDIO_URL
    )


if __name__ == "__main__":
    main()
