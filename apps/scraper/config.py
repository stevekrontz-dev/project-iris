"""
KSU Research - Scraper Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/ksu_research")

# KSU URLs
KSU_FACULTY_WEB = "https://facultyweb.kennesaw.edu"
KSU_DIRECTORY = "https://directory.kennesaw.edu"
KSU_CCSE_RESEARCH = "https://www.kennesaw.edu/ccse/research/faculty-research.php"

# Rate Limiting (be respectful to KSU servers)
REQUESTS_PER_SECOND = 1
REQUEST_DELAY = 1.0  # seconds between requests

# Scraping Settings
MAX_RETRIES = 3
TIMEOUT = 30  # seconds

# Output
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# User Agent
USER_AGENT = "KSU Research Platform Data Collection (research@kennesaw.edu)"

# Headers
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
