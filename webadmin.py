"""Веб-админка RSS-бота (Flask): настройка лент из браузера."""
from __future__ import annotations

import os
import threading
from functools import wraps

from flask import Flask, jsonify, request, send_from_directory

import rss_core as core

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")


def _check_auth() -> bool:
    cfg = core.load_config()
    pwd = str(cfg.get("web", {}).get("password", "") or "")
    if not pwd:
        return True  # пароль не задан — пускаем всех (локалка)
    token = request.headers.get("X-Admin-Token", "") or request.args.get("token", "")
    return token == pwd


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not _check_auth():
            return jsonify({"ok": False, "error": "unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper


def create_app() -> Flask:
    app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=None)

    @app.get("/")
    def index():
        return send_from_directory(TEMPLATES_DIR, "dashboard.html")

    @app.post("/api/login")
    def login():
        cfg = core.load_config()
        pwd = str(cfg.get("web", {}).get("password", "") or "")
        body = request.get_json(silent=True) or {}
        if not pwd or body.get("password") == pwd:
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Неверный пароль"}), 403

    @app.get("/api/status")
    @require_auth
    def status():
        cfg = core.load_config()
        try:
            import bot as botmod  # lazy, чтобы не тянуть discord в лёгких проверках
            b = botmod.bot_instance
            online = bool(b and getattr(b, "is_ready", lambda: False)())
            guilds = len(b.guilds) if b and online else 0
        except Exception:
            online, guilds = False, 0
        return jsonify({
            "ok": True,
            "version": core.__version__,
            "bot_online": online,
            "guilds": guilds,
            "uptime": core.STARTED_AT.isoformat(),
            "feeds_count": len(cfg.get("feeds", [])),
            "default_interval": cfg.get("default_interval", 300),
        })

    @app.get("/api/feeds")
    @require_auth
    def feeds_list():
        cfg = core.load_config()
        return jsonify({"ok": True, "feeds": cfg.get("feeds", [])})

    @app.post("/api/feeds")
    @require_auth
    def feeds_add():
        body = request.get_json(silent=True) or {}
        url = str(body.get("rss_url", "") or "").strip()
        channel = str(body.get("channel_id", "") or "").strip()
        if not url.startswith(("http://", "https://")):
            return jsonify({"ok": False, "error": "Некорректный RSS URL"}), 400
        if not channel.isdigit():
            return jsonify({"ok": False, "error": "channel_id должен быть ID канала (цифры)"}), 400
        cfg = core.load_config()
        feed = core.default_feed(url, channel, str(body.get("name", "") or "").strip())
        for k in ("enabled", "interval_sec", "color", "template", "use_embed",
                  "show_image", "show_author", "mention", "include_keywords",
                  "exclude_keywords", "max_posts"):
            if k in body:
                feed[k] = body[k]
        # id уникален
        base = feed["id"]
        i = 1
        while core.get_feed(cfg, feed["id"]):
            i += 1
            feed["id"] = f"{base}_{i}"
        cfg["feeds"].append(feed)
        core.save_config(cfg)
        core.log_event("INFO", f"Лента добавлена: {feed['name']}", feed["id"])
        return jsonify({"ok": True, "feed": feed})

    @app.put("/api/feeds/<feed_id>")
    @require_auth
    def feeds_update(feed_id: str):
        body = request.get_json(silent=True) or {}
        cfg = core.load_config()
        feed = core.get_feed(cfg, feed_id)
        if not feed:
            return jsonify({"ok": False, "error": "Лента не найдена"}), 404
        for k in ("name", "rss_url", "channel_id", "enabled", "interval_sec", "color",
                  "template", "use_embed", "show_image", "show_author", "mention",
                  "include_keywords", "exclude_keywords", "max_posts"):
            if k in body:
                feed[k] = body[k]
        core.save_config(cfg)
        core.log_event("INFO", f"Лента обновлена: {feed.get('name')}", feed_id)
        return jsonify({"ok": True, "feed": feed})

    @app.delete("/api/feeds/<feed_id>")
    @require_auth
    def feeds_delete(feed_id: str):
        cfg = core.load_config()
        before = len(cfg.get("feeds", []))
        cfg["feeds"] = [f for f in cfg.get("feeds", []) if str(f.get("id")) != str(feed_id)]
        if len(cfg["feeds"]) == before:
            return jsonify({"ok": False, "error": "Лента не найдена"}), 404
        core.save_config(cfg)
        core.log_event("INFO", "Лента удалена", feed_id)
        return jsonify({"ok": True})

    @app.get("/api/config")
    @require_auth
    def config_get():
        cfg = core.load_config()
        safe = {k: v for k, v in cfg.items() if k != "discord_token"}
        safe["has_token"] = bool(cfg.get("discord_token"))
        return jsonify({"ok": True, "config": safe})

    @app.put("/api/config")
    @require_auth
    def config_put():
        body = request.get_json(silent=True) or {}
        cfg = core.load_config()
        for k in ("guild_id", "default_interval", "max_summary_length"):
            if k in body:
                cfg[k] = body[k]
        if isinstance(body.get("web"), dict):
            cfg.setdefault("web", {}).update(body["web"])
        if body.get("discord_token"):
            cfg["discord_token"] = body["discord_token"]
        core.save_config(cfg)
        return jsonify({"ok": True})

    @app.get("/api/logs")
    @require_auth
    def logs():
        return jsonify({"ok": True, "logs": core.recent_logs(150)})

    @app.post("/api/feeds/<feed_id>/preview")
    @require_auth
    def preview(feed_id: str):
        """Прочитать ленту без публикации — для проверки URL/фильтров."""
        cfg = core.load_config()
        feed = core.get_feed(cfg, feed_id)
        if not feed:
            return jsonify({"ok": False, "error": "Лента не найдена"}), 404
        max_len = int(cfg.get("max_summary_length", 300) or 300)
        items, err = core.fetch_feed_items(feed.get("rss_url", ""), feed.get("name", ""), max_len, 8)
        shown = []
        for it in items:
            ok = core.match_filters(it, feed.get("include_keywords", ""), feed.get("exclude_keywords", ""))
            shown.append({**it, "passes_filter": ok,
                          "rendered": core.render_template(feed.get("template", ""), it)})
        return jsonify({"ok": True, "items": shown, "warning": err})

    @app.post("/api/feeds/<feed_id>/test")
    @require_auth
    def test_post(feed_id: str):
        """Опубликовать свежую запись в Discord (нужен запущенный бот)."""
        import asyncio
        cfg = core.load_config()
        feed = core.get_feed(cfg, feed_id)
        if not feed:
            return jsonify({"ok": False, "error": "Лента не найдена"}), 404
        try:
            import bot as botmod
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": f"bot недоступен: {exc}"}), 500
        b = botmod.bot_instance
        if not b or not getattr(b, "is_ready", lambda: False)():
            return jsonify({"ok": False, "error": "Бот не онлайн. Запусти bot.py"}), 409
        max_len = int(cfg.get("max_summary_length", 300) or 300)
        items, err = core.fetch_feed_items(feed.get("rss_url", ""), feed.get("name", ""), max_len, 3)
        if not items:
            return jsonify({"ok": False, "error": err or "Лента пустая"}), 502
        item = items[0]
        ok = asyncio.run_coroutine_threadsafe(botmod.post_item(b, feed, item, "test"), b.loop).result(timeout=30)
        if ok:
            return jsonify({"ok": True, "posted": item["title"]})
        return jsonify({"ok": False, "error": "Не удалось отправить (смотри логи)"}), 500

    return app


def run_in_thread(port: int = 0) -> threading.Thread:
    cfg = core.load_config()
    port = port or int(cfg.get("web", {}).get("port", 8000) or 8000)

    def _run():
        app = create_app()
        # use_reloader=False — мы уже в потоке
        app.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)

    t = threading.Thread(target=_run, name="webadmin", daemon=True)
    t.start()
    core.log_event("INFO", f"Веб-админка: http://127.0.0.1:{port}")
    return t


def main() -> None:
    """Запуск только админки без Discord (для настройки)."""
    cfg = core.load_config()
    port = int(cfg.get("web", {}).get("port", 8000) or 8000)
    print(f"🌐 Админка: http://127.0.0.1:{port}")
    create_app().run(host="127.0.0.1", port=port, threaded=True)


if __name__ == "__main__":
    main()
