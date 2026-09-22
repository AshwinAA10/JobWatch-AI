"""Deterministic normalization helpers for job titles, locations, URLs, and descriptions."""

import html
import re
import unicodedata
from typing import Optional, Set
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# Common tracking / referrer query parameters safe to prune
TRACKING_QUERY_PARAMS: Set[str] = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ref",
    "gh_src",
    "source",
    "lever-origin",
    "lever-source",
    "mode",
    "iis",
    "iisn",
    "fbclid",
    "gclid",
    "msclkid",
    "twclid",
    "tracking_id",
    "trackingid",
    "tracker",
    "from",
}

# Standardized city aliases
CITY_ALIASES = {
    "bangalore": "bengaluru",
    "gurgaon": "gurugram",
    "bombay": "mumbai",
    "calcutta": "kolkata",
    "madras": "chennai",
    "nyc": "new york",
    "new york city": "new york",
    "sf": "san francisco",
    "sf bay area": "san francisco",
    "san francisco bay area": "san francisco",
    "bay area": "san francisco",
}

# Standardized seniority levels
SENIORITY_PATTERNS = [
    ("director", re.compile(r"\b(director|head of|vp|vice president)\b", re.IGNORECASE)),
    ("manager", re.compile(r"\b(manager|engineering manager)\b", re.IGNORECASE)),
    ("principal", re.compile(r"\b(principal|distinguished|fellow)\b", re.IGNORECASE)),
    ("lead", re.compile(r"\b(lead|tech lead|team lead)\b", re.IGNORECASE)),
    ("staff", re.compile(r"\b(staff)\b", re.IGNORECASE)),
    ("senior", re.compile(r"\b(senior|sr\.?|iii|iv)\b", re.IGNORECASE)),
    ("mid", re.compile(r"\b(mid|intermediate|ii)\b", re.IGNORECASE)),
    ("junior", re.compile(r"\b(junior|jr\.?|associate|entry level|entry-level|graduate|i)\b", re.IGNORECASE)),
    ("intern", re.compile(r"\b(intern|internship|co[\s\-]*op|coop|student|trainee)\b", re.IGNORECASE)),
]


def clean_text(text: Optional[str]) -> str:
    """Strip HTML markup, decode entities, collapse whitespace, and lowercase."""
    if not text:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", text)
    # Decode HTML entities
    cleaned = html.unescape(cleaned)
    # Unicode NFKC normalization
    cleaned = unicodedata.normalize("NFKC", cleaned)
    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.lower()


def normalize_title(title: str) -> str:
    """Clean and normalize a job title while strictly preserving seniority and role distinctions.
    
    Examples:
        'Senior Software Engineer - Backend' -> 'senior software engineer backend'
        'Software Engineer II (Remote)' -> 'software engineer ii remote'
    """
    if not title:
        return ""
    # Unicode NFKC
    normalized = unicodedata.normalize("NFKC", title).lower()
    # Replace punctuation and separators with single spaces
    normalized = re.sub(r"[\-_/\\|()\[\],&:+]", " ", normalized)
    # Collapse multiple whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def extract_seniority(title: str) -> Optional[str]:
    """Extract canonical seniority tier from job title if present."""
    if not title:
        return None
    cleaned = f" {normalize_title(title)} "
    for level, pattern in SENIORITY_PATTERNS:
        if pattern.search(cleaned):
            return level
    return None


def normalize_location(location: Optional[str]) -> Optional[str]:
    """Normalize location string, canonicalizing city aliases and whitespace.
    
    Examples:
        'Bangalore, India' -> 'bengaluru, india'
        'Remote - US' -> 'remote us'
    """
    if not location:
        return None
    cleaned = clean_text(location)
    # Replace punctuation except commas with spaces
    cleaned = re.sub(r"[\-_/\\|()\[\];]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Map known city names
    tokens = cleaned.split(",")
    normalized_parts = []
    for part in tokens:
        p = part.strip()
        p = CITY_ALIASES.get(p, p)
        normalized_parts.append(p)
    return ", ".join(normalized_parts) if normalized_parts else cleaned


def normalize_url(url: Optional[str]) -> Optional[str]:
    """Normalize a URL by canonicalizing scheme, host, trailing slash, and removing tracking params.
    
    Crucially preserves job ID and requisition parameters.
    """
    if not url:
        return None
    try:
        parsed = urlparse(url.strip())
        if not parsed.scheme or not parsed.netloc:
            return url.strip()

        # Lowercase scheme and netloc (strip standard ports)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        if netloc.endswith(":80") and scheme == "http":
            netloc = netloc[:-3]
        elif netloc.endswith(":443") and scheme == "https":
            netloc = netloc[:-4]

        # Normalize path: strip trailing slash unless root path
        path = parsed.path
        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/")

        # Filter out tracking query parameters
        query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
        filtered_pairs = [
            (k, v)
            for k, v in query_pairs
            if k.lower() not in TRACKING_QUERY_PARAMS
        ]
        filtered_pairs.sort(key=lambda x: x[0])
        new_query = urlencode(filtered_pairs)

        return urlunparse((scheme, netloc, path, parsed.params, new_query, ""))
    except Exception:
        return url.strip()
