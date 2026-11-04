# 📣 Материалы для публикации и раскрутки

Всё готово к копипасту. Заполняй сверху вниз — и публикуй.

---

## 1. Название

| Где | Значение |
|---|---|
| Продукт (в интерфейсе) | **Discord RSS Bot** |
| Репозиторий на GitHub | `Discord-RSS-Bot` → `https://github.com/Zver1o7/Discord-RSS-Bot` |
| Короткое (для тегов/постов) | RSS → Discord бот |

Альтернативы названия репо (если захочешь переименовать): `forum-rss-bot`, `rss-to-discord`, `discord-rss-feeds`.

## 2. Описание для GitHub (поле Description, макс. 350 символов)

**Основное (EN — лучше для международной аудитории):**

```
🤖 Discord RSS bot: any forum RSS → beautiful embed posts with images, keyword filters, custom templates & dark web admin panel. Python, discord.py, Flask. Self-hosted, 5-minute setup.
```

**Вариант на русском:**

```
🤖 Discord RSS-бот: любая RSS-лента форума → красивые embed-посты с картинками, фильтрами и веб-админкой в браузере. Python + discord.py + Flask. Самохостинг, настройка за 5 минут.
```

**Совсем короткий (для Telegram/соцсетей):**

```
Форум RSS → Discord. Красиво, с картинками, с админкой в браузере. Открытый код.
```

## 3. Topics (репозиторий → Settings → Topics → Edit)

Копируй по одному:

```
discord-bot
rss
rss-bot
python
discord
discord.py
flask
web-admin
forum
self-hosted
automation
open-source
embed
feed-reader
```

## 4. Social preview (картинка репозитория 1280×640)

1. Открой [`banner.svg`](banner.svg) в браузере (двойной клик).
2. Скриншот окна ровно **1280×640** (в DevTools: F12 → Toggle device toolbar → 1280×640 → screenshot), либо сконвертируй SVG → PNG любым онлайн-конвертером.
3. GitHub → репозиторий → **Settings → General → Social preview → Edit** → загрузи PNG.

## 5. Релиз v1.0.0

Код уже закоммичен, версия `1.0.0`. Пуш и релиз:

```bat
git remote add origin https://github.com/Zver1o7/Discord-RSS-Bot.git
git push -u origin main
```

Дальше: **Releases → Draft a new release** → Tag `v1.0.0` → Title `v1.0.0 — First public release` → в описание вставь блок из [CHANGELOG.md](../CHANGELOG.md) → **Publish release**.

Текст для release notes (EN, копипаст):

```markdown
First public release 🎉

- Any forum RSS → beautiful Discord embeds (image, author, date, link button)
- Custom message templates & keyword filters
- Dark web admin panel: add/preview/test feeds in the browser
- Slash commands: /rss-list, /rss-check
- No duplicate posts, first run never spams history
- Zero frontend build, single-file UI

Setup in 5 minutes — see README.
```

## 6. Где раскручивать — готовые тексты

### 🤖 Reddit (аудитория EN, самое горячее)

**r/discordbots** (флэр `Show-off` / `Self-promo` — читай правила саба перед постом):

```
Title: I built an open-source bot that turns any forum RSS into beautiful Discord embeds — with a web admin panel

Body:
Hey! Made a self-hosted Discord bot that polls any RSS feed (XenForo, phpBB, SMF, IPS, WordPress...) and posts new topics as clean embeds — image, author, date, link button, keyword filters, custom templates.

What makes it different:
- Dark web admin panel in the browser — add feeds, preview RSS before posting, test-post with one click. No config-file editing.
- No duplicate posts (seen.json), first run never spams the whole backlog
- Slash commands /rss-list and /rss-check
- Plain Python: discord.py + feedparser + Flask, ~700 lines, no frontend build

MIT licensed: https://github.com/Zver1o7/Discord-RSS-Bot

Would love feedback — especially on which forum engines people use, so I can add more RSS URL recipes.
```

**r/selfhosted:**

```
Title: Show-off: Discord RSS Bot — forum RSS to Discord with a web admin panel (self-hosted, MIT)

Body: short version + GitHub link + "runs on any VPS or Raspberry Pi, setup in 5 minutes".
```

**r/Python** (флэр `Project`): та же суть, акцент на коде: `feedparser`, `asyncio`, `tasks.loop`, Flask REST API, single-file HTML UI.

### 💬 Telegram

```
🤖 Открыл Discord RSS-бота — open source

Любая RSS-лента форума → красивые посты в Discord: картинка, автор, дата, кнопка «Читать».

Что внутри:
• веб-админка в браузере (тёмная тема)
• фильтры по словам, свой шаблон сообщения
• не спамит историей при первом запуске
• слэш-команды /rss-list, /rss-check

Python: discord.py + feedparser + Flask. MIT.
Настройка за 5 минут 👇
https://github.com/Zver1o7/Discord-RSS-Bot
```

### 🐦 X / Twitter (тред из 3 твитов)

```
1/3 🤖 New open-source project: Discord RSS Bot

Any forum RSS → beautiful Discord embeds (image, author, date, link button), keyword filters, custom templates.

+ dark web admin panel in your browser — add feeds, preview, test-post.

2/3 Built with Python: discord.py + feedparser + Flask. No database, no frontend build — config.json + seen.json and you're done.

No duplicate posts; first run never spams the backlog.

3/3 MIT,5-minute setup, works with XenForo / phpBB / SMF / IPS / WordPress feeds.

GitHub: https://github.com/Zver1o7/Discord-RSS-Bot

RT appreciated 🙏
```

### 📰 Habr (RU — отличный охват)

Заголовок: **«Делаю RSS-бота для Discord: форум → красивые посты и веб-админка на Flask»**

Лид (первый абзац):

> Захотел, чтобы новые темы с форума сами прилетали в Discord-канал красивыми постами — с картинкой, автором и ссылкой. Готовых ботов нашёл много, но либо они требуют правки JSON руками, либо выглядят как 2015 год. Сделал свой: парсинг RSS, фильтры, шаблоны и тёмная веб-админка, где всё настраивается кнопками. Рассказываю, как устроен, и выкладываю под MIT.

Тезисы статьи:
1. Почему feedparser, а не регулярки (и как вытаскивать картинку из enclosure / media / `<img>`)
2. Как не заспамить канал при первом запуске (`seen.json`, uid = md5 от guid/link)
3. REST API на Flask + один HTML-файл без сборки
4. Проблема «RSS закрыт гостям» на форумах и как её диагностировать
5. Слэш-команды и синхронизация (guild vs global)

Финал: ссылка на GitHub + «пишите в комментарии, какие движки форума используют вы — добавлю рецепты URL».

### 🎮 Discord (showcase-серверы / бот-листы)

Сообщение (EN):

```
Self-hosted RSS → Discord bot, now open source (MIT)

• Forum RSS feeds → clean embeds with image/author/date/button
• Web admin panel (preview + test-post, no config editing)
• Keyword filters, custom templates, /rss-list, /rss-check
• Python: discord.py + feedparser + Flask

https://github.com/Zver1o7/Discord-RSS-Bot
```

### 📋 Сервисы-каталоги (заявки)

- **top.gg** → Add your bot: Name `Discord RSS Bot`, description из п.2 (EN), tags: `utility`, `news`, `moderation` (проверь актуальный список), invite с правами Send Messages + Embed Links.
- **discords.com / discordbotlist.com** — то же описание + ссылка на GitHub.
- ⚠️ Для каталогов нужен бот **онлайн 24/7** — сначала подними его на VPS (см. INSTALL.md, раздел «Автозапуск»).

## 7. Чеклист перед публичным релизом

- [x] `config.json` и `data/` в `.gitignore` — токена в истории git нет
- [x] LICENSE (MIT) лежит
- [x] README.md (RU) + README.en.md (EN)
- [x] CHANGELOG.md с v1.0.0
- [x] Версия 1.0.0 в коде, бейджах и админке
- [ ] Сменить пароль админки `admin123` на свой (до раздачи ссылки!)
- [ ] Social preview 1280×640 (п.4)
- [ ] Topics (п.3)
- [ ] Push + Release v1.0.0 (п.5)
- [ ] Пост на Reddit → Telegram → Habr (п.6), с интервалом в пару дней, не всё разом

## 8. Пуш на GitHub (если ещё не залит)

Токен: https://github.com/settings/tokens/new → галочка **repo** → Generate.

```bat
cd D:\123\discord-rss-bot
git remote add origin https://Zver1o7:ТОКЕН@github.com/Zver1o7/Discord-RSS-Bot.git
git push -u origin main
```

После пуша удали токен на той же странице (Delete) — он больше не нужен.
