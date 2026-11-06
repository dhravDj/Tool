"""Sample Python module for code intelligence testing."""

import os
import sys
from typing import List, Optional
import requests
from pydantic import BaseModel

API_KEY = "dummy_hardcoded_secret_token_12345"

class UserAccount(BaseModel):
    """Represents a user account in the system."""
    user_id: int
    username: str
    is_active: bool = True

    def get_display_name(self) -> str:
        """Return formatted display name."""
        return f"User: {self.username}"

def fetch_user_data(user_id: int) -> Optional[UserAccount]:
    """Fetch user data from remote service."""
    if user_id <= 0:
        return None
    try:
        response = requests.get(f"https://api.example.com/users/{user_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return UserAccount(**data)
    except Exception:
        pass
    return None
