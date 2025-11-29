# src/utils.py
from googlesearch import search
from urllib.parse import urlparse

def find_career_page_url(company_name):
    """
    Searches Google for '[Company Name] careers' and returns the URL.
    """
    try:
        query = f"{company_name} careers jobs"
        # Perform search (limit to top 1 result for speed)
        results = list(search(query, num_results=1, lang="en"))
        
        if not results:
            return None, None
            
        career_url = results[0]
        
        # Deduce the homepage from the career URL
        parsed = urlparse(career_url)
        home_url = f"{parsed.scheme}://{parsed.netloc}"
        
        return home_url, career_url
    except Exception as e:
        print(f"  [!] Search failed for {company_name}: {e}")
        return None, None