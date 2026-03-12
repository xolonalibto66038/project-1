from itertools import chain
from operator import attrgetter

from django.views.generic import TemplateView
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)

from apps.authentication.mixins import TeacherRequiredMixin

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
    BaseQuestion,
    Choice,
    EssayQuestion,
    MultipleChoiceQuestion,
    Quiz,
    QuizQuestion,
    TrueFalseQuestion,
)


class QuestionListView(TeacherRequiredMixin, ListView):
    template_name = "apps/assessement/questions/list.html"
    context_object_name = "questions"
    paginate_by = 10

    def get_queryset(self):
        teacher = self.request.user
        search = self.request.GET.get("search", "").strip()
        qtype = self.request.GET.get("type", "").strip()

        search_filter = Q()
        if search:
            search_filter = Q(title__icontains=search) | Q(
                question_text__icontains=search
            )

        type_models = {
            "essay": EssayQuestion,
            "tf": TrueFalseQuestion,
            "mcq": MultipleChoiceQuestion,
        }

        if qtype and qtype in type_models:
            querysets = [
                type_models[qtype]
                .objects.filter(created_by=teacher)
                .filter(search_filter)
            ]
        else:
            querysets = [
                EssayQuestion.objects.filter(created_by=teacher).filter(search_filter),
                TrueFalseQuestion.objects.filter(created_by=teacher).filter(
                    search_filter
                ),
                MultipleChoiceQuestion.objects.filter(created_by=teacher).filter(
                    search_filter
                ),
            ]

        return sorted(chain(*querysets), key=attrgetter("created_at"), reverse=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_search"] = self.request.GET.get("search", "")
        context["current_type"] = self.request.GET.get("type", "")
        return context


class EssayQuestionCreateView(TeacherRequiredMixin, CreateView):
    model = EssayQuestion
    form_class = EssayQuestionForm
    template_name = "apps/assessement/questions/essay.html"
    success_url = reverse_lazy("assessment:question:question-list")

    def form_valid(self, form):
        question = form.save(commit=False)
        question.created_by = self.request.user
        question.save()
        form.save_m2m()

        messages.success(self.request, "Essay question created successfully.")
        return super().form_valid(form)


class EssayQuestionUpdateView(TeacherRequiredMixin, UpdateView):
    model = EssayQuestion
    form_class = EssayQuestionForm
    template_name = "apps/assessement/questions/essay.html"
    success_url = reverse_lazy("assessment:question:question-list")

    def get_queryset(self):
        # Prevent editing other teachers' questions
        return EssayQuestion.objects.filter(created_by=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Essay question updated successfully.")
        return super().form_valid(form)


class TrueFalseQuestionCreateView(TeacherRequiredMixin, CreateView):
    model = TrueFalseQuestion
    form_class = TrueFalseQuestionForm
    template_name = "apps/assessement/questions/tf.html"
    success_url = reverse_lazy("assessment:question:question-list")

    def form_valid(self, form):
        question = form.save(commit=False)
        question.created_by = self.request.user
        question.save()
        form.save_m2m()

        messages.success(self.request, "True/False question created successfully.")
        return super().form_valid(form)


class TrueFalseQuestionUpdateView(TeacherRequiredMixin, UpdateView):
    model = TrueFalseQuestion
    form_class = TrueFalseQuestionForm
    template_name = "apps/assessement/questions/tf.html"
    success_url = reverse_lazy("assessment:question:question-list")

    def get_queryset(self):
        return TrueFalseQuestion.objects.filter(created_by=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "True/False question updated successfully.")
        return super().form_valid(form)


class MultipleChoiceQuestionCreateView(TeacherRequiredMixin, CreateView):
    model = MultipleChoiceQuestion
    form_class = MultipleChoiceQuestionForm
    template_name = "apps/assessement/questions/mcq.html"
    success_url = reverse_lazy("assessment:question:question-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["formset"] = ChoiceCreateFormSet(self.request.POST)
        else:
            context["formset"] = ChoiceCreateFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]

        if not formset.is_valid():
            return self.form_invalid(form)

        # ✅ Count correct choices BEFORE saving
        correct_count = 0

        for f in formset.cleaned_data:
            if not f.get("DELETE", False) and f.get("is_correct", False):
                correct_count += 1

        if correct_count == 0:
            formset._non_form_errors = formset.error_class(
                ["At least one correct choice is required."]
            )
            return self.form_invalid(form)

        if not form.cleaned_data.get("allow_multiple") and correct_count > 1:
            formset._non_form_errors = formset.error_class(
                ["Only one correct choice allowed when allow_multiple=False."]
            )
            return self.form_invalid(form)

        # ✅ Save everything safely
        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.created_by = self.request.user
            self.object.save()
            form.save_m2m()

            formset.instance = self.object
            formset.save()

        messages.success(self.request, "MCQ question created successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class MultipleChoiceQuestionUpdateView(TeacherRequiredMixin, UpdateView):
    model = MultipleChoiceQuestion
    form_class = MultipleChoiceQuestionForm
    template_name = "apps/assessement/questions/mcq.html"
    success_url = reverse_lazy("assessment:question:question-list")

    def get_queryset(self):
        return MultipleChoiceQuestion.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["formset"] = ChoiceFormSet(
                self.request.POST,
                instance=self.object,
            )
        else:
            context["formset"] = ChoiceFormSet(
                instance=self.object,  # queryset=Choice.objects.none()
            )

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        form = self.get_form()
        formset = ChoiceFormSet(request.POST, instance=self.object)

        if form.is_valid() and formset.is_valid():

            # Count correct answers (excluding deleted ones)
            correct_count = 0
            for f in formset.cleaned_data:
                if not f.get("DELETE", False) and f.get("is_correct", False):
                    correct_count += 1

            # Validation rules
            if correct_count == 0:
                formset._non_form_errors = formset.error_class(
                    ["At least one correct choice is required."]
                )
                return self.render_to_response(
                    self.get_context_data(form=form, formset=formset)
                )

            if not form.cleaned_data.get("allow_multiple") and correct_count > 1:
                formset._non_form_errors = formset.error_class(
                    ["Only one correct choice allowed when allow_multiple=False."]
                )
                return self.render_to_response(
                    self.get_context_data(form=form, formset=formset)
                )

            # Save safely
            with transaction.atomic():
                self.object = form.save()
                formset.save()

            messages.success(request, "MCQ question updated successfully.")
            return redirect(self.success_url)

        # If invalid, re-render with errors
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )


class QuestionTypeSelectView(TemplateView):
    template_name = "apps/assessement/questions/question_type_select.html"