<p align="center">
  <img src="docs/banner.svg" alt="Discord RSS Bot" width="100%">
</p>

# Discord RSS Bot

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.3.0-blue?style=flat-square)](CHANGELOG.md)

> Форум/сайт RSS → красивые посты в Discord. Веб-админка в браузере, фильтры, шаблоны, слэш-команды.

[🇬🇧 English version](README.en.md)

## Для чего

Бот следит за RSS/Atom-лентами и публикует новые записи в выбранный канал Discord в виде аккуратного embed с картинкой, автором, кнопкой и прочим.

## Скриншоты

<p align="center">
  <img src="docs/screenshots/web-admin-dashboard.svg" alt="Веб-админка Discord RSS Bot" width="900">
</p>

<p align="center">
  <img src="docs/screenshots/discord-embed-example.svg" alt="Пример embed-поста в Discord" width="700">
</p>

## Возможности

- **Любые RSS/Atom** — универсальный парсер, подходит под большинство источников
- **Красивые embed-посты** — цвет акцента, превью, автор, дата, футер, кнопка «Читать на форуме»
- **Веб-админка в браузере** — тёмная панель на Flask. Добавление, редактирование, фильтры, предпросмотр и тест без правок JSON
- **Вебхуки и ветки** — можно публиковать через webhook или в конкретную thread по ID
- **Кастомные шаблоны** — полный контроль над текстом поста через переменные
- **Фильтры** — «только» и «исключить» по ключевым словам
- **Индивидуальные интервалы** — свой таймаут для каждой ленты
- **Импорт/экспорт** — бэкап и перенос лент через JSON
- **Дублирование лент** — быстро скопировать настройки
- **Умная синхронизация** — при первом запуске история не публикуется
- **Тест из админки и из Discord** — быстрая проверка перед боевым включением
- **Статистика** — счётчик публикаций, аптайм, команды `/about` и `/rss-stats`
- **Логи в админке** — сразу видно, что происходит
- **Защита паролем** — опционально для веб-панели
- **Docker** — готовый `Dockerfile` и `docker-compose.yml`
- **Видимое авторство** — баннер в консоли, команда `/about`, футер в админке

## Слэш-команды

| Команда | Права | Описание |
|---|---|---|
| `/about` | Любые | Информация о боте, версия, статистика, uptime |
| `/rss-ping` | Любые | Проверка задержки бота |
| `/rss-stats` | Любые | Краткая статистика: ленты, посты, аптайм |
| `/rss-list` | Любые | Список всех лент, каналов и статусов |
| `/rss-info <feed_id>` | Любые | Настройки выбранной ленты (с автодополнением ID) |
| `/rss-check <feed_id>` | Управление сервером | Принудительно проверить ленту |
| `/rss-toggle <feed_id>` | Управление сервером | Включить/выключить ленту |
| `/rss-test <feed_id>` | Управление сервером | Опубликовать свежую запись для теста |
| `/rss-reset <feed_id>` | Управление сервером | Сбросить историю ленты |
| `/rss-reload` | Управление сервером | Перечитать конфиг без перезапуска |

## Быстрый старт

```bash
git clone https://github.com/Zver1o7/Discord-RSS-Bot.git
cd Discord-RSS-Bot
pip install -r requirements.txt
copy config.example.json config.json
```

Открой `config.json`, впиши `discord_token`. Запусти:

```bash
start.bat
```
или
```bash
python bot.py
```

Админка откроется на [http://127.0.0.1:8000](http://127.0.0.1:8000)

Подробная инструкция: [docs/INSTALL.md](docs/INSTALL.md)

## Docker

```bash
git clone https://github.com/Zver1o7/Discord-RSS-Bot.git
cd Discord-RSS-Bot
copy config.example.json config.json
docker compose up -d --build
```

Админка будет доступна на `http://127.0.0.1:8000`. `config.json` и папка `data/` монтируются как volume.

## Структура проекта

```text
Discord-RSS-Bot/
├── bot.py
├── rss_core.py
├── webadmin.py
├── templates/dashboard.html
├── docs/
│   ├── INSTALL.md
│   ├── FORUMS.md
│   └── screenshots/
├── config.example.json
├── requirements.txt
├── start.bat
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Автор

**[Zver1o7](https://github.com/Zver1o7)**

[Репозиторий](https://github.com/Zver1o7/Discord-RSS-Bot) · [Проблемы](https://github.com/Zver1o7/Discord-RSS-Bot/issues) · [Релизы](https://github.com/Zver1o7/Discord-RSS-Bot/releases)

## Лицензия

[MIT License](LICENSE)
