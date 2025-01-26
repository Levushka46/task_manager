# Task Manager 🚀

Асинхронная система управления задачами с использованием Django REST Framework и Celery. Позволяет создавать задачи, отслеживать их статус и получать результаты через API.

## Основные возможности ✨
- JWT аутентификация
- 2 типа задач: сумма чисел и обратный отсчёт
- Ограничение: 5 одновременных задач на пользователя
- Фильтрация задач по статусу
- Пагинация результатов
- Полная интеграция с Celery + Redis

## Технологии 🔧
- Python 3.8.10
- Django 4.2
- Django REST Framework 3.15
- Celery 5.4
- Redis 5.2
- PostgreSQL
- djangorestframework-simplejwt 5.3

## Установка ⚙️

1. Клонировать репозиторий:
```bash
git clone https://github.com/Levushka46/task_manager.git
cd task_manager
```
2. Запустить docker:
```bash
docker compose up --build
```

## Тесты🔧

```bash
python3 manage.py test
```

## API Endpoints

1. Регистрация пользователя
```http
POST /api/register/
```

Пример запроса:
```json
{
  "username": "user123",
  "password": "securepassword123"
}
```

2.1 Получение JWT токена
```http
POST /api/token/
```

Пример запроса:
```json
{
  "refresh": "eyJhbG...",
  "access": "eyJhbGci..."
}
```
2.2 Обновление JWT токена
```http
POST /api/token/refresh/
```

```json
{
  "refresh": "eyJhbG...",
}
```

3. Создание задачи
```http
POST /api/tasks/
```

Пример запроса:
```json
{
  "task_type": "sum_numbers",
  "input_data": {"a": 5, "b": 3}
}
```
Или
```json
{
  "task_type": "countdown",
  "input_data": {"seconds": 10}
}
```

4. Список задач пользователя
```http
GET /api/tasks/
```
Параметры query:
```
?status=pending,running - фильтрация по статусам
```
```
?limit=10&offset=0 - пагинация
```
Пример ответа:
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "task_type": "sum_numbers",
      "status": "COMPLETED",
      "result": 8,
      "created_at": "2023-08-20T12:34:56Z"
    }
  ]
}
```

5. Детали задачи
```http
GET /api/tasks/{id}/
```

Пример ответа при вводе 1:
```json
{
  "id": 1,
  "task_type": "countdown",
  "status": "RUNNING",
  "input_data": {"seconds": 10},
  "result": null,
  "created_at": "2023-08-20T12:34:56Z"
}
```

Используйте JWT токен в заголовках:
```
Authorization: Bearer your.access.token
```
