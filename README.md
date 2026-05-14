# Library API

API бібліотеки книг на FastAPI з інтеграційними тестами, TDD та GitHub Actions CI.

---

## CI Status

> Замініть:
> - `YOUR_USERNAME`
> - `YOUR_REPOSITORY`

---

# Можливості API

- Додавання книг
- Пошук книг
- Видача книг
- Повернення книг
- Перевірка доступності
- Список книг користувача
- Прострочені книги (`getOverdueBooks`)

---

# Технології

- Python 3.11
- FastAPI
- SQLAlchemy
- SQLite
- Pytest
- HTTPX
- GitHub Actions

---

# Запуск локально

## 1. Створення віртуального середовища

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 2. Встановлення залежностей

```bash
pip install fastapi sqlalchemy pytest pytest-asyncio httpx uvicorn
```

---

# Запуск API

```bash
uvicorn app.main:app --reload
```

API буде доступне за адресою:

```text
http://127.0.0.1:8000
```

Swagger документація:

```text
http://127.0.0.1:8000/docs
```

---

# Запуск тестів

```bash
pytest -v
```

---

# GitHub Actions

CI автоматично запускає тести при:

* push
* pull request

Файл конфігурації:

```text
.github/workflows/test.yml
```

---

# TDD Workflow

## RED

Додано failing test для `getOverdueBooks`

## GREEN

Реалізовано мінімальну логіку

## REFACTOR

Оптимізовано структуру запиту та читабельність коду
