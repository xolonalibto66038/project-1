from itertools import chain
from operator import attrgetter

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)

from apps.authentication.mixins import TeacherRequiredMixin, StudentRequiredMixin
from apps.curriculum.models import GradeSubject

from ..forms import (
    AddQuestionToQuizForm,
    ChoiceCreateFormSet,
    ChoiceFormSet,
    EssayQuestionForm,
    MultipleChoiceQuestionForm,
    QuizForm,
    TrueFalseQuestionForm,
)
from ..models import (
    Answer,
    Attempt,
    BaseQuestion,
    Choice,
    EssayQuestion,
    MultipleChoiceQuestion,
    Quiz,
    QuizQuestion,
    TrueFalseQuestion,
)

QUESTION_MODELS = {
    "mcq": MultipleChoiceQuestion,
    "essay": EssayQuestion,
    "tf": TrueFalseQuestion,
}


class QuizListView(TeacherRequiredMixin, ListView):
    model = Quiz
    template_name = "apps/assessement/quizzes/list.html"
    context_object_name = "quizzes"
    paginate_by = 10
    ordering = ["-created_at"]

    def get_queryset(self):
        return Quiz.objects.filter(created_by=self.request.user).prefetch_related(
            "quiz_questions"
        )


class QuizCreateView(TeacherRequiredMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = "apps/assessement/quizzes/create.html"
    success_url = reverse_lazy("assessment:quiz:quiz-list")

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save(commit=False)

            # Attach teacher profile
            self.object.created_by = self.request.user

            self.object.save()
            form.save_m2m()

        messages.success(self.request, "Quiz created successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class QuizUpdateView(TeacherRequiredMixin, UpdateView):
    model = Quiz
    form_class = QuizForm
    template_name = "apps/assessement/quizzes/create.html"  # reuse template
    success_url = reverse_lazy("assessment:quiz:quiz-list")

    def get_queryset(self):
        """
        Ensure teacher can only edit their own quizzes
        """
        return Quiz.objects.filter(created_by=self.request.user)

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()

        messages.success(self.request, "Quiz updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class QuizDeleteView(TeacherRequiredMixin, DeleteView):
    model = Quiz
    template_name = "apps/assessement/quizzes/confirm_delete.html"
    success_url = reverse_lazy("assessment:quiz:quiz-list")

    def get_queryset(self):
        return Quiz.objects.filter(created_by=self.request.user)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.quiz_attempts.exists():  # ← fixed from .attempts
            messages.error(request, "Cannot delete quiz with existing attempts.")
            return redirect("assessment:quiz:quiz-detail", pk=self.object.pk)

        messages.success(request, "Quiz deleted successfully.")
        return super().delete(request, *args, **kwargs)


class StudentTakeQuizView(StudentRequiredMixin, View):
    template_name = "apps/assessement/quizzes/take_quiz.html"

    def _get_grade_subject(self):
        return get_object_or_404(
            GradeSubject,
            pk=self.kwargs["grade_subject_pk"],
        )

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def _get_back_url(self):
        return reverse(
            "curriculum:grade-subject:grade-subject-quizzes-list",
            kwargs={"pk": self.kwargs["grade_subject_pk"]},
        )

    def get(self, request, grade_subject_pk, pk):
        quiz          = get_object_or_404(Quiz, pk=pk)
        grade_subject = self._get_grade_subject()

        if not quiz.is_available:
            messages.error(request, "This quiz is not available.")
            return redirect(self._get_back_url())

        # can_attempt, reason = quiz.can_user_attempt(request.user)
        # if not can_attempt:
        #     messages.error(request, reason)
        #     return redirect(self._get_back_url())

        existing_attempt = Attempt.objects.filter(
            student=request.user,
            quiz=quiz,
            is_completed=False,
        ).first()

        if existing_attempt:
            attempt = existing_attempt
        else:
            attempt_number = (
                Attempt.objects.filter(
                    student=request.user, quiz=quiz
                ).count() + 1
            )
            attempt = Attempt.objects.create(
                student=request.user,
                quiz=quiz,
                attempt_number=attempt_number,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

        questions = (
            quiz.quiz_questions
            .select_related("question_content_type")
            .order_by("order")
        )

        return render(request, self.template_name, {
            "quiz":            quiz,
            "attempt":         attempt,
            "questions":       questions,
            "grade_subject":   grade_subject,
            "back_url":        self._get_back_url(),
            "time_remaining":  attempt.time_remaining,
        })

    def post(self, request, grade_subject_pk, pk):
        quiz = get_object_or_404(Quiz, pk=pk)
        attempt = get_object_or_404(
            Attempt,
            pk=request.POST.get("attempt_id"),
            student=request.user,
            quiz=quiz,
            is_completed=False,
        )

        if attempt.is_expired:
            attempt.submit(auto_submit=True)
            messages.warning(request, "Time is up. Quiz auto-submitted.")
            return redirect(
                reverse("assessment:quiz:quiz-result",
                        kwargs={"attempt_id": attempt.pk})
            )

        questions = (
            quiz.quiz_questions
            .select_related("question_content_type")
            .order_by("order")
        )

        with transaction.atomic():
            for qq in questions:
                question = qq.question

                if question is None:
                    continue

                content_type = ContentType.objects.get_for_model(question)

                answer, _ = Answer.objects.get_or_create(
                    student=request.user,
                    attempt=attempt,
                    question_content_type=content_type,
                    question_object_id=question.pk,
                )

                field_name = f"question_{qq.pk}"

                if question.question_type == "tf":
                    value = request.POST.get(field_name)
                    if value in ("true", "false"):
                        answer.answer_boolean = value == "true"
                        answer.save(update_fields=["answer_boolean", "updated_at"])

                elif question.question_type == "mcq":
                    selected_ids = request.POST.getlist(field_name)
                    if selected_ids:
                        valid_ids = list(
                            question.choices.filter(
                                pk__in=selected_ids
                            ).values_list("pk", flat=True)
                        )
                        answer.selected_choices.set(valid_ids)
                        answer.save(update_fields=["updated_at"])

                else:
                    text = request.POST.get(field_name, "").strip()
                    answer.answer_text = text
                    answer.save(update_fields=["answer_text", "updated_at"])

                answer.auto_grade()

            attempt.submit(auto_submit=False)

        messages.success(request, "Quiz submitted successfully.")
        return redirect(
            reverse("assessment:quiz:quiz-result",
                    kwargs={"attempt_id": attempt.pk})
        )

class QuizAddQuestionView(TeacherRequiredMixin, FormView):
    template_name = "apps/assessement/quizzes/add_question.html"
    form_class    = AddQuestionToQuizForm

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(
            Quiz,
            pk=kwargs["pk"],
            created_by=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["teacher"] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        # Type-change submit — re-render without validating
        if "submit_question" not in request.POST:
            form = self.get_form_class()(teacher=request.user)
            return self.render_to_response(self.get_context_data(form=form))
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        question_data   = form.cleaned_data["question"]
        q_type          = question_data["q_type"]
        question        = question_data["question"]
        points_override = form.cleaned_data.get("points_override")

        content_type = ContentType.objects.get_for_model(question)

        already_added = QuizQuestion.objects.filter(
            quiz=self.quiz,
            question_content_type=content_type,
            question_object_id=question.id,
        ).exists()

        if already_added:
            form.add_error("question", "This question is already in the quiz.")
            return self.form_invalid(form)

        next_order = (
            QuizQuestion.objects
            .filter(quiz=self.quiz)
            .order_by("-order")
            .values_list("order", flat=True)
            .first() or 0
        ) + 1

        with transaction.atomic():
            QuizQuestion.objects.create(
                quiz=self.quiz,
                question_type=q_type,
                question_content_type=content_type,
                question_object_id=question.id,
                order=next_order,
                points_override=points_override,
            )

        messages.success(self.request, "Question added successfully.")
        return redirect(
            reverse("assessment:quiz:quiz-add-question", kwargs={"pk": self.quiz.pk})
        )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["quiz"] = self.quiz
        context["quiz_questions"] = (
            self.quiz.quiz_questions
            .select_related("question_content_type")
            .order_by("order")
        )
        return context


class QuizResultView(StudentRequiredMixin, View):
    template_name = "apps/assessement/quizzes/quiz_result.html"

    def get(self, request, attempt_id):
        attempt = get_object_or_404(
            Attempt.objects.select_related(
                'quiz',
                'quiz__grade_subject',
                'quiz__grade_subject__grade',
                'quiz__grade_subject__grade__level',
                'quiz__grade_subject__subject',
                'student',
            ),
            pk=attempt_id,
            student=request.user,
            is_completed=True,
        )

        quiz = attempt.quiz

        # ── Build question + answer pairs ──────────────────────────────
        quiz_questions = (
            quiz.quiz_questions
            .select_related('question_content_type')
            .order_by('order')
        )

        # Bulk-fetch all answers for this attempt — no N+1
        answers_map = {
            (str(a.question_content_type_id), str(a.question_object_id)): a
            for a in attempt.answers.prefetch_related('selected_choices').all()
        }

        question_results = []
        for qq in quiz_questions:
            question = qq.question
            if question is None:
                continue

            ct_id  = str(qq.question_content_type_id)
            obj_id = str(qq.question_object_id)
            answer = answers_map.get((ct_id, obj_id))

            question_results.append({
                'order':            qq.order,
                'question':         question,
                'question_type':    qq.question_type,
                'effective_points': qq.effective_points,
                'answer':           answer,
                'is_correct':       answer.is_correct if answer else None,
                'points_earned':    answer.points_earned if answer else 0,
                # Type-specific helpers
                'selected_choices': (
                    answer.selected_choices.all()
                    if answer and qq.question_type == 'mcq'
                    else []
                ),
                'answer_boolean': (
                    answer.answer_boolean
                    if answer and qq.question_type == 'tf'
                    else None
                ),
                'answer_text': (
                    answer.answer_text
                    if answer and qq.question_type == 'essay'
                    else ''
                ),
            })

        # ── Back URL ──────────────────────────────────────────────────
        back_url = None
        if quiz.grade_subject:
            back_url = reverse(
                'curriculum:grade-subject:grade-subject-quizzes-list',
                kwargs={'pk': quiz.grade_subject.pk},
            )

        return render(request, self.template_name, {
            'attempt':          attempt,
            'quiz':             quiz,
            'question_results': question_results,
            'is_passed':        attempt.is_passed,
            'grade_letter':     attempt.get_grade_letter(),
            'back_url':         back_url,
            'grade_subject':    quiz.grade_subject,
        })
    
class QuizAttemptsView(StudentRequiredMixin, ListView):
    template_name       = "apps/assessement/quizzes/attempts.html"
    context_object_name = "attempts"

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Attempt.objects
            .filter(student=self.request.user, quiz=self.quiz)
            .order_by("-started_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["quiz"]      = self.quiz
        context["back_url"]  = (
            reverse(
                "curriculum:grade-subject:grade-subject-quizzes-list",
                kwargs={"pk": self.quiz.grade_subject.pk},
            )
            if self.quiz.grade_subject
            else None
        )
        return context
    
class QuizDetailView(TeacherRequiredMixin, DetailView):
    model = Quiz
    template_name = "apps/assessement/quizzes/detail.html"
    context_object_name = "quiz"

    def get_queryset(self):
        return Quiz.objects.filter(created_by=self.request.user).prefetch_related(
            "quiz_questions__question_content_type"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["quiz_questions"] = self.object.quiz_questions.select_related(
            "question_content_type"
        ).order_by("order")

        return context
