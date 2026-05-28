<div align="center">

# ♟️ DreamerExx Chess Engine

### Шахматный движок с графическим интерфейсом, ИИ и дебютной книгой

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.5.0-green.svg)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## ✨ Возможности

| Функция | Описание |
|---------|----------|
| 🎮 **Полная шахматная логика** | Все правила: рокировка, взятие на проходе, превращение пешек |
| 🤖 **Искусственный интеллект** | Alpha-beta с итеративным углублением, LMR, Null-move pruning |
| 📚 **Дебютная книга** | Дебютные линии для реалистичной игры |
| 🎨 **Графический интерфейс** | Красивая доска с загрузкой фигур из интернета |
| 🔄 **Переворот доски** | Играйте за любой цвет |
| 📋 **PGN экспорт** | Сохраняйте и копируйте партии |
| 🧠 **Позиционная оценка** | Фаза игры, пешечная структура, мобильность, пара слонов |
| ⚡ **Эвристики поиска** | Killer moves, History heuristic, Transposition table, Quiescence search |

---

### ВНИМАНИЕ: V3 сильнее V2 в контроли с 3+ минутами, а в пулю и быстрый блиц V2 будет сильнее.

## 🚀 Запуск

### 1. Графический интерфейс (GUI)

```bash
python gui.py
```

**Требования:** Python 3.8+, Pygame (`pip install pygame`)

### 2. UCI версия (для Arena, Cute Chess, Lichess)

Скачайте [последний релиз](https://github.com/ExxDreamerCode/chess_engine/releases/tag/engineV3)

---

## 📊 Турнирные результаты

### 🏆 Gauntlet V3 (15 партий, 5 минут на 40 ходов)

| Rank | Name | Elo | Games | Score | Draw |
|:-----|:-----|:----|:------|:------|:-----|
| 🥇 | **DreamerExx v3** | **+382** | 15 | **90.0%** | 6.7% |
| 🥈 | Allaya Chess | 0 | 3 | 50.0% | 33.3% |
| 🥉 | Sunfish | -inf | 3 | 0.0% | 0.0% |
| 4 | Endamat | -inf | 3 | 0.0% | 0.0% |
| 5 | Beast | -inf | 3 | 0.0% | 0.0% |
| 6 | DreamerExx v2 | -inf | 3 | 0.0% | 0.0% |

#### 🎯 Результаты V3

| Соперник | Результат |
|:---------|:----------|
| Allaya Chess | 1.5/3 (50%) |
| Sunfish | 3/3 (100%) |
| Endamat | 3/3 (100%) |
| Beast | 3/3 (100%) |
| DreamerExx v2 | 3/3 (100%) |

(Endamat почему то все 3 партии проиграл по времени)

[Смотреть полный PGN турнира](Test_V3.pgn)  

---

### 🏆 Турнир V2 (1+1)

DreamerExx v2 против четырёх движков на Python

| Rank | Name | Elo | Games | Score | Draw |
|:-----|:-----|:----|:------|:------|:-----|
| 🥇 | Sunfish | 241 | 12 | 80.0% | 20% |
| 🥈 | Endamat | 97 | 12 | 63.6% | 36% |
| 🥉 | **DreamerExx v2** | 0 | 12 | 50.0% | 17% |
| 4 | Allaya Chess | -97 | 12 | 36.4% | 36% |
| 5 | Beast | -241 | 12 | 20.0% | 0% |

#### 🎯 Результаты V2

| Достижение | Результат |
|:-----------|:----------|
| Победа над Sunfish | 1 победа в 3 встречах |
| Против Beast | 3 победы из 3 |
| Общий результат | 6.0 очков из 12 (50%) |

[Смотреть полный PGN турнира](Test_V2.pgn)  

---

## 📈 Прогресс версий

| Версия | Примерный рейтинг | Ключевые улучшения |
|:-------|:---------------|:-------------------|
| V1 | 500-800 | Базовая реализация |
| V2 | 1700-1800 | Quiescence search, транспозиция, дебютная книга |
| **V3** | **1900-2000** | LMR, Null-move pruning, фаза игры, мобильность, проходные пешки |

---

## 🤖 Lichess Bots

| Версия | Lichess | Пуля | Блиц | Рапид | Статус |
|--------|---------|------|------|-------|--------|
| **V3** | [@DreamerExx_V3](https://lichess.org/@/DreamerExxV3) | ~? | ~? | ~? | 🚧 Скоро |
| **V2** | [@DreamerExx_V2](https://lichess.org/@/DreamerExx_V2) | ~1700 | ~1600 | ~1700 | 🔥 Активен |
| **V1** | [@DreamerExx_V1](https://lichess.org/@/DreamerExx_V1) | ~700 | ~700 | ~700 | 🦴 Исторический |

---

## 🎯 Технологии поиска

```mermaid
graph LR
    A[Позиция] --> B[Iterative Deepening]
    B --> C[Alpha-Beta + TT]
    C --> D[Move Ordering]
    D --> E[LMR / Null-move]
    E --> F[Quiescence Search]
    F --> G[Evaluation]
    G --> A
```

---

## 📁 Структура проекта

```
chess_engine/
├── uci.py              # UCI интерфейс
├── gui.py              # Графический интерфейс
├── engine.py           # Фасад движка
├── board.py            # Логика доски
├── evaluation.py       # Оценка позиции
├── search.py           # Поиск
├── transposition.py    # Транспозиционная таблица
├── opening_book.py     # Дебютная книга
└── pieces/             # Изображения фигур
```

---