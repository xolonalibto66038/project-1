# apps/accounts/views/teacher.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.forms.teacher import TeacherProfileForm
from apps.accounts.forms.user import UserUpdateForm
from apps.authentication.decorators import teacher_required


@login_required
@teacher_required
def teacher_profile_update(request):
    user = request.user
    profile = user.teacher_profile

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, request.FILES, instance=user)
        profile_form = TeacherProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:teacher")

    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = TeacherProfileForm(instance=profile)

    return render(
        request,
        "dashboard/update_teacher.html",
        {
            "profile": profile,
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )
