"""Shared base model configuration for canonical OVIS state models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OvisBaseModel(BaseModel):
    """Base model for canonical OVIS schema objects."""

    model_config = ConfigDict(extra="forbid")


Timestamp = datetime
