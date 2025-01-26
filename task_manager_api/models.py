from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusChoices(models.TextChoices):
    PENDING = "pending", _("Запланировано")
    RUNNING = "running", _("Выполняется")
    COMPLETED = "completed", _("Выполнено")
    FAILED = "failed", _("Ошибка")


class TaskTypeChoices(models.TextChoices):
    SUM_NUMBERS = "sum_numbers", _("сумма чисел")
    COUNTDOWN = "countdown", _("обратный отсчет")


class Task(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name=_("Пользователь")
    )
    task_type = models.CharField(
        max_length=15,
        choices=TaskTypeChoices.choices,
        default=TaskTypeChoices.SUM_NUMBERS,
        verbose_name=_("Тип задачи"),
    )
    input_data = models.JSONField(verbose_name=_("Входные данные"))
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name=_("Статус"),
    )
    result = models.JSONField(
        null=True, blank=True, verbose_name=_("Результат")
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Дата создания")
    )

    def __str__(self):
        return f"Task {self.id} {self.task_type} {self.status}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Задача")
        verbose_name_plural = _("Задачи")
