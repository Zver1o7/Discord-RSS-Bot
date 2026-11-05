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

BANNER = (
    "╔══════════════════════════════════════════════════════════╗\n"
    "║                DISCORD RSS BOT v{ver}                   ║\n"
    "║                by {author} • {repo}                      ║\n"
    "╚══════════════════════════════════════════════════════════╝"
)

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
    ts = datetime.now(timezone.utc) if feed.get("show_timestamp", True) else None
    emb = discord.Embed(
        title=item["title"][:256],
        url=item["link"] or None,
        description=item["summary"][:4096] or None,
        color=hex_to_int(feed.get("color", "#5865F2")),
        timestamp=ts,
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
    webhook_url = str(feed.get("webhook_url", "") or "").strip()
    thread_id = str(feed.get("thread_id", "") or "").strip()
    channel_id = str(feed.get("channel_id", "")).strip()

    mention = str(feed.get("mention", "") or "").strip()
    content = core.render_template(feed.get("template", ""), item)
    use_embed = feed.get("use_embed", True)

    # подготовка контента
    embed = build_embed(feed, item) if use_embed else None
    view = build_view(item)
    if use_embed:
        prefix = f"{mention}\n" if mention else ""
        text = prefix + (content if len(content) < 1500 else (mention or ""))
        if len(content) >= 1500:
            text = prefix.strip() or None
        send_kwargs = {"content": text or None, "embed": embed, "view": view}
    else:
        send_kwargs = {"content": ((f"{mention}\n" if mention else "") + content)[:2000] or item.get("link")}

    # 1) Вебхук
    if webhook_url.startswith(("http://", "https://")):
        try:
            wh = discord.Webhook.from_url(webhook_url, client=bot)
            kwargs = dict(send_kwargs)
            if thread_id.isdigit():
                kwargs["thread"] = discord.Object(id=int(thread_id))
            await wh.send(wait=True, **kwargs)
            core.log_event("INFO", f"Опубликовано webhook ({reason}): {item['title'][:80]}", str(feed.get("id")))
            try:
                core.inc_stat("posts")
                core.set_feed_meta(str(feed.get("id","")), last_post=datetime.now(timezone.utc).isoformat(timespec="seconds"))
            except Exception:
                pass
            return True
        except Exception as exc:  # noqa: BLE001
            core.log_event("ERROR", f"Webhook ошибка: {exc}", str(feed.get("id")))
            return False

    # 2) Обычный канал/ветка
    target_id = thread_id if thread_id.isdigit() else channel_id
    if not target_id.isdigit():
        core.log_event("ERROR", f"Некорректный channel_id/thread_id: {channel_id}/{thread_id}", str(feed.get("id")))
        return False
    channel = bot.get_channel(int(target_id))
    if channel is None:
        try:
            channel = await bot.fetch_channel(int(target_id))
        except Exception as exc:  # noqa: BLE001
            core.log_event("ERROR", f"Канал {target_id} недоступен: {exc}", str(feed.get("id")))
            return False
    try:
        await channel.send(**send_kwargs)  # type: ignore[arg-type]
        core.log_event("INFO", f"Опубликовано ({reason}): {item['title'][:80]}", str(feed.get("id")))
        try:
            core.inc_stat("posts")
        except Exception:
            pass
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
    try:
        core.set_feed_meta(fid, last_check=_last_check[fid])
    except Exception:
        pass
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
        print(BANNER.format(ver=core.__version__, author=core.__author__, repo=core.__github__))
        log.info("Discord RSS Bot v%s — запущен как %s (серверов: %d)", core.__version__, self.user, len(self.guilds))
        log.info("Автор: %s | %s", core.__author__, core.__github__)
        core.log_event("INFO", f"Бот онлайн: {self.user} (серверов: {len(self.guilds)}) | by {core.__author__}")
        try:
            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"RSS | v{core.__version__} | by {core.__author__}"))
        except Exception:
            pass
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

    async def feed_id_autocomplete(inter: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        cfg = core.load_config()
        cur = (current or "").lower()
        choices = []
        for f in cfg.get("feeds", [])[:25]:
            fid = str(f.get("id", ""))
            name = str(f.get("name", ""))
            label = f"{name} ({fid})"[:100]
            if cur in fid.lower() or cur in name.lower():
                choices.append(app_commands.Choice(name=label, value=fid))
            if len(choices) >= 25:
                break
        return choices

    @bot.tree.command(name="about", description="О боте: автор, версия, ссылки")
    async def about_cmd(inter: discord.Interaction) -> None:
        try:
            stats = core.load_stats()
            posts = int(stats.get("posts", 0) or 0)
        except Exception:
            posts = 0
        try:
            from datetime import datetime, timezone
            up = (datetime.now(timezone.utc) - core.STARTED_AT).total_seconds()
            h, rem = divmod(int(up), 3600)
            m, s = divmod(rem, 60)
            uptime = f"{h}ч {m}м {s}с"
        except Exception:
            uptime = "—"
        emb = discord.Embed(
            title="🤖 Discord RSS Bot",
            description=(
                "Форум/сайт RSS → красивые embed-посты в Discord + веб-админка.\n\n"
                f"**Автор:** [{core.__author__}]({core.__author_url__})"
            ),
            color=0x5865F2,
            url=core.__github__,
        )
        emb.add_field(name="Версия", value=f"`v{core.__version__}`", inline=True)
        emb.add_field(name="Uptime", value=uptime, inline=True)
        emb.add_field(name="Опубликовано постов", value=f"`{posts}`", inline=True)
        emb.add_field(name="Репозиторий", value=f"[GitHub]({core.__github__})", inline=True)
        emb.add_field(name="Issues", value=f"[Сообщить об ошибке]({core.__github__}/issues)", inline=True)
        emb.add_field(name="Релизы", value=f"[Releases]({core.__github__}/releases)", inline=True)
        emb.set_footer(text=f"by {core.__author__} • {core.__github__}")
        await inter.response.send_message(embed=emb, ephemeral=True)

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
    @app_commands.autocomplete(feed_id=feed_id_autocomplete)
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

    @bot.tree.command(name="rss-info", description="Информация о ленте")
    @app_commands.describe(feed_id="ID ленты (смотри /rss-list)")
    @app_commands.autocomplete(feed_id=feed_id_autocomplete)
    async def rss_info(inter: discord.Interaction, feed_id: str) -> None:
        cfg = core.load_config()
        feed = core.get_feed(cfg, feed_id)
        if not feed:
            await inter.response.send_message("❌ Лента не найдена.", ephemeral=True)
            return
        enabled = "🟢 Включена" if feed.get("enabled", True) else "⚪ Выключена"
        iv = feed.get("interval_sec") or cfg.get("default_interval") or 300
        inc = feed.get("include_keywords") or "—"
        exc = feed.get("exclude_keywords") or "—"
        emb = discord.Embed(title=f"📡 {feed.get('name')}", color=0x5865F2)
        emb.add_field(name="ID", value=f"`{feed.get('id')}`", inline=True)
        emb.add_field(name="Статус", value=enabled, inline=True)
        emb.add_field(name="Канал", value=f"<#{feed.get('channel_id')}>", inline=True)
        emb.add_field(name="RSS", value=f"[Открыть]({feed.get('rss_url')})", inline=False)
        emb.add_field(name="Интервал", value=f"{iv} сек", inline=True)
        emb.add_field(name="Embed", value="Да" if feed.get("use_embed", True) else "Нет", inline=True)
        emb.add_field(name="Фильтр «включить»", value=inc, inline=False)
        emb.add_field(name="Фильтр «исключить»", value=exc, inline=False)
        emb.set_footer(text=f"by {core.__author__}")
        await inter.response.send_message(embed=emb, ephemeral=True)

    @bot.tree.command(name="rss-toggle", description="Включить/выключить ленту")
    @app_commands.describe(feed_id="ID ленты (смотри /rss-list)")
    @app_commands.autocomplete(feed_id=feed_id_autocomplete)
    async def rss_toggle(inter: discord.Interaction, feed_id: str) -> None:
        if not inter.user.guild_permissions.manage_guild:
            await inter.response.send_message("⛔ Нужны права «Управление сервером».", ephemeral=True)
            return
        cfg = core.load_config()
        feed = core.get_feed(cfg, feed_id)
        if not feed:
            await inter.response.send_message("❌ Лента не найдена.", ephemeral=True)
            return
        feed["enabled"] = not bool(feed.get("enabled", True))
        core.save_config(cfg)
        state = "включена" if feed["enabled"] else "выключена"
        await inter.response.send_message(f"✅ Лента **{feed.get('name')}** {state}.", ephemeral=True)
        core.log_event("INFO", f"Лента {state} через /rss-toggle", feed_id)

    @bot.tree.command(name="rss-test", description="Тестовый пост свежей записи из ленты")
    @app_commands.describe(feed_id="ID ленты (смотри /rss-list)")
    @app_commands.autocomplete(feed_id=feed_id_autocomplete)
    async def rss_test_cmd(inter: discord.Interaction, feed_id: str) -> None:
        if not inter.user.guild_permissions.manage_guild:
            await inter.response.send_message("⛔ Нужны права «Управление сервером».", ephemeral=True)
            return
        cfg = core.load_config()
        feed = core.get_feed(cfg, feed_id)
        if not feed:
            await inter.response.send_message("❌ Лента не найдена.", ephemeral=True)
            return
        await inter.response.defer(ephemeral=True)
        max_len = int(cfg.get("max_summary_length", 300) or 300)
        items, err = core.fetch_feed_items(feed.get("rss_url", ""), feed.get("name", ""), max_len, 3)
        if not items:
            await inter.followup.send(f"❌ Не удалось получить записи. {err or ''}", ephemeral=True)
            return
        item = items[0]
        ok = await post_item(bot, feed, item, reason="test")
        if ok:
            await inter.followup.send(f"✅ Тестовый пост отправлен: **{item['title'][:80]}**", ephemeral=True)
        else:
            await inter.followup.send("❌ Не удалось отправить пост. Проверь логи в веб-админке.", ephemeral=True)

    @bot.tree.command(name="rss-stats", description="Статистика бота")
    async def rss_stats(inter: discord.Interaction) -> None:
        cfg = core.load_config()
        feeds = cfg.get("feeds", [])
        active = sum(1 for f in feeds if f.get("enabled", True))
        try:
            stats = core.load_stats()
            posts = int(stats.get("posts", 0) or 0)
        except Exception:
            posts = 0
        try:
            up = (datetime.now(timezone.utc) - core.STARTED_AT).total_seconds()
            h, rem = divmod(int(up), 3600)
            m, s = divmod(rem, 60)
            uptime = f"{h}ч {m}м {s}с"
        except Exception:
            uptime = "—"
        emb = discord.Embed(title="📊 Статистика RSS Bot", color=0x5865F2)
        emb.add_field(name="Всего лент", value=f"`{len(feeds)}`", inline=True)
        emb.add_field(name="Активных", value=f"`{active}`", inline=True)
        emb.add_field(name="Опубликовано", value=f"`{posts}`", inline=True)
        emb.add_field(name="Серверов", value=f"`{len(bot.guilds)}`", inline=True)
        emb.add_field(name="Uptime", value=uptime, inline=True)
        emb.add_field(name="Версия", value=f"`v{core.__version__}`", inline=True)
        emb.set_footer(text=f"by {core.__author__}")
        await inter.response.send_message(embed=emb, ephemeral=True)

    @bot.tree.command(name="rss-ping", description="Проверить, что бот отвечает")
    async def rss_ping(inter: discord.Interaction) -> None:
        latency = round(bot.latency * 1000)
        await inter.response.send_message(f"🏓 Pong! `{latency} ms` · v{core.__version__}", ephemeral=True)

    @bot.tree.command(name="rss-reload", description="Перезагрузить конфиг без перезапуска")
    async def rss_reload(inter: discord.Interaction) -> None:
        if not inter.user.guild_permissions.manage_guild:
            await inter.response.send_message("⛔ Нужны права «Управление сервером».", ephemeral=True)
            return
        cfg = core.load_config()
        _next_run.clear()
        await inter.response.send_message(f"✅ Конфиг перечитан. Лент: **{len(cfg.get('feeds',[]))}**. Таймеры сброшены.", ephemeral=True)
        core.log_event("INFO", "Конфиг перезагружен через /rss-reload")

    @bot.tree.command(name="rss-reset", description="Сбросить историю ленты (повторная публикация новых записей)")
    @app_commands.describe(feed_id="ID ленты (смотри /rss-list)")
    @app_commands.autocomplete(feed_id=feed_id_autocomplete)
    async def rss_reset(inter: discord.Interaction, feed_id: str) -> None:
        if not inter.user.guild_permissions.manage_guild:
            await inter.response.send_message("⛔ Нужны права «Управление сервером».", ephemeral=True)
            return
        cfg = core.load_config()
        feed = core.get_feed(cfg, feed_id)
        if not feed:
            await inter.response.send_message("❌ Лента не найдена.", ephemeral=True)
            return
        seen = core.load_seen()
        seen[str(feed_id)] = []
        core.save_seen(seen)
        await inter.response.send_message(f"✅ История ленты **{feed.get('name')}** сброшена. Следующая проверка обработает записи как новые (с учётом первого запуска).", ephemeral=True)
        core.log_event("INFO", "История ленты сброшена", feed_id)

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
