from django.db import models
from django.utils.translation import gettext_lazy as _

from .question import BaseQuestion


class TrueFalseQuestion(BaseQuestion):
    correct_answer = models.BooleanField()

    explanation = models.TextField(blank=True)

    class Meta:
        db_table = "true_false_questions"
        verbose_name = _("True / False Question")
        verbose_name_plural = _("True/False Questions")
        indexes = [
            models.Index(fields=["question_type"]),
            models.Index(fields=["difficulty_level"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_by"]),
        ]

    def save(self, *args, **kwargs):
        self.question_type = "tf"
        super().save(*args, **kwargs)

    def get_question_type(self):
        return "true_false_question"  # ou une autre logique

    def auto_grade(self, answer: bool):
        return answer == self.correct_answer

    def grade(self, answer):
        if not isinstance(answer, bool):
            return {
                "awarded_points": 0,
                "is_correct": False,
                "feedback": "Invalid answer format.",
            }

        is_correct = answer == self.correct_answer
        awarded = self.points if is_correct else 0

        return {
            "awarded_points": awarded,
            "is_correct": is_correct,
            "feedback": self.explanation if self.explanation else "",
        }
