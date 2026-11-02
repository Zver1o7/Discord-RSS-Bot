# 📖 Установка с нуля — Discord RSS Bot

Пошагово для Windows. Для Linux — те же шаги, только команды в блоке для Linux.

---

## 1. Что понадобится (2 минуты)

- [ ] Python **3.10+** — https://www.python.org/downloads/
  - ⚠️ При установке поставь галочку **Add python.exe to PATH**, иначе `python` не найдётся в консоли.
- [ ] Discord-сервер, где ты админ (или есть права приглашать ботов).
- [ ] RSS-ссылка форума (где взять — см. [FORUMS.md](FORUMS.md)).

Проверь установку:

```bat
python --version
```

Должно показать `Python 3.10.x` или новее. Если пишет «не найден» — переустанови с галочкой PATH.

Для Linux:

```bash
python3 --version
pip3 --version
```

---

## 2. Создай Discord-приложение (3 минуты)

1. Зайди на https://discord.com/developers/applications → **New Application** → любое имя, например `Forum RSS`.
2. Слева **Bot** → **Reset Token** → **скопируй токен** (выглядит как длинная строка). Это `discord_token`.
   - Никому его не показывай. Если засветил — там же **Reset Token**.
3. Пригласи бота на сервер:
   - Слева **OAuth2 → URL Generator**.
   - Scopes: ✅ `bot`, ✅ `applications.commands`.
   - Bot Permissions: ✅ `Send Messages`, ✅ `Embed Links` (остальное по желанию).
   - Открой сгенерированный URL внизу → выбери свой сервер → Authorize.
4. (Опционально, для мгновенных слэш-команд) Узнай **ID сервера**: Discord → Настройки → Расширенные → Режим разработчика ВКЛ → правый клик по названию сервера → Копировать ID. Это `guild_id`.

> Привилегированные интенты (Members / Message Content) **не нужны** — бот работает на базовых.

---

## 3. Настрой бота (2 минуты)

```bat
cd discord-rss-bot
copy config.example.json config.json
pip install -r requirements.txt
```

Открой `config.json` в блокноте / VS Code и впиши:

| Поле | Куда |
|---|---|
| `discord_token` | Токен из шага 2 |
| `guild_id` | ID сервера (или оставь `null`) |
| `web.password` | Свой пароль админки вместо `admin123` |
| `feeds[0].rss_url` | RSS твоего форума |
| `feeds[0].channel_id` | ID канала для постов |

Как узнать **ID канала**: режим разработчика ВКЛ → правый клик по каналу → Копировать ID (только цифры, например `123456789012345678`).

Пример готового `config.json`:

```json
{
  "discord_token": "MTIz...",
  "guild_id": "111222333444555666",
  "default_interval": 300,
  "max_summary_length": 300,
  "web": { "enabled": true, "port": 8000, "password": "мой-секретный-пароль" },
  "feeds": [
    {
      "id": "feed_example",
      "name": "Новости форума",
      "rss_url": "https://forum.example.ru/forums/novosti/index.rss",
      "channel_id": "123456789012345678",
      "enabled": true,
      "interval_sec": 0,
      "color": "#5865F2",
      "template": "📰 **{title}**\n👤 {author} · 🕒 {date}\n\n{summary}\n\n🔗 {link}",
      "use_embed": true,
      "show_image": true,
      "show_author": true,
      "mention": "",
      "include_keywords": "",
      "exclude_keywords": "",
      "max_posts": 3
    }
  ]
}
```

> `config.json` уже в `.gitignore` — токен не уедет в GitHub. Никогда не коммить его вручную.

---

## 4. Запуск

**Windows (двойной клик):**

```bat
start.bat
```

**Вручную:**

```bat
python bot.py
```

**Только админка без Discord** (поковырять настройки):

```bat
python webadmin.py
```

Открой **http://127.0.0.1:8000**, введи пароль из `web.password`.

Дальше: **＋ Добавить ленту** → вставь RSS URL + ID канала → Сохранить → 👁 Предпросмотр → 📤 Тест. Перезапуск бота не нужен, интервал применяется на лету.

Для Linux:

```bash
pip3 install -r requirements.txt
python3 bot.py
```

---

## 5. Проверка что всё работает

1. В админке бейдж сверху: **🟢 Бот онлайн**.
2. Вкладка **Логи**: `Бот онлайн: ... (серверов: 1)`.
3. Нажми 👁 на ленте — должны подтянуться 2–3 последние темы форума.
4. Нажми 📤 Тест — в Discord-канале появится красивый embed.
5. В Discord введи `/rss-list` — бот покажет ленты.

Если `/`-команд нет — подожди до часа (глобальный синк Discord) или задай `guild_id` и перезапусти.

---

## 6. Автозапуск (чтобы работал 24/7)

Варианты по возрастанию сложности:

- **Просто:** оставь консоль с `python bot.py` включённой.
- **Windows Task Scheduler:** задание при входе → `pythonw.exe D:\путь\bot.py` (без окна).
- **VPS (рекомендуется):** `systemd`-сервис или `tmux` / `screen` + `python3 bot.py`.
- **Docker** (если добавишь Dockerfile): `docker compose up -d`.

Для VPS не забудь: админка слушает только `127.0.0.1` — это правильно. Для доступа снаружи используй SSH-туннель (`ssh -L 8000:localhost:8000 user@server`), а не открывай порт в интернет.

---

## 7. Если что-то пошло не так

| Симптом | Что делать |
|---|---|
| `Python was not found` | Переустанови Python с галочкой Add to PATH |
| `Нет токена Discord` | Не создан `config.json` или пустой `discord_token`; либо задай `DISCORD_TOKEN` в переменных окружения |
| `LoginFailure / Improper token` | Токен неверный или с пробелами — скопируй заново из Developer Portal → Bot |
| `Канал недоступен` | Бота нет на сервере / неверный `channel_id` / нет прав на канал |
| `RSS не распарсился` | Открой URL в браузере — должен быть XML. См. FORUMS.md, проверь гостевой доступ к разделу |
| `Порт уже занят` | Смени `web.port` (например 8001) и перезапусти |
| Посты не приходят | Лента выключена (⏸), интервал ещё не подошёл, фильтры режут всё, записи уже в `seen.json`. Смотри вкладку Логи |

Не помогло — открой issue на GitHub и приложи: версию Python (`python --version`), кусок `data/bot.log` (без токена!) и URL ленты.
