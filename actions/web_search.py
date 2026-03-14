# actions/web_search.py
# CyberPorza — Optimized Web Search
# Primary: DuckDuckGo (Fast & Reliable)
# Summary: Gemini (Intelligence)

import json
import sys
import re
from pathlib import Path
from google import genai

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR        = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]

def _ddg_search(query: str, max_results: int = 8) -> list:
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title":   r.get("title", ""),
                    "snippet": r.get("body", r.get("snippet", "")),
                    "url":     r.get("href", r.get("link", "")),
                })
        return results
    except Exception as e:
        print(f"[PORZA-SEARCH] ⚠️ DDG Error: {e}")
        return []

def _summarize_with_gemini(query: str, search_data: list) -> str:
    """Uses Gemini to turn raw search results into a smart answer."""
    if not search_data:
        return "Sonuç bulunamadı kankam."

    context = "\n".join([f"- {r['title']}: {r['snippet']} ({r['url']})" for r in search_data])
    prompt = (
        f"Query: {query}\n\n"
        f"Search Results:\n{context}\n\n"
        "Based on these results, provide a concise, smart answer in Turkish. "
        "Address the user as 'kankam'. Max 3-4 sentences."
    )

    try:
        client = genai.Client(api_key=_get_api_key())
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"[PORZA-SEARCH] ⚠️ Summarization failed: {e}")
        return "\n".join([f"{r['title']}\n{r['snippet']}\n" for r in search_data[:3]])

def web_search(
    parameters:     dict,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params = parameters or {}
    query  = params.get("query", "").strip()
    
    if not query:
        return "Ne aramamı istediğini söylemedin kankam."

    if player:
        player.write_log(f"CYBER-SEARCH: Searching for: {query}")

    print(f"[PORZA-SEARCH] 🔍 Searching: {query!r}")

    # 1. Search with DuckDuckGo
    results = _ddg_search(query)
    
    # 2. Summarize with Gemini
    if results:
        print(f"[PORZA-SEARCH] ✅ Found {len(results)} results. Summarizing...")
        final_answer = _summarize_with_gemini(query, results)
        return final_answer
    else:
        return f"'{query}' hakkında hiçbir bilgi bulamadım kankam."