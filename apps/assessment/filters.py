from django.contrib import admin
from django.db import models


class LengthRangeFilter(admin.SimpleListFilter):
    """Custom filter for question length ranges"""

    title = "Answer Length Range"
    parameter_name = "length_range"

    def lookups(self, request, model_admin):
        return (
            ("short", "Short (1-100 chars)"),
            ("medium", "Medium (101-500 chars)"),
            ("long", "Long (501-1000 chars)"),
            ("essay", "Essay (1000+ chars)"),
            ("flexible", "Very Flexible (500+ char range)"),
        )

    def queryset(self, request, queryset):
        if self.value() == "short":
            return queryset.filter(max_length__lte=100)
        elif self.value() == "medium":
            return queryset.filter(max_length__gt=100, max_length__lte=500)
        elif self.value() == "long":
            return queryset.filter(max_length__gt=500, max_length__lte=1000)
        elif self.value() == "essay":
            return queryset.filter(max_length__gt=1000)
        elif self.value() == "flexible":
            return queryset.extra(where=["max_length - min_length >= 500"])


class AttemptGradeFilter(admin.SimpleListFilter):
    """Custom filter for attempt grades"""

    title = "Grade"
    parameter_name = "grade"

    def lookups(self, request, model_admin):
        return (
            ("A", "A (90-100%)"),
            ("B", "B (80-89%)"),
            ("C", "C (70-79%)"),
            ("D", "D (60-69%)"),
            ("F", "F (0-59%)"),
            ("passed", "Passed"),
            ("failed", "Failed"),
        )

    def queryset(self, request, queryset):
        if self.value() == "A":
            return queryset.filter(score_percentage__gte=90)
        elif self.value() == "B":
            return queryset.filter(score_percentage__gte=80, score_percentage__lt=90)
        elif self.value() == "C":
            return queryset.filter(score_percentage__gte=70, score_percentage__lt=80)
        elif self.value() == "D":
            return queryset.filter(score_percentage__gte=60, score_percentage__lt=70)
        elif self.value() == "F":
            return queryset.filter(score_percentage__lt=60)
        elif self.value() == "passed":
            return queryset.filter(
                score_percentage__gte=models.F("quiz__passing_score")
            )
        elif self.value() == "failed":
            return queryset.filter(score_percentage__lt=models.F("quiz__passing_score"))
