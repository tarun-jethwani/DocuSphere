# app.py

# --- third-party ---
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from readability import Document
import trafilatura

app = FastAPI()

class URLRequest(BaseModel):
    url: HttpUrl  # requires http/https in the JSON

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def fetch_html(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        return r.text
    except requests.RequestException as e:
        print(f"[fetch] error: {e}")
        raise HTTPException(status_code=400, detail=f"Fetch failed: {e}")

def trafilatura_extract(html: str, url: str) -> str | None:
    text = trafilatura.extract(
        html,
        url=url,  # must be a plain string
        include_comments=False,
        include_tables=False,
        favor_precision=True,
    )
    return text.strip() if text else None

def readability_extract(html: str) -> str | None:
    try:
        doc = Document(html)
        title = (doc.short_title() or "").strip()
        summary_html = doc.summary(html_partial=True)
        soup = BeautifulSoup(summary_html, "html.parser")

        parts = []
        for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
            t = tag.get_text(" ", strip=True)
            if not t:
                continue
            parts.append(f"- {t}" if tag.name == "li" else t)

        body = "\n".join(parts).strip()
        if not body:
            return None
        return f"{title}\n\n{body}" if title else body
    except Exception as e:
        print(f"[readability] error: {e}")
        return None

def scrape_text(url_in) -> str:
    # Normalize HttpUrl/any -> str
    url = str(url_in)

    html = fetch_html(url)

    # 1) Try trafilatura
    text = trafilatura_extract(html, url)
    if text:
        print("[extractor] trafilatura used")
        return text

    # 2) Fallback to readability
    text = readability_extract(html)
    if text:
        print("[extractor] readability fallback used")
        return text

    # 3) Heuristic fallback: H1 + largest text block
    print("[extractor] using heuristic fallback")
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "svg", "img", "form", "iframe", "header", "footer", "nav", "aside"]):
        t.decompose()

    title_el = soup.select_one("h1") or soup.title
    title = title_el.get_text(strip=True) if title_el else ""

    blocks = soup.find_all(["article", "section", "div"])
    node = max(blocks, key=lambda b: len(b.get_text(" ", strip=True)), default=soup)

    parts = []
    for tag in node.find_all(["h1", "h2", "h3", "p", "li"]):
        t = tag.get_text(" ", strip=True)
        if t:
            parts.append(f"- {t}" if tag.name == "li" else t)
    body = "\n".join(parts).strip()

    if body:
        return f"{title}\n\n{body}" if title else body

    raise HTTPException(status_code=422, detail="Could not extract main content (all extractors failed)")

@app.post("/scrape")
def scrape_endpoint(req: URLRequest):
    text = scrape_text(str(req.url))  # ensure plain string
    print("\n--- Extracted Text ---\n")
    print(text)
    print("\n----------------------\n")
    return {"message": "Text extracted and printed to terminal", "length": len(text)}
