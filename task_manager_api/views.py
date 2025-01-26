from django.db.models import Q
from rest_framework import generics, mixins, permissions, viewsets
from rest_framework.exceptions import ParseError

from .models import StatusChoices, Task, TaskTypeChoices
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
    queryset = Task.objects.all()

    def perform_create(self, serializer):
        active_statuses = [StatusChoices.PENDING, StatusChoices.RUNNING]
        active_tasks = Task.objects.filter(
            user=self.request.user, status__in=active_statuses
        ).count()

        if active_tasks >= 5:
            raise ParseError("Достигнут лимит активных задач (5)")

        task = serializer.save(user=self.request.user)

        if task.task_type == TaskTypeChoices.SUM_NUMBERS:
            sum_numbers_task.delay(task.id)
        elif task.task_type == TaskTypeChoices.COUNTDOWN:
            countdown_task.delay(task.id)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
