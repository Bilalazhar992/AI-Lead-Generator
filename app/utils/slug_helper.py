import re
import random
import string


def generate_slug(name: str) -> str:
    """Convert a business name to a URL-safe lowercase slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    return slug.strip("-")


def make_unique_slug(base: str) -> str:
    """Append a random 5-char alphanumeric suffix to a base slug."""
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return f"{base}-{suffix}"
