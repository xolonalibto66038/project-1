# recommendations/models.py

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.content.choices import DifficultyLevel, Term
from common.models import TimeStampModel


class ItemFeatureVector(TimeStampModel):
    """
    Flattened, precomputed feature snapshot for any curriculum item.

    Populated by signals when Resources or Courses are created/updated.
    Used by the recommendation engine for fast, join-free similarity scoring.

    One row per content item — enforced by the unique constraint on
    (content_type, object_id).

    Hierarchy path (most specific → least specific):
        Resource → course → chapter → grade_subject → subject → level
        Resource → course (standalone)  → grade_subject → subject → level
        Resource → grade_subject (test/exam) → subject → level
        Course   → chapter → grade_subject → subject → level
        Course   → grade_subject (standalone) → subject → level
    """

    # ── Generic FK ────────────────────────────────────────────────────────────
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("Content Type"),
        db_index=True,
    )
    object_id = models.UUIDField(
        db_index=True,
        verbose_name=_("Object ID"),
    )
    content_object = GenericForeignKey("content_type", "object_id")

    # ── Flattened curriculum hierarchy ────────────────────────────────────────
    level_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_("Level ID"),
        help_text=_("Cached level PK (Primaire / Moyen / Secondaire / Université)."),
    )
    grade_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_("Grade ID"),
        help_text=_("Cached grade PK (e.g. 3AM, 1AS)."),
    )
    subject_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_("Subject ID"),
        help_text=_("Cached subject PK (e.g. Mathématiques, Physique)."),
    )
    specialty_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_("Specialty ID"),
        help_text=_(
            "Cached specialty (filière) PK. NULL means the item applies to "
            "all specialties of this grade."
        ),
    )
    course_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_("Course ID"),
        help_text=_("Cached course PK. NULL for subject-level items (test/exam)."),
    )

    # ── Item-specific metadata ────────────────────────────────────────────────
    item_type = models.CharField(
        max_length=20,
        choices=[
            # Course-level types
            ("course", _("Course")),
            # Resource types — mirrors ResourceType choices
            ("lesson", _("Lesson")),
            ("exercise", _("Exercise")),
            ("homework", _("Homework")),
            ("test", _("Test")),
            ("exam", _("Exam")),
        ],
        verbose_name=_("Item Type"),
        help_text=_("Discriminator used by the engine to boost same-type matches."),
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DifficultyLevel.choices,  # easy / medium / hard — matches Resource
        blank=True,
        null=True,
        verbose_name=_("Difficulty"),
        help_text=_("Cached difficulty level. NULL when not applicable."),
    )
    term = models.CharField(
        max_length=10,
        choices=Term.choices,  # T1 / T2 / T3 — matches Chapter & Course
        blank=True,
        null=True,
        verbose_name=_("Term"),
        help_text=_("Cached school term. NULL when not applicable."),
    )

    # ── Housekeeping ──────────────────────────────────────────────────────────
    last_synced_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last Synced At"),
        help_text=_(
            "Timestamp of the last sync by the recommendation pipeline. "
            "Distinct from updated_at (inherited from TimeStampModel) which "
            "tracks Django model saves."
        ),
    )

    class Meta:
        verbose_name = _("Item Feature Vector")
        verbose_name_plural = _("Item Feature Vectors")
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id"],
                name="unique_item_feature_vector",
            ),
        ]
        indexes = [
            # Primary lookup path used by _get_candidate_vectors()
            models.Index(
                fields=["level_id", "grade_id", "subject_id"],
                name="ifv_level_grade_subject_idx",
            ),
            # Specialty filter (Secondaire items)
            models.Index(
                fields=["specialty_id"],
                name="ifv_specialty_idx",
            ),
            # Engine pre-filter by type
            models.Index(
                fields=["item_type"],
                name="ifv_item_type_idx",
            ),
            # Term-aware recommendations
            models.Index(
                fields=["term"],
                name="ifv_term_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.content_type.model} | {self.object_id} | "
            f"{self.item_type} | {self.term or '—'}"
        )
