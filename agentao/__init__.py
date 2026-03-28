"""Agentao - A CLI chat agent with tools and skills support."""

import warnings
warnings.filterwarnings("ignore", message="urllib3.*or chardet.*doesn't match")

__version__ = "0.1.1"

from .agent import Agentao
from .skills import SkillManager

__all__ = ["Agentao", "SkillManager"]
