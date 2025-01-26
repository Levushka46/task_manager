from django.db.models import Q
from rest_framework import generics, mixins, permissions, serializers, viewsets
from rest_framework.exceptions import ParseError

from .models import Task
from .serializers import TaskSerializer, UserRegistrationSerializer
from .tasks import countdown_task, sum_numbers_task


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer


class TaskViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        active_tasks = Task.objects.filter(
            user=self.request.user, status__in=["pending", "running"]
        ).count()

        if active_tasks >= 5:
            raise ParseError("Достигнут лимит активных задач (5)")

        task = serializer.save(user=self.request.user)

        if task.task_type == "sum_numbers":
            sum_numbers_task.delay(task.id)
        elif task.task_type == "countdown":
            countdown_task.delay(task.id)

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)
