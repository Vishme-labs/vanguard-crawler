import re
from urllib.parse import urlparse, urljoin

def normalize_url(base, link):
    # Remove fragments, whitespace; convert relative to absolute
    if not link:
        return None
    link = link.strip()
    if link.startswith("mailto:") or link.startswith("tel:"):
        return None
    absolute = urljoin(base, link)
    parsed = urlparse(absolute)
    # Only allow http(s)
    if parsed.scheme not in ("http", "https"):
        return None
    # strip fragment
    normalized = parsed._replace(fragment="").geturl()
    return normalized

def same_domain(a, b):
    pa = urlparse(a)
    pb = urlparse(b)
    return pa.netloc == pb.netloc

PARAM_RE = re.compile(r"[?&]([a-zA-Z0-9_\-]+)=")
def extract_params(url):
    return list({m.group(1) for m in PARAM_RE.finditer(url)})
