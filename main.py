import asyncio
import pandas as pd
from playwright.async_api import async_playwright
from src.scrapers import duckduckgo_search, determine_and_scrape, extract_home_page
# UPDATED: Importing settings from config to ensure consistency
from src.config import MAX_JOBS_TOTAL, USER_AGENT, HEADLESS

# --- CONFIG ---
INPUT_FILE = 'data/raw_data.xlsx'
OUTPUT_FILE = 'data/submission.xlsx'
USER_DATA_DIR = "./chrome_profile" 

async def main():
    try:
        df = pd.read_excel(INPUT_FILE)
        companies = df.iloc[:, 0].dropna().tolist()
        print(f"Loaded {len(companies)} companies.")
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
        return

    results = []
    total_jobs_found = 0

    async with async_playwright() as p:
        print("Launching Chromium...")
        
        # UPDATED: Using variables from src/config.py
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR, 
            headless=HEADLESS,       # Uses the value from config.py
            args=["--start-maximized"],
            no_viewport=True,
            user_agent=USER_AGENT    # Uses the Linux User Agent from config.py
        )
        page = context.pages[0]

        for company in companies:
            if total_jobs_found >= MAX_JOBS_TOTAL:
                print("\n--- Target Reached (200+ Jobs) ---")
                break
                
            print(f"\nProcessing: {company}")
            
            # 1. Search Data
            linkedin_url = await duckduckgo_search(page, f"site:linkedin.com/company {company}")
            career_url = await duckduckgo_search(page, f"{company} careers")
            
            if not career_url:
                print("  -> Skipped (No career page)")
                continue

            home_page = extract_home_page(career_url)

            # 2. Scrape Page
            # Returns tuple: (list_of_jobs, description_string)
            jobs, description = await determine_and_scrape(page, career_url)
            print(f"  -> Scraped {len(jobs)} jobs.")
            
            total_jobs_found += len(jobs)
            
            # 3. Create Row with EXACT Column Names
            row = {
                "Company Name": company,
                "Company Description": description,
                "Website URL": home_page,
                "Linkedin URL": linkedin_url if linkedin_url else "N/A",
                "Careers Page URL": career_url,
                "Job listings page URL": career_url, 
                
                # Default values (Empty)
                "job post1 URL": "", "job post1 title": "",
                "job post2 URL": "", "job post2 title": "",
                "job post3 URL": "", "job post3 title": ""
            }

            # Fill Job Slots dynamically
            if len(jobs) >= 1:
                row["job post1 URL"] = jobs[0]['Url']
                row["job post1 title"] = jobs[0]['Title']
            
            if len(jobs) >= 2:
                row["job post2 URL"] = jobs[1]['Url']
                row["job post2 title"] = jobs[1]['Title']
                
            if len(jobs) >= 3:
                row["job post3 URL"] = jobs[2]['Url']
                row["job post3 title"] = jobs[2]['Title']

            results.append(row)

        await context.close()

    # 4. Save Final Excel
    print(f"\nSaving {len(results)} rows to {OUTPUT_FILE}...")
    with pd.ExcelWriter(OUTPUT_FILE) as writer:
        if results:
            # Ensure columns are in the exact order you asked for
            cols = [
                "Company Name", "Company Description", "Website URL", "Linkedin URL", 
                "Careers Page URL", "Job listings page URL", 
                "job post1 URL", "job post1 title", 
                "job post2 URL", "job post2 title", 
                "job post3 URL", "job post3 title"
            ]
            # Use 'reindex' to ensure all columns exist even if data is missing, then select order
            df_final = pd.DataFrame(results)
            # Add missing columns if any
            for c in cols:
                if c not in df_final.columns:
                    df_final[c] = ""
            
            df_final[cols].to_excel(writer, sheet_name='Data', index=False)
        else:
            pd.DataFrame(["No data found"]).to_excel(writer, sheet_name='Data')
            
        # Methodology
        method_data = [
            {"Step": "1. Discovery", "Detail": "Used DuckDuckGo to identify Linkedin and Career URLs."},
            {"Step": "2. Enrichment", "Detail": "Extracted Meta-Description and Home Page URL from Career Page."},
            {"Step": "3. Formatting", "Detail": "Mapped scraped data to specific 12-column schema required by assignment."}
        ]
        pd.DataFrame(method_data).to_excel(writer, sheet_name='Methodology', index=False)
        
    print("Done! Check data/submission.xlsx")

if __name__ == "__main__":
    asyncio.run(main()) 