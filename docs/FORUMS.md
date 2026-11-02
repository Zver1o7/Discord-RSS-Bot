# 📰 RSS-адреса для популярных форумов

Боту нужен именно **XML**, а не HTML-страница. Проверка: открой URL в браузере — должен показаться машинный XML (`<rss…>` или `<feed…>`), а не обычная страница форума.

## XenForo (2.x)

- Раздел: `https://forum.example/index.php?forums/НАЗВАНИЕ.12/.rss`
  - ID раздела виден в URL раздела.
- Весь форум: `https://forum.example/index.php?forums/-/index.rss`
- Альтернатива: `https://forum.example/forums/НАЗВАНИЕ.12/index.rss` (если включены ЧПУ).

Если пусто — в админке XenForo: Настройки → RSS может быть отключён.

## phpBB (3.x)

- Всё: `https://forum.example/feed.php`
- Конкретный раздел: `https://forum.example/feed.php?f=12`
- Новости: `https://forum.example/feed.php?mode=news`

Включается: Админка → Общие → Настройки фида.

## SMF (Simple Machines Forum)

- `https://forum.example/index.php?action=.xml;type=rss`
- Раздел: `https://forum.example/index.php?action=.xml;board=12;type=rss`

## MyBB

- `https://forum.example/syndication.php`
- Раздел: `https://forum.example/syndication.php?fid=12&limit=15`

Включается: Админка → Конфигурация → RSS-синдикация.

## Invision Community (IPS)

- Админка форума → Community → RSS-каналы → там готовые URL вида `https://forum.example/rss/1-nazvanie.xml`.
- Единого шаблона нет — скопируй URL из админки/подвала форума.

## vBulletin

- `https://forum.example/external.php?type=rss2`
- Раздел: `https://forum.example/external.php?type=rss2&forumids=12`

## WordPress / DLE / XenForo-портал (новости сайта)

- `https://site.example/feed`
- DLE: `https://site.example/rss.xml`

## Если RSS закрыт гостям

Симптом: в браузере без логина — ошибка прав, а залогиненным — XML. Решения:

1. Открой раздел гостям (только чтение) — лучший вариант.
2. Или создай отдельный открытый раздел-зеркало новостей.
3. Бот авторизацию на форуме не поддерживает by design (так безопаснее).

## Быстрая диагностика

1. Открой URL в приватном окне браузера — видишь XML? Отлично.
2. В админке бота: 👁 Предпросмотр — покажет записи или точную ошибку парсера.
3. Лента есть, но посты не идут — проверь фильтры ключевиков и что лента включена (🟢).
