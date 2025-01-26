import time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import StatusChoices, Task, TaskTypeChoices
from .tasks import countdown_task, sum_numbers_task

User = get_user_model()


class UserRegistrationTests(APITestCase):
    def test_successful_registration(self):
        url = reverse("register")
        data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_duplicate_username_registration(self):
        User.objects.create_user(
            username="existinguser", password="testpass123"
        )
        url = reverse("register")
        data = {"username": "existinguser", "password": "testpass123"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.token_url = reverse("token_obtain")

    def test_successful_token_obtain(self):
        data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post(self.token_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_invalid_credentials_token_obtain(self):
        data = {"username": "wronguser", "password": "wrongpass"}
        response = self.client.post(self.token_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.task1 = Task.objects.create(
            user=self.user,
            task_type=TaskTypeChoices.SUM_NUMBERS,
            input_data={"numbers": [1, 2, 3]},
            status=StatusChoices.COMPLETED,
        )
        self.task2 = Task.objects.create(
            user=self.user,
            task_type=TaskTypeChoices.COUNTDOWN,
            input_data={"seconds": 5},
            status=StatusChoices.PENDING,
        )

    @patch("task_manager_api.tasks.sum_numbers_task.delay")
    @patch("task_manager_api.tasks.countdown_task.delay")
    def test_create_task_success(self, mock_countdown, mock_sum):
        url = reverse("tasks-list")
        data = {
            "task_type": TaskTypeChoices.SUM_NUMBERS,
            "input_data": {"numbers": [4, 5, 6]},
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 3)

        mock_sum.assert_called_once_with(response.data["id"])

    def test_active_tasks_limit(self):
        for _ in range(5):
            Task.objects.create(
                user=self.user,
                task_type=TaskTypeChoices.SUM_NUMBERS,
                input_data={"numbers": [1, 2, 3]},
                status=StatusChoices.PENDING,
            )

        url = reverse("tasks-list")
        data = {
            "task_type": TaskTypeChoices.SUM_NUMBERS,
            "input_data": {"numbers": [4, 5, 6]},
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Достигнут лимит активных задач (5)", str(response.data["detail"])
        )

    def test_get_task_list(self):
        url = reverse("tasks-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_status(self):
        url = reverse("tasks-list") + f"?status={StatusChoices.COMPLETED}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], StatusChoices.COMPLETED)

    def test_retrieve_task_detail(self):
        url = reverse("tasks-detail", args=[self.task1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.task1.id)

    def test_other_user_access(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse("tasks-detail", args=[self.task1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pagination(self):
        for _ in range(15):
            Task.objects.create(
                user=self.user,
                task_type=TaskTypeChoices.SUM_NUMBERS,
                input_data={"numbers": [1, 2, 3]},
                status=StatusChoices.COMPLETED,
            )

        url = reverse("tasks-list") + "?limit=10"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("next", response.data)


class CeleryTasksTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.sum_task = Task.objects.create(
            user=self.user,
            task_type=TaskTypeChoices.SUM_NUMBERS,
            input_data={"a": 10, "b": 20},
            status=StatusChoices.PENDING,
        )

        self.countdown_task = Task.objects.create(
            user=self.user,
            task_type=TaskTypeChoices.COUNTDOWN,
            input_data={"seconds": 2},
            status=StatusChoices.PENDING,
        )

    def test_sum_numbers_task_success(self):
        """Тест успешного выполнения задачи суммирования"""
        sum_numbers_task(self.sum_task.id)

        updated_task = Task.objects.get(id=self.sum_task.id)
        self.assertEqual(updated_task.status, StatusChoices.COMPLETED)
        self.assertEqual(updated_task.result["result"], 30)
        self.assertEqual(updated_task.status, "completed")

    def test_sum_numbers_task_missing_parameters(self):
        """Тест ошибки при отсутствии необходимых параметров"""
        invalid_task = Task.objects.create(
            user=self.user,
            task_type=TaskTypeChoices.SUM_NUMBERS,
            input_data={"wrong_key": 5},
            status=StatusChoices.PENDING,
        )

        sum_numbers_task(invalid_task.id)

        updated_task = Task.objects.get(id=invalid_task.id)
        self.assertEqual(updated_task.status, StatusChoices.FAILED)
        self.assertIn("a", updated_task.result["error"])

    @patch("time.sleep")
    def test_countdown_task_success(self, mock_sleep):
        """Тест успешного выполнения задачи отсчета"""
        countdown_task(self.countdown_task.id)

        updated_task = Task.objects.get(id=self.countdown_task.id)
        self.assertEqual(updated_task.status, StatusChoices.COMPLETED)
        self.assertEqual(
            updated_task.result["message"], "Обратный отсчёт завершён"
        )
        mock_sleep.assert_called_once_with(2)

    def test_countdown_task_invalid_seconds(self):
        """Тест ошибки при некорректном значении seconds"""
        invalid_task = Task.objects.create(
            user=self.user,
            task_type=TaskTypeChoices.COUNTDOWN,
            input_data={"seconds": "invalid"},
            status=StatusChoices.PENDING,
        )

        countdown_task(invalid_task.id)

        updated_task = Task.objects.get(id=invalid_task.id)
        self.assertEqual(updated_task.status, StatusChoices.FAILED)
        self.assertIn("int", updated_task.result["error"])

    def test_countdown_task_missing_seconds(self):
        """Тест ошибки при отсутствии параметра seconds"""
        invalid_task = Task.objects.create(
            user=self.user,
            task_type=TaskTypeChoices.COUNTDOWN,
            input_data={"wrong_key": 5},
            status=StatusChoices.PENDING,
        )

        countdown_task(invalid_task.id)

        updated_task = Task.objects.get(id=invalid_task.id)
        self.assertEqual(updated_task.status, StatusChoices.FAILED)
        self.assertIn("seconds", updated_task.result["error"])
