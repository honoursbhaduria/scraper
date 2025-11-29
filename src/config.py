# src/config.py

# Limits
MAX_JOBS_TOTAL = 205         # Stop after finding this many jobs
JOBS_PER_COMPANY = 3         # Only scrape top 3 jobs per company

# Browser Settings
# We set this to False so you can see the browser and solve CAPTCHAs manually if needed
HEADLESS = False             
TIMEOUT_MS = 30000           # Increased to 30 seconds to fix timeout errors

# Updated to match your Debian Linux environment
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'

# Keywords to identify generic job links if no ATS is found
JOB_KEYWORDS = [
    'engineer', 'manager', 'developer', 'analyst', 'intern', 
    'specialist', 'consultant', 'lead', 'senior', 'junior', 'associate'
]