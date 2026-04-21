import html
import httpx

from fetcher import Article

TG_API = "https://api.telegram.org/bot{token}/{method}"
CAPTION_LIMIT = 1024
TEXT_LIMIT = 4096


def _escape(s: str) -> str:
    return html.escape(s or "", quote=False)


def _build(title: str, summary: str, source: str, url: str, tag: str, limit: int) -> str:
    head = f"<b>{_escape(title)}</b>"
    footer = (
        f"\n\n🔗 Manba: {_escape(source)}\n"
        f"👉 <a href=\"{_escape(url)}\">To'liq o'qish</a>\n\n"
        f"{tag} #yangilik"
    )
    body = _escape(summary)
    text = f"{head}\n\n{body}{footer}"

    if len(text) <= limit:
        return text

    available = limit - len(head) - len(footer) - 4
    if available < 50:
        return f"{head}{footer}"[:limit]

    trimmed = body[: available - 3].rsplit(" ", 1)[0] + "..."
    return f"{head}\n\n{trimmed}{footer}"


def send(
    token: str,
    channel: str,
    article: Article,
    title: str,
    summary: str,
    dry_run: bool = False,
) -> bool:
    has_image = bool(article.image_url)
    limit = CAPTION_LIMIT if has_image else TEXT_LIMIT
    text = _build(title, summary, article.source, article.url, article.tag, limit)

    if dry_run:
        print("--- DRY RUN ---")
        print(f"Image: {article.image_url or '(none)'}")
        print(text)
        print("---")
        return True

    if has_image:
        try:
            r = httpx.post(
                TG_API.format(token=token, method="sendPhoto"),
                data={
                    "chat_id": channel,
                    "photo": article.image_url,
                    "caption": text,
                    "parse_mode": "HTML",
                },
                timeout=30,
            )
            if r.status_code == 200 and r.json().get("ok"):
                return True
            print(f"  [photo failed, fallback to text] {r.text[:200]}")
        except Exception as e:
            print(f"  [photo exception: {e}]")

    text = _build(title, summary, article.source, article.url, article.tag, TEXT_LIMIT)
    r = httpx.post(
        TG_API.format(token=token, method="sendMessage"),
        data={
            "chat_id": channel,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=30,
    )
    if r.status_code != 200 or not r.json().get("ok"):
        print(f"  [send failed] {r.text[:200]}")
        return False
    return True
