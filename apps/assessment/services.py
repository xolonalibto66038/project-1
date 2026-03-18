# apps/assessment/services/grading.py

from django.db import transaction


class GradingService:

    @staticmethod
    @transaction.atomic
    def grade_attempt(attempt):
        """
        Auto-grade a quiz attempt.
        Only called if quiz.is_auto_gradable is True.
        """
        # from apps.assessment.models import Attempt  # adjust import

        if not attempt.quiz.is_auto_gradable:
            attempt.requires_manual_grading = True
            attempt.save(update_fields=["requires_manual_grading"])
            return

        total_awarded = 0
        all_correct = True

        answers = attempt.answers.select_related(
            "quiz_question__question_content_type"
        ).prefetch_related("quiz_question__question")

        for answer in answers:
            question = answer.quiz_question.question

            if question is None:
                continue

            result = question.grade(answer.submitted_answer)

            answer.awarded_points = result["awarded_points"]
            answer.is_correct = result["is_correct"]
            answer.feedback = result.get("feedback", "")
            answer.save(update_fields=["awarded_points", "is_correct", "feedback"])

            total_awarded += result["awarded_points"]
            if not result["is_correct"]:
                all_correct = False

        # Update attempt summary
        total_points = attempt.quiz.total_points or 1  # avoid division by zero
        attempt.score = total_awarded
        attempt.score_percentage = (total_awarded / total_points) * 100
        attempt.is_graded = True
        attempt.passed = attempt.score_percentage >= float(attempt.quiz.passing_score)
        attempt.save(
            update_fields=[
                "score",
                "score_percentage",
                "is_graded",
                "passed",
            ]
        )
