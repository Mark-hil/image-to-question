from typing import Any, Dict, Optional

class AppError(Exception):
    """
    Base exception class for application errors.
    This ensures the frontend receives a predictable JSON error structure.
    """
    def __init__(
        self, 
        error_code: str, 
        message: str, 
        status_code: int = 400, 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
