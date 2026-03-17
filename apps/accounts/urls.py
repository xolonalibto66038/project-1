# apps/accounts/urls/profile.py

from django.urls import path

from apps.accounts.views.student import student_profile_update
from apps.accounts.views.teacher import teacher_profile_update

app_name = "accounts"

urlpatterns = [
    path("teacher/", teacher_profile_update, name="teacher"),
    path("student/", student_profile_update, name="student"),
]
