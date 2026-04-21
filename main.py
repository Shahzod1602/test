import argparse
import sys
import time
from datetime import datetime, timedelta

import config
import db
import fetcher
import publisher
import translator

LAST_POST_KEY = "last_post_at"
LAST_INDEX_KEY = "last_source_index"
FETCH_POOL = 10  # rotation rejimida har manbadan tekshiriladigan oxirgi yangiliklar


def _ensure_keys() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        sys.exit("TELEGRAM_BOT_TOKEN .env da ko'rsatilmagan")
    if not config.GEMINI_API_KEY:
        sys.exit("GEMINI_API_KEY .env da ko'rsatilmagan")


def _send_one(article: fetcher.Article, dry_run: bool) -> bool:
    if not article.image_url:
        article.image_url = fetcher.fetch_og_image(article.url)
    title_uz, summary_uz = translator.translate_to_uzbek(
        article.title, article.summary, article.language
    )
    ok = publisher.send(
        config.TELEGRAM_BOT_TOKEN,
        config.TELEGRAM_CHANNEL,
        article,
        title_uz,
        summary_uz,
        dry_run=dry_run,
    )
    if ok and not dry_run:
        db.mark_sent(config.DB_PATH, article.url, article.source, title_uz)
    if ok:
        print(f"  ✓ {title_uz[:80]}")
    else:
        print(f"  ✗ {article.title[:80]}")
    return ok


def _pick_unsent(source_tuple, pool: int) -> fetcher.Article | None:
    name, url, lang, tag = source_tuple
    try:
        articles = fetcher.fetch_feed(name, url, lang, tag, pool)
    except Exception as e:
        print(f"  ! feed olishda xato: {e}")
        return None
    for a in articles:
        if not db.is_sent(config.DB_PATH, a.url):
            return a
    return None


def run_once(dry_run: bool = False, max_per_source: int | None = None) -> None:
    _ensure_keys()
    translator.init(config.GEMINI_API_KEY)
    db.init(config.DB_PATH)

    limit = max_per_source or config.MAX_ARTICLES_PER_SOURCE
    sent = skipped = 0

    for source in config.SOURCES:
        name, url, lang, tag = source
        print(f"\n[*] {name} ({lang})")
        try:
            articles = fetcher.fetch_feed(name, url, lang, tag, limit)
        except Exception as e:
            print(f"  ! feed olishda xato: {e}")
            continue

        for a in articles:
            if db.is_sent(config.DB_PATH, a.url):
                skipped += 1
                continue
            try:
                if _send_one(a, dry_run):
                    sent += 1
                time.sleep(2)
            except Exception as e:
                print(f"  ! xato: {e}")

    print(f"\n[=] Natija: {sent} yuborildi, {skipped} allaqachon mavjud")


def rotation_tick(dry_run: bool = False) -> bool:
    _ensure_keys()
    translator.init(config.GEMINI_API_KEY)
    db.init(config.DB_PATH)

    last_idx_raw = db.get_state(config.DB_PATH, LAST_INDEX_KEY)
    last_idx = int(last_idx_raw) if last_idx_raw is not None else -1

    n = len(config.SOURCES)
    for offset in range(n):
        idx = (last_idx + 1 + offset) % n
        source = config.SOURCES[idx]
        name = source[0]
        print(f"[*] Rotation: {name} (index {idx})")

        article = _pick_unsent(source, FETCH_POOL)
        if article is None:
            print(f"  - {name}: yangi yangilik yo'q, keyingisiga o'tamiz")
            continue

        try:
            if _send_one(article, dry_run):
                if not dry_run:
                    db.set_state(config.DB_PATH, LAST_INDEX_KEY, str(idx))
                    db.set_state(config.DB_PATH, LAST_POST_KEY, datetime.now().isoformat())
                return True
        except Exception as e:
            print(f"  ! xato: {e}")
            continue

    print("[=] Hech qaysi manbadan yangi yangilik topilmadi")
    return False


def run_rotation_loop(dry_run: bool = False) -> None:
    _ensure_keys()
    db.init(config.DB_PATH)

    interval = timedelta(minutes=config.POST_INTERVAL_MINUTES)
    print(f"[i] Rotation rejimi: har {config.POST_INTERVAL_MINUTES} daqiqada 1 manbadan 1 yangilik")
    print(f"[i] Manbalar tartibi: {[s[0] for s in config.SOURCES]}")

    while True:
        try:
            last_post_raw = db.get_state(config.DB_PATH, LAST_POST_KEY)
            now = datetime.now()

            if last_post_raw:
                last_post = datetime.fromisoformat(last_post_raw)
                next_post = last_post + interval
                wait_seconds = (next_post - now).total_seconds()
            else:
                wait_seconds = 0

            if wait_seconds > 0:
                mins = int(wait_seconds // 60)
                print(f"[z] Keyingi post {mins} daqiqadan keyin ({(now + timedelta(seconds=wait_seconds)).strftime('%H:%M')})")
                time.sleep(min(wait_seconds, 300))
                continue

            print(f"\n--- {now.strftime('%Y-%m-%d %H:%M:%S')} ---")
            rotation_tick(dry_run=dry_run)

        except KeyboardInterrupt:
            print("\n[i] To'xtatildi")
            return
        except Exception as e:
            print(f"[!!] Kutilmagan xato: {e}")
            time.sleep(60)


def main() -> None:
    p = argparse.ArgumentParser(description="O'zbek yangiliklar kanali uchun AI bot")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true",
                      help="Hamma manbalardan bir martaga tekshirish")
    mode.add_argument("--rotate-once", action="store_true",
                      help="Rotation: faqat 1 ta yangilik yuborish (test uchun)")
    mode.add_argument("--rotate", action="store_true",
                      help="Rotation loop: har POST_INTERVAL_MINUTES daqiqada 1 yangilik")

    p.add_argument("--dry-run", action="store_true", help="Telegramga yubormaslik")
    p.add_argument("--limit", type=int, default=None, help="--once uchun: manbadan nechta")
    p.add_argument("--reset-rotation", action="store_true",
                   help="Rotation indeksini tiklash (keyingi post Kun.uz dan boshlanadi)")

    args = p.parse_args()

    if args.reset_rotation:
        db.init(config.DB_PATH)
        db.set_state(config.DB_PATH, LAST_INDEX_KEY, "-1")
        db.set_state(config.DB_PATH, LAST_POST_KEY, "1970-01-01T00:00:00")
        print("[i] Rotation tiklandi, keyingi post — birinchi manbadan")
        return

    if args.rotate_once:
        rotation_tick(dry_run=args.dry_run)
        return

    if args.rotate:
        run_rotation_loop(dry_run=args.dry_run)
        return

    if args.once or args.dry_run:
        run_once(dry_run=args.dry_run, max_per_source=args.limit)
        return

    # default — agar rejim ko'rsatilmagan bo'lsa, rotation loop
    run_rotation_loop(dry_run=False)


if __name__ == "__main__":
    main()
