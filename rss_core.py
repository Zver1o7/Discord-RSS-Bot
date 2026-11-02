"""Общая логика RSS-бота: конфиг, состояние, парсинг лент, фильтры, шаблоны."""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
DATA_DIR = os.path.join(BASE_DIR, "data")
SEEN_PATH = os.path.join(DATA_DIR, "seen.json")
LOG_PATH = os.path.join(DATA_DIR, "bot.log")

_lock = threading.Lock()
LOGS: deque[dict] = deque(maxlen=300)
STARTED_AT = datetime.now(timezone.utc)

DEFAULT_CONFIG: dict[str, Any] = {
    "discord_token": "",
    "guild_id": None,
    "default_interval": 300,
    "max_summary_length": 300,
    "web": {"enabled": True, "port": 8000, "password": "admin123"},
    "feeds": [],
}

TEMPLATE_VARS = ("{title}", "{link}", "{author}", "{summary}", "{date}", "{feed_name}", "{tags}")


# ---------- config ----------

def ensure_dirs() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def load_config() -> dict[str, Any]:
    ensure_dirs()
    if not os.path.exists(CONFIG_PATH):
        return json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return json.loads(json.dumps(DEFAULT_CONFIG))
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    cfg.update(data if isinstance(data, dict) else {})
    if "web" not in cfg or not isinstance(cfg["web"], dict):
        cfg["web"] = dict(DEFAULT_CONFIG["web"])
    if "feeds" not in cfg or not isinstance(cfg["feeds"], list):
        cfg["feeds"] = []
    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONFIG_PATH)


def get_feed(cfg: dict, feed_id: str) -> dict | None:
    for feed in cfg.get("feeds", []):
        if str(feed.get("id")) == str(feed_id):
            return feed
    return None


def new_feed_id(url: str) -> str:
    digest = hashlib.md5(url.encode("utf-8", "ignore")).hexdigest()[:8]
    return f"feed_{digest}"


# ---------- state (already posted) ----------

def load_seen() -> dict[str, list[str]]:
    ensure_dirs()
    try:
        with open(SEEN_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_seen(seen: dict[str, list[str]]) -> None:
    ensure_dirs()
    tmp = SEEN_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)
    os.replace(tmp, SEEN_PATH)


def entry_uid(entry: dict) -> str:
    for key in ("id", "guid", "link", "title"):
        val = str(entry.get(key, "") or "").strip()
        if val:
            return hashlib.md5(val.encode("utf-8", "ignore")).hexdigest()
    raw = json.dumps(entry, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode("utf-8", "ignore")).hexdigest()


# ---------- logs ----------

def log_event(level: str, msg: str, feed_id: str = "") -> None:
    rec = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "level": level,
        "feed": feed_id,
        "msg": msg,
    }
    with _lock:
        LOGS.append(rec)
    ensure_dirs()
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{rec['time']} [{level}] {feed_id} {msg}\n")
    except OSError:
        pass


def recent_logs(limit: int = 100) -> list[dict]:
    with _lock:
        return list(LOGS)[-limit:]


# ---------- parsing helpers (no discord dependency) ----------

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)


def clean_html(raw: str) -> str:
    if not raw:
        return ""
    text = html.unescape(raw)
    # bs4 если есть — аккуратнее, иначе regex
    try:
        from bs4 import BeautifulSoup  # type: ignore
        text = BeautifulSoup(text, "html.parser").get_text(" ")
    except Exception:
        text = TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = WS_RE.sub(" ", text).strip()
    return text


def truncate(text: str, limit: int) -> str:
    text = (text or "").strip()
    if limit <= 0 or len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0] or text[:limit]
    return cut.rstrip() + "…"


def extract_image(entry: dict, raw_html: str = "") -> str:
    # 1. enclosures
    for enc in entry.get("enclosures", []) or []:
        href = enc.get("href", "") or enc.get("url", "")
        typ = (enc.get("type", "") or "").lower()
        if href and (typ.startswith("image") or href.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))):
            return href
    # 2. media_content / media_thumbnail (feedparser)
    for key in ("media_content", "media_thumbnail"):
        for m in entry.get(key, []) or []:
            u = m.get("url", "")
            if u:
                return u
    # 3. первый <img> в summary/content
    for html_field in (raw_html, entry.get("summary", ""), entry.get("description", "")):
        if not html_field:
            continue
        m = IMG_RE.search(html_field)
        if m:
            return m.group(1)
    # 4. contents
    for c in entry.get("content", []) or []:
        v = c.get("value", "") if isinstance(c, dict) else ""
        m = IMG_RE.search(v or "")
        if m:
            return m.group(1)
    return ""


def normalize_entry(raw: Any, feed_name: str = "", max_len: int = 300) -> dict:
    """Приводит запись feedparser к плоскому dict для embed/шаблона."""
    get = lambda k, d="": raw.get(k, d) if isinstance(raw, dict) else d  # noqa: E731
    title = clean_html(str(get("title", "Без названия")))
    link = str(get("link", "")).strip()
    author = str(get("author", "") or get("author_detail", "")).strip()
    try:
        ad = get("author_detail", "")
        if isinstance(ad, dict) and ad.get("name"):
            author = str(ad.get("name", author))
    except Exception:
        pass

    summary_html = ""
    content = get("content", [])
    if content and isinstance(content, list) and isinstance(content[0], dict):
        summary_html = content[0].get("value", "")
    if not summary_html:
        summary_html = str(get("summary", "") or get("description", "") or "")

    summary = truncate(clean_html(summary_html), max_len)
    image = extract_image(raw if isinstance(raw, dict) else {}, summary_html)

    published = ""
    for k in ("published", "updated"):
        if get(k):
            published = str(get(k))
            break
    tags = ""
    try:
        t = get("tags", [])
        if isinstance(t, list):
            terms = [x.get("term", "") for x in t if isinstance(x, dict) and x.get("term")]
            tags = ", ".join(terms[:5])
    except Exception:
        tags = ""

    return {
        "uid": entry_uid({"id": get("id", ""), "guid": get("guid", ""), "link": link, "title": title}),
        "title": title[:256] or "Без названия",
        "link": link,
        "author": author[:100],
        "summary": summary,
        "image": image,
        "date": published,
        "tags": tags,
        "feed_name": feed_name,
    }


def fetch_feed_items(rss_url: str, feed_name: str = "", max_len: int = 300, limit: int = 10) -> tuple[list[dict], str]:
    """Скачивает ленту, возвращает (items, error). Без дискорда — можно вызывать из веба."""
    try:
        import feedparser  # type: ignore
    except ImportError:
        return [], "feedparser не установлен (pip install -r requirements.txt)"
    try:
        parsed = feedparser.parse(rss_url)
    except Exception as exc:  # noqa: BLE001
        return [], f"Ошибка загрузки: {exc}"
    if getattr(parsed, "bozo", False):
        err = str(getattr(parsed, "bozo_exception", "")) or "некорректный RSS"
        # если записи всё же есть — отдаём их, но с предупреждением
        entries = list(getattr(parsed, "entries", []) or [])
        if not entries:
            return [], f"RSS не распарсился: {err}"
        items = [normalize_entry(e, feed_name, max_len) for e in entries[:limit]]
        return items, f"Предупреждение: {err}"
    entries = list(getattr(parsed, "entries", []) or [])
    items = [normalize_entry(e, feed_name, max_len) for e in entries[:limit]]
    return items, ""


def match_filters(item: dict, include: str, exclude: str) -> bool:
    """True — запись проходит фильтры. Ключевики через запятую, поиск по title+summary."""
    text = f"{item.get('title','')} {item.get('summary','')}".lower()
    inc = [w.strip().lower() for w in (include or "").split(",") if w.strip()]
    exc = [w.strip().lower() for w in (exclude or "").split(",") if w.strip()]
    if exc and any(w in text for w in exc):
        return False
    if inc and not any(w in text for w in inc):
        return False
    return True


def render_template(template: str, item: dict) -> str:
    out = template or "📰 **{title}**\n{link}"
    mapping = {
        "{title}": item.get("title", ""),
        "{link}": item.get("link", ""),
        "{author}": item.get("author", ""),
        "{summary}": item.get("summary", ""),
        "{date}": item.get("date", ""),
        "{feed_name}": item.get("feed_name", ""),
        "{tags}": item.get("tags", ""),
    }
    for k, v in mapping.items():
        out = out.replace(k, str(v))
    return out.strip()


def default_feed(url: str, channel_id: str, name: str = "") -> dict:
    return {
        "id": new_feed_id(url + "|" + channel_id),
        "name": name or url[:40],
        "rss_url": url,
        "channel_id": str(channel_id),
        "enabled": True,
        "interval_sec": 0,
        "color": "#5865F2",
        "template": "📰 **{title}**\n👤 {author} · 🕒 {date}\n\n{summary}\n\n🔗 {link}",
        "use_embed": True,
        "show_image": True,
        "show_author": True,
        "mention": "",
        "include_keywords": "",
        "exclude_keywords": "",
        "max_posts": 3,
    }
