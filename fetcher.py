from dataclasses import dataclass
import feedparser
import httpx
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (newsai-bot) AppleWebKit/537.36"


@dataclass
class Article:
    title: str
    summary: str
    url: str
    source: str
    language: str
    tag: str
    image_url: str | None = None


def _extract_image(entry) -> str | None:
    media_content = entry.get("media_content")
    if media_content:
        for m in media_content:
            if m.get("url"):
                return m["url"]

    media_thumbnail = entry.get("media_thumbnail")
    if media_thumbnail:
        for m in media_thumbnail:
            if m.get("url"):
                return m["url"]

    for enc in entry.get("enclosures", []) or []:
        if enc.get("type", "").startswith("image"):
            return enc.get("href") or enc.get("url")

    summary_html = entry.get("summary", "")
    if summary_html:
        soup = BeautifulSoup(summary_html, "html.parser")
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]

    return None


def _clean_html(raw: str) -> str:
    if not raw:
        return ""
    text = BeautifulSoup(raw, "html.parser").get_text(separator=" ").strip()
    return " ".join(text.split())


def fetch_feed(source_name: str, url: str, language: str, tag: str, limit: int) -> list[Article]:
    feed = feedparser.parse(url, agent=UA)
    articles: list[Article] = []
    for entry in feed.entries[:limit]:
        link = entry.get("link")
        title = entry.get("title", "").strip()
        if not link or not title:
            continue

        summary = _clean_html(entry.get("summary", ""))
        if len(summary) > 500:
            summary = summary[:500].rsplit(" ", 1)[0] + "..."

        articles.append(
            Article(
                title=title,
                summary=summary,
                url=link,
                source=source_name,
                language=language,
                tag=tag,
                image_url=_extract_image(entry),
            )
        )
    return articles


def fetch_og_image(url: str) -> str | None:
    try:
        r = httpx.get(
            url,
            timeout=10,
            follow_redirects=True,
            headers={"User-Agent": UA},
        )
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        for selector in [
            {"property": "og:image"},
            {"name": "twitter:image"},
            {"name": "twitter:image:src"},
        ]:
            tag = soup.find("meta", attrs=selector)
            if tag and tag.get("content"):
                return tag["content"]
    except Exception:
        return None
    return None
