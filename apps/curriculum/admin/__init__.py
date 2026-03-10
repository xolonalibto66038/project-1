from .grade import GradeAdmin, GradeInline
from .level import LevelAdmin
from .specialty import SpecialtyAdmin, SpecialtyInline
from .subject import SubjectAdmin
from .subject_grade import GradeSubjectAdmin, GradeSubjectInline

__all__ = [
    "LevelAdmin",
    "GradeAdmin",
    "SubjectAdmin",
    "GradeInline",
    "SpecialtyAdmin",
    "SpecialtyInline",
    "GradeSubjectAdmin",
    "GradeSubjectInline",
]
