from django.db import models
from django.contrib.auth.models import User


STATUS_CHOICES = [
    ('pending', 'Запланировано'),
    ('running', 'Выполняется'),
    ('completed', 'Выполнено'),
    ('failed', 'Ошибка'),
]

class Task(models.Model):
    user =  models.ForeignKey(User, on_delete = models.CASCADE)
    task_type = models.CharField(max_length=100)
    input_data = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.status}'
