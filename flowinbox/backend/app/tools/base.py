from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid


class ToolInput(BaseModel):
    user_id: str = Field(..., description="UUID of authenticated user")


class ToolOutput(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
