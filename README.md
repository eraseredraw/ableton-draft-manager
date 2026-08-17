# ableton-draft-manager

CLI-инструмент для управления черновиками Ableton Live: сканирование проектов, извлечение метаданных из `.als`, поиск дубликатов, снапшот-бэкапы и отчёт-журнал сессий.

## Возможности

- Сканирование папок с Ableton-проектами (`.als`)
- Извлечение метаданных: BPM, тональность, длительность, число треков
- Поиск дубликатов по содержимому
- Снапшот-бэкапы по датам (с ограничением числа хранимых копий)
- Markdown-отчёт по проектам и сессиям
- CI: lint + тесты + сборка релиза (GitHub Actions)

## Требования

- Python 3.11+
- Ableton Live 10/11/12 проекты

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e .
```

## Использование

```bash
admanager scan --path "D:\Music\Drafts" --report report.md
admanager scan --path "D:\Music\Drafts" --backup --keep 5
admanager dups --path "D:\Music\Drafts"
```

## Структура

```
src/admanager/        # исходники
tests/                # pytest-тесты
.github/workflows/    # CI
```

## Разработка

```bash
pip install -e .[dev]
pytest
ruff check src tests
```