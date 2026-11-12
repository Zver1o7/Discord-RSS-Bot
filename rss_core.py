"""Общая логика RSS-бота: конфиг, состояние, парсинг лент, фильтры, шаблоны."""
from __future__ import annotations

__version__ = "1.5.0"
__author__ = "Zver1o7"
__github__ = "https://github.com/Zver1o7/Discord-RSS-Bot"
__author_url__ = "https://github.com/Zver1o7"

import hashlib
import html
import json
import os
import re
import threading
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
DATA_DIR = os.path.join(BASE_DIR, "data")
SEEN_PATH = os.path.join(DATA_DIR, "seen.json")
LOG_PATH = os.path.join(DATA_DIR, "bot.log")
STATS_PATH = os.path.join(DATA_DIR, "stats.json")
HISTORY_PATH = os.path.join(DATA_DIR, "history.json")
DIGEST_PATH = os.path.join(DATA_DIR, "digest.json")

_lock = threading.Lock()
LOGS: deque[dict] = deque(maxlen=300)
STARTED_AT = datetime.now(timezone.utc)

DEFAULT_CONFIG: dict[str, Any] = {
    "discord_token": "",
    "guild_id": None,
    "default_interval": 300,
    "max_summary_length": 300,
    "quiet_hours": {"enabled": False, "start": 23, "end": 8},
    "alerts": {"channel_id": "", "after_failures": 3},
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
    if "alerts" not in cfg or not isinstance(cfg["alerts"], dict):
        cfg["alerts"] = dict(DEFAULT_CONFIG["alerts"])
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


def is_quiet_now(cfg: dict | None = None) -> bool:
    """True, если сейчас тихие часы (настройка quiet_hours)."""
    try:
        cfg = cfg or load_config()
        qh = cfg.get("quiet_hours") or {}
        if not qh.get("enabled"):
            return False
        start = int(qh.get("start", 23) or 23)
        end = int(qh.get("end", 8) or 8)
        hour = datetime.now().hour
        if start == end:
            return False
        if start > end:  # интервал через полночь
            return hour >= start or hour < end
        return start <= hour < end
    except Exception:
        return False


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


def recent_logs(limit: int = 100, query: str = "") -> list[dict]:
    with _lock:
        items = list(LOGS)
    if query:
        q = query.lower().strip()
        items = [r for r in items
                 if q in str(r.get("msg", "")).lower()
                 or q in str(r.get("feed", "")).lower()
                 or q in str(r.get("level", "")).lower()]
    return items[-limit:]


def load_stats() -> dict:
    ensure_dirs()
    try:
        with open(STATS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {"posts": 0, "checks": 0, "feeds": {}}


def save_stats(stats: dict) -> None:
    ensure_dirs()
    tmp = STATS_PATH + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        os.replace(tmp, STATS_PATH)
    except OSError:
        pass


def inc_stat(key: str, amount: int = 1) -> None:
    stats = load_stats()
    try:
        stats[key] = int(stats.get(key, 0) or 0) + amount
    except Exception:
        stats[key] = amount
    save_stats(stats)


def set_feed_meta(feed_id: str, **fields) -> None:
    stats = load_stats()
    feeds = stats.setdefault("feeds", {})
    meta = feeds.setdefault(str(feed_id), {})
    meta.update(fields)
    save_stats(stats)


def get_feed_meta(feed_id: str) -> dict:
    stats = load_stats()
    return (stats.get("feeds") or {}).get(str(feed_id), {})


# ---------- history (posts per day) ----------

def record_post_day(amount: int = 1) -> None:
    """Увеличивает счётчик публикаций за сегодня. Хранит 30 дней."""
    ensure_dirs()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            hist = json.load(f)
        if not isinstance(hist, dict):
            hist = {}
    except (OSError, json.JSONDecodeError):
        hist = {}
    hist[today] = int(hist.get(today, 0) or 0) + amount
    for key in sorted(hist.keys())[:-30]:
        hist.pop(key, None)
    try:
        tmp = HISTORY_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(hist, f, ensure_ascii=False)
        os.replace(tmp, HISTORY_PATH)
    except OSError:
        pass


def get_history(days: int = 7) -> list[dict]:
    """Список {date, posts} за последние N дней (сегодня последний)."""
    ensure_dirs()
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            hist = json.load(f)
        if not isinstance(hist, dict):
            hist = {}
    except (OSError, json.JSONDecodeError):
        hist = {}
    out = []
    for i in range(days - 1, -1, -1):
        day = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        out.append({"date": day, "posts": int(hist.get(day, 0) or 0)})
    return out


# ---------- digest queue ----------

def load_digest() -> dict:
    ensure_dirs()
    try:
        with open(DIGEST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_digest(data: dict) -> None:
    ensure_dirs()
    tmp = DIGEST_PATH + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DIGEST_PATH)
    except OSError:
        pass


def queue_digest(feed_id: str, items: list[dict], max_keep: int = 30) -> int:
    """Копит записи в очередь дайджеста. Возвращает размер очереди."""
    data = load_digest()
    entry = data.get(str(feed_id)) or {"items": [], "queued_at": None}
    have = {str(i.get("uid")) for i in entry.get("items", [])}
    for it in items:
        uid = str(it.get("uid") or it.get("link") or it.get("title"))
        if uid in have:
            continue
        entry["items"].append({
            "uid": uid,
            "title": it.get("title", ""),
            "link": it.get("link", ""),
            "image": it.get("image", ""),
            "summary": it.get("summary", ""),
            "author": it.get("author", ""),
            "date": it.get("date", ""),
        })
        have.add(uid)
    entry["items"] = entry["items"][-max_keep:]
    if not entry.get("queued_at"):
        entry["queued_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data[str(feed_id)] = entry
    save_digest(data)
    return len(entry["items"])


def get_digest(feed_id: str) -> dict:
    return load_digest().get(str(feed_id)) or {"items": [], "queued_at": None}


def clear_digest(feed_id: str) -> None:
    data = load_digest()
    if str(feed_id) in data:
        data.pop(str(feed_id), None)
        save_digest(data)


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


def match_filters(item: dict, include: str, exclude: str,
                  include_regex: str = "", exclude_regex: str = "") -> bool:
    """True — запись проходит фильтры. Ключевики через запятую, поиск по title+summary."""
    text = f"{item.get('title','')} {item.get('summary','')}".lower()
    inc = [w.strip().lower() for w in (include or "").split(",") if w.strip()]
    exc = [w.strip().lower() for w in (exclude or "").split(",") if w.strip()]
    if exc and any(w in text for w in exc):
        return False
    if inc and not any(w in text for w in inc):
        return False
    for pattern, mode in ((include_regex, "inc"), (exclude_regex, "exc")):
        if not pattern:
            continue
        try:
            hit = re.search(pattern, text, re.IGNORECASE)
        except re.error:
            continue  # некорректная регулярка — просто игнорируем
        if mode == "inc" and not hit:
            return False
        if mode == "exc" and hit:
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
        "show_timestamp": True,
        "mention": "",
        "include_keywords": "",
        "exclude_keywords": "",
        "max_posts": 3,
        "webhook_url": "",
        "thread_id": "",
        "post_mode": "instant",
        "digest_interval": 3600,
        "digest_max": 5,
        "include_regex": "",
        "exclude_regex": "",
    }
