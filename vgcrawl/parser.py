from bs4 import BeautifulSoup
from .utils import normalize_url

def extract_links(base_url, html):
    soup = BeautifulSoup(html, "lxml")
    tags = []
    for tag in soup.find_all(["a", "link", "script", "img", "iframe", "form"]):
        if tag.name == "a" and tag.get("href"):
            tags.append(tag.get("href"))
        elif tag.name in ("script", "img", "iframe") and tag.get("src"):
            tags.append(tag.get("src"))
        elif tag.name == "link" and tag.get("href"):
            tags.append(tag.get("href"))
        elif tag.name == "form" and tag.get("action"):
            tags.append(tag.get("action"))
    results = []
    for href in tags:
        n = normalize_url(base_url, href)
        if n:
            results.append(n)
    return results
