import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL", "@realyangilik")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "15"))
POST_INTERVAL_MINUTES = int(os.getenv("POST_INTERVAL_MINUTES", "35"))
DB_PATH = os.getenv("DB_PATH", "news.db")
PRESET = os.getenv("PRESET", "general").lower()

# Har bir manba: (nom, RSS URL, til, hashtag)
SOURCE_PRESETS: dict[str, list[tuple[str, str, str, str]]] = {
    "general": [
        ("Kun.uz",      "https://kun.uz/news/rss",                       "uz", "#kun_uz"),
        ("Gazeta.uz",   "https://www.gazeta.uz/oz/rss/",                 "uz", "#gazeta"),
        ("Spot.uz",     "https://www.spot.uz/ru/rss/",                   "ru", "#biznes"),
        ("BBC World",   "https://feeds.bbci.co.uk/news/world/rss.xml",   "en", "#dunyo"),
        ("Al Jazeera",  "https://www.aljazeera.com/xml/rss/all.xml",     "en", "#dunyo"),
        ("Championat",  "https://www.championat.com/rss/news/",          "ru", "#sport"),
    ],
    "football": [
        ("BBC Sport",        "https://feeds.bbci.co.uk/sport/football/rss.xml", "en", "#futbol"),
        ("Sky Sports",       "https://www.skysports.com/rss/12040",             "en", "#futbol"),
        ("ESPN Soccer",      "https://www.espn.com/espn/rss/soccer/news",       "en", "#futbol"),
        ("FourFourTwo",      "https://www.fourfourtwo.com/feeds.xml",           "en", "#futbol"),
        ("Football Italia",  "https://www.football-italia.net/rss.xml",         "en", "#futbol"),
    ],
}

if PRESET not in SOURCE_PRESETS:
    raise ValueError(f"Noma'lum PRESET='{PRESET}'. Mavjudlar: {list(SOURCE_PRESETS)}")

SOURCES = SOURCE_PRESETS[PRESET]

# Har bir manbadan bir yurishda nechta yangilik ko'rib chiqiladi
MAX_ARTICLES_PER_SOURCE = 5
