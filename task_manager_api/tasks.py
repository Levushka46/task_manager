import time

from celery import shared_task

from .models import Task


@shared_task
def sum_numbers_task(task_id):
    task = Task.objects.get(id=task_id)
    task.status = "running"
    task.save()

    try:
        result = task.input_data["a"] + task.input_data["b"]
        task.result = {"result": result}
        task.status = "completed"
    except Exception as e:
        task.result = {"error": str(e)}
        task.status = "failed"
    finally:
        task.save()


@shared_task
def countdown_task(task_id):
    task = Task.objects.get(id=task_id)
    task.status = "running"
    task.save()

    try:
        time.sleep(task.input_data["seconds"])
        task.result = {"message": "Обратный отсчёт завершён"}
        task.status = "completed"
    except Exception as e:
        task.result = {"error": str(e)}
        task.status = "failed"
    finally:
        task.save()
