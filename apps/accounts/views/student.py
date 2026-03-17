# apps/accounts/views/student.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.forms.student import StudentProfileForm
from apps.accounts.forms.user import UserUpdateForm
from apps.authentication.decorators import student_required


@login_required
@student_required
def student_profile_update(request):
    user = request.user
    profile = user.student_profile

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, request.FILES, instance=user)
        profile_form = StudentProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:student")
        else:
            for error in profile_form.non_field_errors():
                messages.error(request, error)
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = StudentProfileForm(instance=profile)

    return render(
        request,
        "dashboard/update_student.html",
        {
            "profile": profile,
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )
