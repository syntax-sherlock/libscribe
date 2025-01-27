from urllib.parse import urlparse
import re

def extract_owner_repo(github_url: str) -> tuple[str, str]:
    """Extract owner and repo from GitHub URL with validation."""
    if not re.match(r"^https?://github\.com/[^/]+/[^/]+/?", github_url):
        raise ValueError("Invalid GitHub repository URL format")
    
    path = urlparse(github_url).path.strip("/")
    parts = path.split("/")
    return parts[0], parts[1].replace(".git", "")
