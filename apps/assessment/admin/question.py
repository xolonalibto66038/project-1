from django.contrib import admin
from django.utils.html import format_html


class BaseQuestionAdmin(admin.ModelAdmin):
    """
    Base admin class for all question types
    """

    list_display = [
        "title",
        "question_type_display",
        "points",
        "difficulty_level",
        "created_by",
        "is_active",
        "created_at",
    ]
    list_filter = ["difficulty_level", "is_active", "created_at", "created_by"]
    search_fields = ["title", "question_text"]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        ("Question Content", {"fields": ("title", "question_text")}),
        ("Settings", {"fields": ("points", "difficulty_level", "is_active")}),
        (
            "Metadata",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def question_type_display(self, obj):
        """Display question type with colored badge"""
        colors = {
            "textquestion": "#28a745",  # Green
            "multiplechoicequestion": "#007bff",  # Blue
            "truefalsequestion": "#ffc107",  # Yellow
        }
        question_type = obj.get_question_type()
        color = colors.get(question_type, "#6c757d")

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            question_type.replace("question", "").title(),
        )

    question_type_display.short_description = "Type"

    def save_model(self, request, obj, form, change):
        """Auto-set created_by to current user if not set"""
        if not change:  # Only on creation
            if hasattr(request.user, "teacherprofile"):
                obj.created_by = request.user.teacherprofile
        #     else:
        #         # Optional: raise or silently skip
        #         raise ValueError("Current user does not have a TeacherProfile.")
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related("created_by")


# # If you want to register BaseQuestion as well (for viewing all question types together)
# class AllQuestionsAdmin(admin.ModelAdmin):
#     """
#     Admin to view all question types in one place
#     """

#     list_display = [
#         "title",
#         "question_type_display",
#         "points",
#         "difficulty_level",
#         "created_by",
#         "created_at",
#     ]
#     list_filter = ["difficulty_level", "created_at"]
#     search_fields = ["title", "question_text"]
#     readonly_fields = ["created_at", "updated_at", "created_by"]

#     def has_add_permission(self, request):
#         """Disable add permission since this is just for viewing"""
#         return False

#     def has_change_permission(self, request, obj=None):
#         """Disable change permission since this is just for viewing"""
#         return False

#     def question_type_display(self, obj):
#         """Display question type"""
#         return obj.get_question_type().replace("question", "").title()

#     question_type_display.short_description = "Type"

#     def get_queryset(self, request):
#         """Get all question types - this would need to be implemented
#         differently since BaseQuestion is abstract"""
#         # This is a placeholder - you'd need to combine querysets
#         # from all concrete question models
#         return TextQuestion.objects.all()


# # Uncomment if you want to see all questions in one admin view
# admin.site.register(BaseQuestion, AllQuestionsAdmin)
