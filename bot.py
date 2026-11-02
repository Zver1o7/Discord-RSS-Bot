"""Discord RSS-бот: опрос лент форума и красивая публикация в каналы."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

import rss_core as core

log = logging.getLogger("rssbot")
logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", level=logging.INFO)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
bot_instance: commands.Bot | None = None
_last_check: dict[str, str] = {}
_next_run: dict[str, float] = {}


def hex_to_int(value: str, default: int = 0x5865F2) -> int:
    try:
        v = str(value or "").strip().lstrip("#")
        return int(v, 16)
    except (ValueError, TypeError):
        return default


def build_embed(feed: dict, item: dict) -> discord.Embed:
    emb = discord.Embed(
        title=item["title"][:256],
        url=item["link"] or None,
        description=item["summary"][:4096] or None,
        color=hex_to_int(feed.get("color", "#5865F2")),
        timestamp=datetime.now(timezone.utc),
    )
    if feed.get("show_author", True) and item.get("author"):
        emb.set_author(name=item["author"][:256])
    if feed.get("show_image", True) and item.get("image"):
        emb.set_image(url=item["image"])
    footer = feed.get("name", "") or "RSS"
    if item.get("date"):
        footer += f" · {item['date'][:50]}"
    emb.set_footer(text=footer[:2048])
    return emb


def build_view(item: dict) -> discord.ui.View | None:
    if not item.get("link"):
        return None
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="📖 Читать на форуме", url=item["link"], style=discord.ButtonStyle.link))
    return view


async def post_item(bot: commands.Bot, feed: dict, item: dict, reason: str = "new") -> bool:
    channel_id = str(feed.get("channel_id", "")).strip()
    if not channel_id.isdigit():
        core.log_event("ERROR", f"Некорректный channel_id: {channel_id}", str(feed.get("id")))
        return False
    channel = bot.get_channel(int(channel_id))
    if channel is None:
        try:
            channel = await bot.fetch_channel(int(channel_id))
        except Exception as exc:  # noqa: BLE001
            core.log_event("ERROR", f"Канал {channel_id} недоступен: {exc}", str(feed.get("id")))
            return False
    try:
        mention = str(feed.get("mention", "") or "").strip()
        content = core.render_template(feed.get("template", ""), item)
        # embed-режим: короткий текст + embed
        if feed.get("use_embed", True):
            embed = build_embed(feed, item)
            view = build_view(item)
            prefix = f"{mention}\n" if mention else ""
            # если шаблон кастомный и короткий — шлём его как content, иначе только mention
            text = prefix + (content if len(content) < 1500 else (mention or ""))
            # чтобы не дублировать ссылку дважды: если embed есть, content можно ужать
            if len(content) >= 1500:
                text = prefix.strip() or None
            await channel.send(content=text or None, embed=embed, view=view)  # type: ignore[arg-type]
        else:
            text = (f"{mention}\n" if mention else "") + content
            await channel.send(text[:2000] or item.get("link"))
        core.log_event("INFO", f"Опубликовано ({reason}): {item['title'][:80]}", str(feed.get("id")))
        return True
    except Exception as exc:  # noqa: BLE001
        core.log_event("ERROR", f"Не удалось отправить: {exc}", str(feed.get("id")))
        return False


async def check_feed(bot: commands.Bot, feed: dict, *, first_run: bool = False, force_post: bool = False) -> int:
    """Проверяет одну ленту. Возвращает число опубликованных."""
    fid = str(feed.get("id"))
    if not feed.get("enabled", True):
        return 0
    cfg = core.load_config()
    max_len = int(cfg.get("max_summary_length", 300) or 300)
    items, err = await asyncio.to_thread(
        core.fetch_feed_items, feed.get("rss_url", ""), feed.get("name", ""), max_len, 15
    )
    _last_check[fid] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if err and not items:
        core.log_event("ERROR", f"RSS ошибка: {err}", fid)
        return 0
    if err:
        core.log_event("WARN", err, fid)

    seen = core.load_seen()
    known = set(seen.get(fid, []))
    if first_run and not known and items:
        # при первом запуске помечаем всё как виденное, чтобы не спамить историей
        seen[fid] = [i["uid"] for i in items][:200]
        core.save_seen(seen)
        core.log_event("INFO", f"Первый запуск: запомнено {len(items)} записей без публикации", fid)
        return 0

    fresh: list[dict] = []
    for it in items:
        if it["uid"] in known:
            continue
        if not core.match_filters(it, feed.get("include_keywords", ""), feed.get("exclude_keywords", "")):
            known.add(it["uid"])
            continue
        fresh.append(it)
    # RSS отдаёт от новых к старым — постим снизу вверх чтобы порядок сохранился
    fresh = fresh[::-1][: int(feed.get("max_posts", 3) or 3)]

    posted = 0
    for it in fresh:
        if force_post or not first_run:
            ok = await post_item(bot, feed, it)
            if ok:
                posted += 1
        known.add(it["uid"])
    seen[fid] = list(known)[-200:]
    core.save_seen(seen)
    if fresh and posted == 0 and not first_run:
        core.log_event("INFO", f"Нового нет / отфильтровано ({len(fresh)} пропущено)", fid)
    return posted


class RSSBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.poll_loop_started = False

    async def setup_hook(self) -> None:
        self._poll.add_exception_type(Exception)
        if not self._poll.is_running():
            self._poll.start()

    @tasks.loop(seconds=30)
    async def _poll(self) -> None:
        cfg = core.load_config()
        default_iv = int(cfg.get("default_interval", 300) or 300)
        now = asyncio.get_event_loop().time()
        for feed in cfg.get("feeds", []):
            fid = str(feed.get("id"))
            iv = int(feed.get("interval_sec", 0) or 0) or default_iv
            iv = max(60, iv)
            last = _next_run.get(fid, 0)
            if now < last:
                continue
            _next_run[fid] = now + iv
            try:
                await check_feed(self, feed)
            except Exception as exc:  # noqa: BLE001
                core.log_event("ERROR", f"check_feed упал: {exc}", fid)

    @_poll.before_loop
    async def _before_poll(self) -> None:
        await self.wait_until_ready()
        # первый проход — запомнить без спама
        cfg = core.load_config()
        default_iv = int(cfg.get("default_interval", 300) or 300)
        now = asyncio.get_event_loop().time()
        for feed in cfg.get("feeds", []):
            fid = str(feed.get("id"))
            iv = int(feed.get("interval_sec", 0) or 0) or default_iv
            _next_run[fid] = now + max(60, iv)
            try:
                await check_feed(self, feed, first_run=True)
            except Exception as exc:  # noqa: BLE001
                core.log_event("ERROR", f"first_run упал: {exc}", fid)

    async def on_ready(self) -> None:
        log.info("RSS-бот запущен как %s (серверов: %d)", self.user, len(self.guilds))
        core.log_event("INFO", f"Бот онлайн: {self.user} (серверов: {len(self.guilds)})")
        cfg = core.load_config()
        gid = str(cfg.get("guild_id") or "").strip()
        try:
            if gid and gid.isdigit():
                await self.tree.sync(guild=discord.Object(id=int(gid)))
                log.info("Слэш-команды синхронизированы для сервера %s", gid)
            else:
                await self.tree.sync()
        except Exception as exc:  # noqa: BLE001
            log.warning("Не удалось синхронизировать команды: %s", exc)


def build_bot() -> RSSBot:
    bot = RSSBot()
    global bot_instance
    bot_instance = bot

    @bot.tree.command(name="rss-list", description="Показать все RSS-ленты")
    async def rss_list(inter: discord.Interaction) -> None:
        cfg = core.load_config()
        feeds = cfg.get("feeds", [])
        if not feeds:
            await inter.response.send_message("📭 Ленты не настроены. Добавь их в веб-админке.", ephemeral=True)
            return
        lines = []
        for f in feeds:
            status = "🟢" if f.get("enabled") else "⚪"
            lines.append(f"{status} `{f.get('id')}` **{f.get('name')}** → <#{f.get('channel_id')}>")
        await inter.response.send_message("\n".join(lines)[:1900], ephemeral=True)

    @bot.tree.command(name="rss-check", description="Принудительно проверить ленту сейчас")
    @app_commands.describe(feed_id="ID ленты (смотри /rss-list)")
    async def rss_check(inter: discord.Interaction, feed_id: str) -> None:
        if not inter.user.guild_permissions.manage_guild:
            await inter.response.send_message("⛔ Нужны права «Управление сервером».", ephemeral=True)
            return
        cfg = core.load_config()
        feed = core.get_feed(cfg, feed_id)
        if not feed:
            await inter.response.send_message("❌ Лента не найдена.", ephemeral=True)
            return
        await inter.response.defer(ephemeral=True)
        n = await check_feed(bot, feed)
        await inter.followup.send(f"✅ Проверка готова. Опубликовано: **{n}**.", ephemeral=True)

    return bot


def load_token() -> str:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if token:
        return token
    cfg = core.load_config()
    token = str(cfg.get("discord_token", "") or "").strip()
    if token:
        return token
    raise SystemExit(
        "❌ Нет токена Discord.\n"
        "  1) Создай config.json из config.example.json и впиши discord_token,\n"
        "  2) или задай переменную окружения DISCORD_TOKEN.\n"
        "Токен берётся на https://discord.com/developers/applications → Bot → Token."
    )


def main(run_web: bool = True) -> None:
    cfg = core.load_config()
    if run_web and cfg.get("web", {}).get("enabled", True):
        try:
            from webadmin import run_in_thread  # lazy import
            run_in_thread()
        except Exception as exc:  # noqa: BLE001
            log.warning("Веб-админка не стартовала: %s", exc)
    bot = build_bot()
    bot.run(load_token())


if __name__ == "__main__":
    main()
