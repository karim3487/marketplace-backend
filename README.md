# Marketplace Backend

API для прототипа маркетплейса, построенное на **FastAPI**, **SQLAlchemy 2.0** и **PostgreSQL**.

## 🛠 Технологический стек

- **Python 3.12**
- **FastAPI**: современный асинхронный фреймворк для API.
- **SQLAlchemy 2.0**: асинхронная работа с базой данных.
- **Alembic**: миграции базы данных.
- **MinIO/S3**: хранилище для изображений товаров.
- **uv**: менеджер пакетов и виртуального окружения (рекомендуется).
- **Ruff**: линтинг и форматирование кода.

---

## 🚀 Установка и запуск

Для локальной разработки без Docker выполните следующие шаги:

### 1. Подготовка окружения
Убедитесь, что у вас установлен **uv**. Если нет, [установите его](https://github.com/astral-sh/uv).

```bash
# Установка зависимостей
uv sync

# Создание .env файла
cp .env.example .env
```

### 2. Запуск инфраструктуры
Для работы бэкенда нужны PostgreSQL и MinIO. Вы можете запустить их из соседнего репозитория `marketplace-stack`:
```bash
cd ../marketplace-stack
make up-infra
```

### 3. Настройка базы данных
```bash
cd ../marketplace-backend

# Применение миграций
uv run alembic upgrade head

# Создание администратора (настройки берутся из .env)
uv run python scripts/create_admin.py

# Наполнение тестовыми данными (опционально)
uv run python scripts/seed.py
```

### 4. Запуск сервера
```bash
make run
```
Сервер будет доступен по адресу: [http://localhost:8000](http://localhost:8000)
Документация Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🏗 Разработка (Makefile)

Доступные команды:
- `make format` — форматирование кода (ruff).
- `make lint` — проверка кода линтером.
- `make migrate-create m="message"` — создание новой миграции.
- `make migrate-up` — применение миграций.
- `make seed` — наполнение БД тестовыми товарами.
- `make test` — запуск дымовых тестов (smoke tests).

---

## 🧪 Тестирование
Для проверки работоспособности API:
```bash
make test
```
Это запустит базовые тесты на эндпоинты здоровья (health check).

---

## 🐳 Docker
Бэкенд поставляется с Dockerfile, оптимизированным для быстрой сборки и работы с `uv`. Образ используется в общем `docker-compose.yaml` в репозитории `marketplace-stack`.
