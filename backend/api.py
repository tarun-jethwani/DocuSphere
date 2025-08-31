import requests, re
from bs4 import BeautifulSoup
import trafilatura
from readability import Document
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl, URLRequest
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests, re
from bs4 import BeautifulSoup
from services.scrappers import scrape_text



app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

@app.post("/scrape")
def scrape_endpoint(req: URLRequest):
    text = scrape_text(req.url)
    print("\n--- Extracted Text ---\n")
    print(text)
    print("\n----------------------\n")
    return {"message": "Text extracted and printed to terminal", "length": len(text)}
