# newsai

O'zbek tilidagi avtomatik yangiliklar bot — RSS manbalardan yangiliklarni olib, Gemini orqali o'zbek tiliga tarjima qilib, Telegram kanalga rotation rejimida joylab beradi.

## Manbalar

- Kun.uz, Gazeta.uz (uz)
- Spot.uz, Championat (ru → uz)
- BBC World, Al Jazeera (en → uz)

`config.py` → `SOURCES` ro'yxatini tahrirlab manbalar qo'shish/olib tashlash mumkin.

## Lokal ishga tushirish

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env
# .env ichiga TELEGRAM_BOT_TOKEN, GEMINI_API_KEY yozing

# Test (Telegramga yubormay)
.venv/bin/python main.py --dry-run --limit 2

# Bitta yangilik (rotation tartibida keyingi manbadan)
.venv/bin/python main.py --rotate-once

# Davomiy ishlatish: har POST_INTERVAL_MINUTES daqiqada
.venv/bin/python main.py --rotate
```

## Docker

```bash
docker compose up -d --build
docker compose logs -f
```

## Server (Hetzner) — birinchi marta sozlash

1. **Server'ga SSH bilan kiring** va papka yarating:
   ```bash
   ssh user@your-server
   sudo mkdir -p /opt/newsai/data
   sudo chown $USER:$USER /opt/newsai
   cd /opt/newsai
   ```

2. **`.env` faylini yarating** (faqat serverda, repo'ga emas):
   ```bash
   cat > .env <<'EOF'
   TELEGRAM_BOT_TOKEN=...yangi_token...
   TELEGRAM_CHANNEL=@realyangilik
   GEMINI_API_KEY=...yangi_key...
   POST_INTERVAL_MINUTES=35
   DB_PATH=/data/news.db
   EOF
   chmod 600 .env
   ```

3. **`docker-compose.yml`** ni serverga ko'chiring:
   ```bash
   curl -L https://raw.githubusercontent.com/Shahzod1602/news/main/docker-compose.yml -o docker-compose.yml
   ```

4. **GHCR'ga login** (private image bo'lsa):
   ```bash
   echo $GHCR_PAT | docker login ghcr.io -u Shahzod1602 --password-stdin
   ```

5. **Birinchi marta ishga tushirish**:
   ```bash
   docker compose pull
   docker compose up -d
   docker compose logs -f
   ```

## CI/CD

Har `main` branch'ga push:
1. GitHub Actions Docker image quradi va `ghcr.io/shahzod1602/news:latest` ga yuklaydi
2. Server'ga SSH qilib, `docker compose pull && docker compose up -d` bajaradi

### GitHub Secrets (Settings → Secrets and variables → Actions)

| Nom | Qiymat |
|---|---|
| `SSH_HOST` | Hetzner server IP yoki domen |
| `SSH_USER` | SSH foydalanuvchi nomi (masalan `root` yoki `deploy`) |
| `SSH_PORT` | SSH port (default 22) |
| `SSH_KEY` | Private SSH key (server'ga ulanish uchun) |
| `GHCR_PAT` | GitHub Personal Access Token (`read:packages` scope bilan) |

### SSH key sozlash

Lokalda yangi keypair yarating:
```bash
ssh-keygen -t ed25519 -C "newsai-deploy" -f ~/.ssh/newsai_deploy -N ""
```

- `~/.ssh/newsai_deploy.pub` — server'da `~/.ssh/authorized_keys` ga qo'shing
- `~/.ssh/newsai_deploy` (private) — GitHub Secret `SSH_KEY` ga qo'ying

### GHCR PAT yaratish

1. https://github.com/settings/tokens/new
2. Scope: `read:packages` (image pull uchun)
3. Yaratilgan tokenni `GHCR_PAT` secret'iga qo'ying

## Buyruqlar

| Buyruq | Vazifa |
|---|---|
| `--rotate` | Davomiy: har 35 daq 1 yangilik (default rejim) |
| `--rotate-once` | 1 marta navbatdagi manbadan yuborish |
| `--once --limit N` | Bir martaga hamma manbalardan N tadan |
| `--dry-run` | Yubormay, ekranda ko'rsatish |
| `--reset-rotation` | Rotation indeksini Kun.uz dan boshlash |

## Konfiguratsiya (`.env`)

| O'zgaruvchi | Default | Tavsif |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | @BotFather dan token |
| `TELEGRAM_CHANNEL` | `@realyangilik` | Kanal username |
| `GEMINI_API_KEY` | — | Google AI Studio key |
| `POST_INTERVAL_MINUTES` | `35` | Postlar orasidagi vaqt |
| `DB_PATH` | `news.db` | SQLite fayl yo'li |

## Manbalar qo'shish/o'zgartirish

`config.py`:
```python
SOURCES = [
    ("Nom", "RSS_URL", "til (uz/ru/en)", "#hashtag"),
    ...
]
```

O'zgarish kiritgandan keyin `git push` qilsangiz — CI/CD avtomatik deploy qiladi.
