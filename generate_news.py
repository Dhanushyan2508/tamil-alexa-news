import requests
from bs4 import BeautifulSoup
from gtts import gTTS
from datetime import datetime, timezone
import json
import os
import re


POLIMER_URL = "https://www.polimernews.com/"
PUTHIYA_URL = "https://www.puthiyathalaimurai.com/"

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


def clean_text(text):
    text = " ".join(text.split())
    return text.strip()


def contains_tamil(text):
    return bool(
        re.search(r"[\u0B80-\u0BFF]", text)
    )


def clean_for_speech(text):
    """
    Make website headline text sound better
    when spoken by Tamil TTS.
    """

    text = clean_text(text)

    # Remove website-style quotation marks
    text = text.replace("“", "")
    text = text.replace("”", "")
    text = text.replace("‘", "")
    text = text.replace("’", "")
    text = text.replace("‟", "")

    # Replace pipes with pauses
    text = text.replace("|", ". ")

    # Remove repeated dots
    text = re.sub(
        r"\.{2,}",
        ".",
        text
    )

    # Remove repeated exclamation marks
    text = re.sub(
        r"!+",
        ".",
        text
    )

    # Remove repeated question marks
    text = re.sub(
        r"\?+",
        "?",
        text
    )

    # Clean spaces before punctuation
    text = re.sub(
        r"\s+([.,?!])",
        r"\1",
        text
    )

    # Clean repeated spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip(" .")


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
        "தேடல்",
        "தொடர்புக்கு",
        "எங்களை பற்றி",
        "privacy policy",
        "copyright",
        "terms and conditions"
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
            tag.get_text(
                " ",
                strip=True
            )
        )

        if valid_headline(text):
            headlines.append(text)

    return remove_duplicates(
        headlines
    )


def create_speech(
    polimer_headlines,
    puthiya_headlines
):

    parts = []

    parts.append(
        "வணக்கம். "
        "இன்றைய செய்தித் தலைப்புகள்."
    )

    parts.append(
        "முதலில் பாலிமர் செய்திகள்."
    )

    for headline in polimer_headlines:
        parts.append(headline)

    parts.append(
        "இத்துடன் பாலிமர் "
        "செய்தித் தலைப்புகள் நிறைவடைந்தன."
    )

    parts.append(
        "அடுத்து புதிய தலைமுறை செய்திகள்."
    )

    for headline in puthiya_headlines:
        parts.append(headline)

    parts.append(
        "இத்துடன் புதிய தலைமுறை "
        "செய்தித் தலைப்புகள் நிறைவடைந்தன."
    )

    parts.append(
        "நன்றி. மீண்டும் அடுத்த "
        "செய்தி நேரத்தில் சந்திப்போம்."
    )

    return ". ".join(parts)


def create_audio(speech):

    os.makedirs(
        "docs",
        exist_ok=True
    )

    print(
        "\nCreating Tamil news audio..."
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
            "uid": "tamil-news-latest",
            "updateDate": now.strftime(
                "%Y-%m-%dT%H:%M:%S.0Z"
            ),
            "titleText": (
                "Tamil News Headlines"
            ),
            "mainText": "",
            "streamUrl": AUDIO_URL,
            "redirectionUrl": (
                "https://www.polimernews.com/"
            )
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

    print(
        "Getting Polimer headlines..."
    )

    polimer = extract_headlines(
        POLIMER_URL
    )

    print(
        "Polimer headlines:",
        len(polimer)
    )

    for number, headline in enumerate(
        polimer,
        1
    ):

        print(
            f"POLIMER {number}:",
            headline
        )


    print(
        "\nGetting Puthiya "
        "Thalaimurai headlines..."
    )

    puthiya = extract_headlines(
        PUTHIYA_URL
    )

    print(
        "Puthiya headlines:",
        len(puthiya)
    )

    for number, headline in enumerate(
        puthiya,
        1
    ):

        print(
            f"PUTHIYA {number}:",
            headline
        )


    if not polimer and not puthiya:

        raise RuntimeError(
            "No Tamil news headlines found"
        )


    speech = create_speech(
        polimer,
        puthiya
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
        "\nCompleted successfully."
    )

    print(
        "Audio:",
        AUDIO_URL
    )

    print(
        "Feed:",
        "https://Dhanushyan2508.github.io/"
        "tamil-alexa-news/feed.json"
    )


if __name__ == "__main__":
    main()
