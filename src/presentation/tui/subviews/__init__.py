"""TUI子界面模块"""

from .base import BaseSubview
from .analytics import AnalyticsSubview
from .visualization import VisualizationSubview
from .system import SystemSubview
from .errors import ErrorFeedbackSubview

__all__ = [
    "BaseSubview",
    "AnalyticsSubview",
    "VisualizationSubview",
    "SystemSubview",
    "ErrorFeedbackSubview"
]