<div align="center">

# 🤖 Discord RSS Bot

### Форум RSS → красивые посты в Discord + веб-админка в браузере

> 🇬🇧 **English version:** [README.en.md](README.en.md) · 📣 Для раскрутки: [docs/PROMO.md](docs/PROMO.md)

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.x-blurple?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Flask](https://img.shields.io/badge/flask-admin-black?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![Version](https://img.shields.io/badge/version-1.0.0-blue?style=for-the-badge)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)
[![RSS](https://img.shields.io/badge/RSS-forum-orange?style=for-the-badge&logo=rss&logoColor=white)](#поддерживаемые-форумы)

**Универсальный бот:** берёт любую RSS-ленту форума и постит новые темы в Discord красивым embed'ом — с картинкой, автором, датой и кнопкой «Читать на форуме». Всё настраивается из браузера, код править не нужно.

[🚀 Быстрый старт](#быстрый-старт-за-5-минут) • [📖 Инструкция](docs/INSTALL.md) • [📰 RSS для форумов](docs/FORUMS.md) • [⚙️ Настройки](#настройки-ленты) • [❓ FAQ](#faq)

</div>

---

## ✨ Что умеет

| | Возможность |
|---|---|
| 📡 | **Любое число лент** — разные разделы форума → разные Discord-каналы |
| 🎨 | **Красивый embed** — цветная полоса, картинка, автор, дата, футер, кнопка-ссылка |
| 📝 | **Свой шаблон сообщения** — переменные `{title} {link} {author} {summary} {date} {feed_name} {tags}` |
| 🔎 | **Фильтры** — включать только нужное / исключать флуд по ключевым словам |
| ⏱ | **Гибкий интервал** — общий по умолчанию + свой для каждой ленты (мин. 60 сек) |
| 👁 | **Предпросмотр без спама** — проверить ленту до публикации |
| 📤 | **Тест-пост** — отправить свежую запись в Discord одной кнопкой |
| 🌐 | **Веб-админка** — тёмная тема, работает в браузере, без сборки фронтенда |
| ⚡ | **Слэш-команды** — `/rss-list`, `/rss-check` прямо в Discord |
| 💾 | **Без дублей** — запоминает отправленное в `data/seen.json` |

Пример поста в Discord:

> **📰 Релиз мода — Audi RS7 [1.2]**
> 👤 Vasyan · 🕒 2026-11-02
>
> Добавлены новые колёса, фикс фар, обновлённый салон…
>
> [📖 Читать на форуме] (кнопка)

---

## 🚀 Быстрый старт (за 5 минут)

> Подробно по шагам — в [📖 docs/INSTALL.md](docs/INSTALL.md).

**1. Установи Python 3.10+** — https://www.python.org/downloads/ (при установке поставь галочку `Add to PATH`).

**2. Скачай и настрой:**

```bat
cd discord-rss-bot
copy config.example.json config.json
pip install -r requirements.txt
```

Открой `config.json` и впиши минимум 3 вещи:

```json
{
  "discord_token": "ТОКЕН_С_DISCORD_DEVELOPER_PORTAL",
  "guild_id": null,
  "feeds": [{
    "rss_url": "https://твой-форум.ru/feed",
    "channel_id": "123456789012345678"
  }]
}
```

**3. Пригласи бота на сервер:**

1. https://discord.com/developers/applications → твоё приложение → **OAuth2 → URL Generator**
2. Scopes: `bot` + `applications.commands`
3. Bot Permissions: `Send Messages`, `Embed Links`
4. Открой сгенерированный URL → выбери сервер.

**4. Запусти:**

```bat
start.bat
```

или:

```bat
python bot.py
```

**5. Открой админку:** http://127.0.0.1:8000 — пароль `admin123` (меняется в `config.json → web.password`).

Готово. Дальше ленты добавляются кнопкой **＋ Добавить ленту** — перезапуск не нужен.

---

## 🌐 Веб-админка

| Вкладка | Что делает |
|---|---|
| 📡 **Ленты** | Список, вкл/выкл, предпросмотр 👁, тест-пост 📤, удаление |
| ⚙️ **Настройки** | Интервал по умолчанию, длина описания, Guild ID, порт, пароль, смена токена |
| 📋 **Логи** | Последние 150 событий: публикации, ошибки RSS, статусы |

Авторизация простая: пароль хранится в `config.json → web.password` и передаётся в заголовке `X-Admin-Token`. Для домашней машины этого достаточно. Не выставляй админку в интернет без обратного прокси и HTTPS.

---

## ⚙️ Настройки ленты

| Поле | Что это | Пример |
|---|---|---|
| Название | Подпись в футере embed | `Новости форума` |
| RSS URL | Лента раздела форума | `https://forum.ru/forums/novosti/index.rss` |
| Канал | ID Discord-канала (цифры) | `123456789012345678` |
| Цвет | Полоса embed слева | `#5865F2` |
| Интервал | Секунд между опросами, `0` = общий | `300` |
| Шаблон | Текст сообщения | `📰 **{title}**\n{summary}\n🔗 {link}` |
| Упоминание | Кого пинговать | пусто / `@everyone` / `<@&ID_роли>` |
| Ключевики вкл. | Только посты с этими словами (через запятую) | `релиз, обновление, v1.2` |
| Ключевики искл. | Пропускать посты с этими словами | `флуд, оффтоп, тест` |
| Макс. постов | Сколько новых записей слать за одну проверку | `3` |
| Embed / Картинка / Автор | Тумблеры оформления | вкл |

### Переменные шаблона

```
{title}      — заголовок темы
{link}       — ссылка на тему
{author}     — автор
{summary}    — очищенный текст (без HTML, обрезанный)
{date}       — дата публикации из RSS
{feed_name}  — название ленты
{tags}       — теги (если есть в RSS)
```

Как узнать ID канала: Discord → Настройки → Расширенные → **Режим разработчика ВКЛ** → правый клик по каналу → **Копировать ID**.

---

## 📰 Поддерживаемые форумы

Подробная таблица URL — в [docs/FORUMS.md](docs/FORUMS.md).

| Форум | Где искать RSS |
|---|---|
| XenForo | `https://forum/index.php?forums/НАЗВАНИЕ.ID/.rss` или `/forums/-/index.rss` |
| phpBB | `https://forum/feed.php` или `feed.php?f=ID` |
| SMF | `https://forum/index.php?action=.xml;type=rss` |
| MyBB | `https://forum/syndication.php` |
| Invision (IPS) | `https://forum/rss/1-massovye-novosti.xml` (смотри блок RSS в админке форума) |
| WordPress / DLE | `https://site/feed` |

> Открой URL в браузере: должен вернуться XML (`<rss>…` / `<feed>…`). Если отдаёт HTML-страницу — это не RSS, ищи ссылку с иконкой 📶 RSS в подвале форума.

---

## ⚡ Слэш-команды в Discord

| Команда | Кто может | Что делает |
|---|---|---|
| `/rss-list` | все | Показать все ленты: ID, название, канал |
| `/rss-check feed_id:...` | **Управление сервером** | Принудительно проверить ленту сейчас |

Чтобы команды появились за секунды, а не за час — впиши `guild_id` (ID своего сервера) в `config.json` и перезапусти бота.

---

## 📁 Структура проекта

```
discord-rss-bot/
├── bot.py                    # Discord-бот + опрос лент (tasks.loop)
├── webadmin.py               # Flask-админка + REST API (/api/*)
├── rss_core.py               # Конфиг, парсинг RSS, фильтры, шаблоны, seen/логи
├── templates/
│   └── dashboard.html        # Интерфейс админки (один файл, без сборки)
├── config.example.json       # Пример конфига → скопируй в config.json
├── requirements.txt
├── start.bat                 # Запуск в 1 клик (Windows)
├── CHANGELOG.md              # Что нового по версиям
├── README.en.md              # English version
├── docs/
│   ├── INSTALL.md            # Пошаговая установка с нуля
│   ├── FORUMS.md             # RSS-адреса для XenForo / phpBB / SMF / IPS…
│   ├── PROMO.md              # 📣 Материалы для публикации и раскрутки
│   └── banner.svg            # Баннер 1280×640 для Social preview
├── data/                     # Создаётся сам: seen.json, bot.log (в git не идёт)
└── README.md
```

API админки: `GET /api/status|feeds|config|logs`, `POST /api/feeds|/feeds/<id>/preview|/feeds/<id>/test`, `PUT /api/feeds/<id>|/api/config`, `DELETE /api/feeds/<id>`, `POST /api/login`. Авторизация — заголовок `X-Admin-Token: <web.password>`.

---

## ❓ FAQ

**Бот офлайн в админке (🔴)?**
Запущен только `webadmin.py` без Discord. Запусти `python bot.py` — админка поднимается вместе с ним в том же процессе.

**«RSS не распарсился»?**
Открой URL в браузере. Частые причины: нужен логин на форуме (закрой раздел или дай гостевой доступ к RSS), Cloudflare, неверный URL. Проверь через кнопку 👁 Предпросмотр — там будет точная ошибка.

**Дубли / спам историей при первом запуске?**
Нет — при первом запуске бот запоминает текущие записи без публикации. Чтобы перепроверить — `/rss-check` или кнопка 📤 Тест (отправляет только самую свежую).

**Как выключить ленту временно?**
Кнопка ⏸ в админке (флаг `enabled`). Удалять не нужно.

**Слэш-команды не появились?**
Подожди до часа (глобальный синк) или задай `guild_id` и перезапусти. Проверь, что при приглашении бота выбрал scope `applications.commands`.

**Порт 8000 занят?**
Поменяй `web.port` в Настройках админки или в `config.json`, перезапусти.

**Безопасно ли хранить токен в config.json?**
`config.json` и `data/` уже в `.gitignore` — в git они не уедут. Никому не показывай токен и смени пароль `admin123` после установки.

---

## 🤝 Contributing

PR и issue приветствуются. Стиль: стандартный Python, без тяжёлых зависимостей (только `discord.py`, `feedparser`, `Flask`, `beautifulsoup4`).

Идеи для развития: несколько каналов на одну ленту, дайджест за день, кнопки реакций, вебхук-режим без Discord-бота, Docker-образ.

## 📄 License

MIT — делай что хочешь, авторство сохрани. См. [LICENSE](LICENSE).
