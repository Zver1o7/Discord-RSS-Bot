# Changelog

All notable changes to this project will be documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), versioning: [Semantic Versioning](https://semver.org/lang/ru/).

## [1.0.0] — 2026-11-04

Первый публичный релиз.

### Added

- 📡 Универсальный парсинг любых RSS-лент (XenForo, phpBB, SMF, MyBB, IPS, vBulletin, WordPress, DLE)
- 🎨 Красивые embed-посты: цвет, картинка (из enclosure/media/`<img>`), автор, дата, футер, кнопка-ссылка
- 📝 Настраиваемый шаблон сообщения: `{title} {link} {author} {summary} {date} {feed_name} {tags}`
- 🔎 Фильтры по ключевым словам: включать / исключать
- ⏱ Интервал проверки: общий по умолчанию + свой для каждой ленты (мин. 60 сек)
- 🌐 Веб-админка на Flask (тёмная тема, http://127.0.0.1:8000):
  - добавление / редактирование / удаление / вкл-выкл лент
  - 👁 предпросмотр ленты без публикации (с макетом embed)
  - 📤 тест-пост в Discord одной кнопкой
  - ⚙️ глобальные настройки: интервал, длина описания, guild_id, порт, пароль, токен
  - 📋 логи последних 150 событий
  - 🔐 авторизация по паролю (`web.password`)
- ⚡ Слэш-команды `/rss-list` и `/rss-check` (проверка — только для «Управление сервером»)
- 💾 Защита от дублей: `data/seen.json`, первый запуск не спамит историей
- 📁 Хранение конфига в `config.json` (в `.gitignore`), логов в `data/bot.log`
- 🖥 `start.bat` — запуск в один клик на Windows

### Security

- Токен и пароль не попадают в git (`.gitignore`: `config.json`, `data/`)
- Админка слушает только `127.0.0.1` — наружу не светится без твоего прокси
- Токен можно задать и через переменную окружения `DISCORD_TOKEN`
