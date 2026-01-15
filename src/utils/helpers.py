"""Utility helper functions."""
import re
from datetime import datetime, timedelta
from typing import Optional
import httpx


def validate_email_format(email: str) -> bool:
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def calculate_due_date(days_from_now: int) -> datetime:
    """Calculate a due date from current time."""
    return datetime.utcnow() + timedelta(days=days_from_now)


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO string."""
    if dt is None:
        return None
    return dt.isoformat()


def parse_datetime(dt_string: str) -> datetime:
    """Parse ISO datetime string."""
    return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))


async def fetch_external_data(url: str, timeout: float = 10.0) -> dict:
    """Fetch data from external URL using httpx.

    Uses httpx which has known CVEs in older versions.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize and truncate a string."""
    # Remove leading/trailing whitespace
    cleaned = value.strip()
    # Truncate if necessary
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def generate_slug(title: str) -> str:
    """Generate a URL-friendly slug from a title."""
    # Convert to lowercase
    slug = title.lower()
    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug
