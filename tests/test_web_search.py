import urllib.request
import urllib.parse
import re

def search_web(query, max_results=3):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        
        snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', html)
        results = []
        for i in range(min(len(snippets), max_results)):
            clean_snip = re.sub(r'<[^<]+?>', '', snippets[i]).strip()
            if clean_snip:
                results.append(f"[{i+1}] {clean_snip}")
        return "\n".join(results) if results else "No specific web results returned."
    except Exception as e:
        return f"Web search error: {e}"

if __name__ == "__main__":
    print("SEARCH RESULTS:")
    print(search_web("Python 3.14 release date"))
