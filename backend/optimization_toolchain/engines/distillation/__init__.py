"""
知识蒸馏引擎模块
支持标准蒸馏、自蒸馏、在线蒸馏等多种蒸馏方式
"""
from .distiller import (
    KnowledgeDistiller,
    DistillationConfig,
    DistillationResult,
    DistillationMode,
    DistillationLossType,
)
from .teacher import TeacherModel, TeacherConfig
from .student import StudentModel, StudentConfig

__all__ = [
    "KnowledgeDistiller",
    "DistillationConfig",
    "DistillationResult",
    "DistillationMode",
    "DistillationLossType",
    "TeacherModel",
    "TeacherConfig",
    "StudentModel",
    "StudentConfig",
]
