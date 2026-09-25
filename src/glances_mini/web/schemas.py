"""Pydantic schemas for API serialization and request validation."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ProcessResponse(BaseModel):
    """Schema representing a single process in API responses."""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_rss_bytes: int
    disk_read_bytes_sec: float = 0.0
    disk_write_bytes_sec: float = 0.0

    # Pydantic v2 configuration to allow reading data directly from OOP class objects
    model_config = {"from_attributes": True}


class SystemResponse(BaseModel):
    """Schema representing overall system metrics and top processes."""
    timestamp: float
    cpu_percent_total: float
    memory_percent: float
    memory_used_bytes: int
    memory_total_bytes: int
    processes: List[ProcessResponse]
    is_congested: bool

    model_config = {"from_attributes": True}


class ProcessQueryParams(BaseModel):
    """Query parameters for filtering/sorting processes."""
    limit: int = Field(default=10, ge=1, le=100)
    sort_by: Literal["cpu", "memory"] = Field(default="cpu")