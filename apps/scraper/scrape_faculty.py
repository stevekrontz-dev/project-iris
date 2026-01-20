"""
KSU Research - Faculty Web Scraper
Scrapes faculty profiles from facultyweb.kennesaw.edu

Usage:
    python scrape_faculty.py --letter A
    python scrape_faculty.py --all
"""
import argparse
import json
import re
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm

from config import (
    KSU_FACULTY_WEB,
    DEFAULT_HEADERS,
    REQUEST_DELAY,
    MAX_RETRIES,
    TIMEOUT,
    OUTPUT_DIR,
)

# Configure logging
logger.add(
    Path(OUTPUT_DIR) / "scraper.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO"
)


class FacultyProfile:
    """Represents a scraped faculty profile"""
    def __init__(self):
        self.net_id: Optional[str] = None
        self.name: Optional[str] = None
        self.first_name: Optional[str] = None
        self.last_name: Optional[str] = None
        self.title: Optional[str] = None
        self.department: Optional[str] = None
        self.college: Optional[str] = None
        self.email: Optional[str] = None
        self.phone: Optional[str] = None
        self.office: Optional[str] = None
        self.photo_url: Optional[str] = None
        self.bio: Optional[str] = None
        self.research_interests: list[str] = []
        self.education: list[str] = []
        self.publications: list[str] = []
        self.courses: list[str] = []
        self.profile_url: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "net_id": self.net_id,
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "title": self.title,
            "department": self.department,
            "college": self.college,
            "email": self.email,
            "phone": self.phone,
            "office": self.office,
            "photo_url": self.photo_url,
            "bio": self.bio,
            "research_interests": self.research_interests,
            "education": self.education,
            "publications": self.publications,
            "courses": self.courses,
            "profile_url": self.profile_url,
        }


class KSUFacultyScraper:
    """Scraper for KSU Faculty Web directory"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def _request(self, url: str, retries: int = MAX_RETRIES) -> Optional[BeautifulSoup]:
        """Make a request with retries and rate limiting"""
        for attempt in range(retries):
            try:
                logger.debug(f"Fetching: {url}")
                response = self.session.get(url, timeout=TIMEOUT)
                response.raise_for_status()
                time.sleep(REQUEST_DELAY)  # Rate limiting
                return BeautifulSoup(response.text, "lxml")
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                time.sleep(REQUEST_DELAY * (attempt + 1))

        logger.error(f"Failed to fetch {url} after {retries} attempts")
        return None

    def get_all_faculty_links(self) -> list[dict]:
        """Get list of all faculty members from the main directory page"""
        url = f"{KSU_FACULTY_WEB}/index.php"
        soup = self._request(url)

        if not soup:
            logger.error("Failed to fetch main faculty directory")
            return []

        faculty_links = []
        seen_urls = set()

        # Find all faculty links - they are absolute URLs like:
        # https://facultyweb.kennesaw.edu/username/index.php
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            name = link.get_text(strip=True)

            # Skip empty names or very short names
            if not name or len(name) < 3:
                continue

            # Only process facultyweb.kennesaw.edu links with /index.php
            if "facultyweb.kennesaw.edu" in href and "/index.php" in href:
                # Skip the main index page itself
                if href.rstrip("/").endswith("facultyweb.kennesaw.edu") or href == f"{KSU_FACULTY_WEB}/index.php":
                    continue

                # Extract username from URL
                # URL format: https://facultyweb.kennesaw.edu/username/index.php
                try:
                    # Remove the base URL and /index.php to get username
                    path = href.replace("https://facultyweb.kennesaw.edu/", "").replace("http://facultyweb.kennesaw.edu/", "")
                    username = path.split("/")[0]

                    if username and username != "index.php" and len(username) > 1:
                        full_url = f"https://facultyweb.kennesaw.edu/{username}/index.php"

                        # Avoid duplicates
                        if full_url not in seen_urls:
                            seen_urls.add(full_url)
                            faculty_links.append({
                                "name": name,
                                "net_id": username,
                                "url": full_url
                            })
                except Exception as e:
                    logger.debug(f"Error parsing URL {href}: {e}")
                    continue

        logger.info(f"Found {len(faculty_links)} total faculty profiles")
        return faculty_links

    def get_faculty_list_by_letter(self, letter: str) -> list[dict]:
        """Get list of faculty members for a given letter (filters from all faculty)"""
        all_faculty = self.get_all_faculty_links()

        # Filter by last name starting with the letter
        filtered = []
        for faculty in all_faculty:
            name = faculty.get("name", "")
            # Try to get last name (assume "Last, First" or "First Last" format)
            if "," in name:
                last_name = name.split(",")[0].strip()
            else:
                parts = name.split()
                last_name = parts[-1] if parts else ""

            if last_name.upper().startswith(letter.upper()):
                filtered.append(faculty)

        logger.info(f"Found {len(filtered)} faculty for letter {letter}")
        return filtered

    def scrape_profile(self, profile_url: str, net_id: str) -> Optional[FacultyProfile]:
        """Scrape an individual faculty profile"""
        soup = self._request(profile_url)

        if not soup:
            return None

        profile = FacultyProfile()
        profile.net_id = net_id
        profile.profile_url = profile_url

        # Try to extract name from title tag first (most reliable)
        title_tag = soup.find("title")
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            # Title format is often "Dr. First Last - KSU" or "First Last | Faculty"
            # Remove common suffixes
            full_name = re.sub(r"\s*[-|–]\s*(Kennesaw|KSU|Faculty|Home).*", "", title_text, flags=re.IGNORECASE)
            full_name = full_name.strip()

            if full_name and len(full_name) > 2 and full_name.lower() not in ["contact", "home", "index"]:
                profile.name = full_name

        # If title didn't work, try h1
        if not profile.name:
            h1 = soup.find("h1")
            if h1:
                h1_text = h1.get_text(strip=True)
                if h1_text and len(h1_text) > 2 and h1_text.lower() not in ["contact", "home"]:
                    profile.name = h1_text

        # Clean up the name - remove Dr., PhD, etc. for parsing
        if profile.name:
            clean_name = re.sub(r"^(Dr\.|Prof\.|Professor)\s*", "", profile.name)
            clean_name = re.sub(r",?\s*(Ph\.?D\.?|M\.?D\.?|J\.?D\.?).*$", "", clean_name)
            name_parts = clean_name.strip().split()
            if len(name_parts) >= 2:
                profile.first_name = name_parts[0]
                profile.last_name = name_parts[-1]
            elif len(name_parts) == 1:
                profile.last_name = name_parts[0]

        # Look for photo - faculty pages use /netid/name.jpg pattern
        for img in soup.find_all("img"):
            src = img.get("src", "")
            # Skip common non-photo images
            if any(x in src.lower() for x in ["logo", "icon", "banner", "header", "footer", "button"]):
                continue
            # Look for .jpg/.png in the faculty's directory
            if f"/{net_id}/" in src or net_id in src.lower():
                if src.endswith((".jpg", ".jpeg", ".png", ".gif")):
                    profile.photo_url = urljoin(profile_url, src)
                    break
            # Also check for common photo patterns
            if any(x in src.lower() for x in ["photo", "headshot", "portrait", "profile"]):
                profile.photo_url = urljoin(profile_url, src)
                break

        # If no photo found, check for any jpg in the same directory
        if not profile.photo_url:
            for img in soup.find_all("img"):
                src = img.get("src", "")
                if src.startswith(f"/{net_id}/") or src.startswith(f"./{net_id}") or (src.startswith("/") and net_id in src):
                    profile.photo_url = urljoin(profile_url, src)
                    break

        # Look for email
        email_patterns = [
            r"[\w.+-]+@kennesaw\.edu",
            r"[\w.+-]+@students\.kennesaw\.edu",
        ]
        page_text = soup.get_text()
        for pattern in email_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                profile.email = match.group().lower()
                break

        # Look for phone
        phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", page_text)
        if phone_match:
            profile.phone = phone_match.group()

        # Look for common section headers and extract content
        sections = self._extract_sections(soup)

        if "research" in sections:
            profile.research_interests = self._parse_list_items(sections["research"])
        if "education" in sections:
            profile.education = self._parse_list_items(sections["education"])
        if "publication" in sections:
            profile.publications = self._parse_list_items(sections["publication"])
        if "course" in sections:
            profile.courses = self._parse_list_items(sections["course"])
        if "bio" in sections:
            profile.bio = sections["bio"]

        # Try to extract department/title from structured elements
        self._extract_structured_info(soup, profile)

        # Try to scrape sub-pages for more info (research, publications, etc.)
        self._scrape_subpages(soup, profile, profile_url, net_id)

        return profile

    def _scrape_subpages(self, main_soup: BeautifulSoup, profile: FacultyProfile, base_url: str, net_id: str):
        """Scrape linked sub-pages for research and publications"""
        # Find links to sub-pages
        subpage_links = {}
        for link in main_soup.find_all("a", href=True):
            href = link.get("href", "").lower()
            text = link.get_text(strip=True).lower()

            # Look for research/publications pages
            if any(x in href or x in text for x in ["research", "publication", "scholarly"]):
                if "research" not in subpage_links:
                    subpage_links["research"] = urljoin(base_url, link.get("href"))
            elif any(x in href or x in text for x in ["degree", "education", "cv", "vita"]):
                if "education" not in subpage_links:
                    subpage_links["education"] = urljoin(base_url, link.get("href"))

        # Scrape research/publications page
        if "research" in subpage_links and not profile.publications:
            research_soup = self._request(subpage_links["research"])
            if research_soup:
                # Look for publication lists
                pubs = []
                for li in research_soup.find_all("li"):
                    text = li.get_text(strip=True)
                    # Publications usually have year patterns
                    if re.search(r"\b(19|20)\d{2}\b", text) and len(text) > 30:
                        pubs.append(text[:500])  # Limit length
                if pubs:
                    profile.publications = pubs[:30]  # Limit to 30

                # Look for research interests
                if not profile.research_interests:
                    sections = self._extract_sections(research_soup)
                    if "research" in sections:
                        profile.research_interests = self._parse_list_items(sections["research"])

        # Scrape education page
        if "education" in subpage_links and not profile.education:
            edu_soup = self._request(subpage_links["education"])
            if edu_soup:
                edu = []
                for li in edu_soup.find_all("li"):
                    text = li.get_text(strip=True)
                    # Education entries usually mention degrees or universities
                    if any(x in text.lower() for x in ["ph.d", "m.s", "b.s", "master", "bachelor", "university", "college"]):
                        edu.append(text[:300])
                if edu:
                    profile.education = edu[:10]

    def _extract_sections(self, soup: BeautifulSoup) -> dict:
        """Extract content sections from the page"""
        sections = {}

        # Look for headers followed by content
        for header in soup.find_all(["h2", "h3", "h4", "strong", "b"]):
            header_text = header.get_text(strip=True).lower()

            # Identify section type
            section_type = None
            if "research" in header_text and ("interest" in header_text or "area" in header_text):
                section_type = "research"
            elif "education" in header_text or "degree" in header_text:
                section_type = "education"
            elif "publication" in header_text:
                section_type = "publication"
            elif "course" in header_text or "teaching" in header_text:
                section_type = "course"
            elif "bio" in header_text or "about" in header_text:
                section_type = "bio"

            if section_type:
                # Get content after header
                content = []
                for sibling in header.find_next_siblings():
                    if sibling.name in ["h2", "h3", "h4"]:
                        break
                    text = sibling.get_text(strip=True)
                    if text:
                        content.append(text)

                if content:
                    sections[section_type] = "\n".join(content)

        return sections

    def _parse_list_items(self, text: str) -> list[str]:
        """Parse text into list items"""
        items = []

        # Split by common delimiters
        for line in text.split("\n"):
            line = line.strip()
            # Remove bullet points and numbers
            line = re.sub(r"^[\s•\-\*\d.]+", "", line).strip()
            if line and len(line) > 3:
                items.append(line)

        return items[:20]  # Limit to 20 items

    def _extract_structured_info(self, soup: BeautifulSoup, profile: FacultyProfile):
        """Extract structured info like title and department"""
        # Look for common patterns
        page_text = soup.get_text()

        # Common titles
        titles = ["Professor", "Associate Professor", "Assistant Professor", "Lecturer", "Instructor"]
        for title in titles:
            if title in page_text:
                profile.title = title
                break

        # Look for department mentions
        dept_pattern = r"Department of ([\w\s&]+)"
        match = re.search(dept_pattern, page_text)
        if match:
            profile.department = match.group(1).strip()

        # Look for college mentions
        college_pattern = r"College of ([\w\s&]+)"
        match = re.search(college_pattern, page_text)
        if match:
            profile.college = match.group(1).strip()

    def scrape_all(self, letters: Optional[list[str]] = None) -> list[FacultyProfile]:
        """Scrape all faculty or specific letters"""
        if letters is None:
            letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        all_profiles = []

        for letter in letters:
            logger.info(f"Scraping faculty starting with '{letter}'")
            faculty_list = self.get_faculty_list_by_letter(letter)

            for faculty in tqdm(faculty_list, desc=f"Letter {letter}"):
                profile = self.scrape_profile(faculty["url"], faculty["net_id"])
                if profile:
                    all_profiles.append(profile)

            # Save intermediate results
            self._save_results(all_profiles, f"faculty_partial_{letter}.json")

        return all_profiles

    def _save_results(self, profiles: list[FacultyProfile], filename: str):
        """Save profiles to JSON file"""
        output_path = Path(OUTPUT_DIR) / filename
        data = [p.to_dict() for p in profiles]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(profiles)} profiles to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Scrape KSU Faculty Web")
    parser.add_argument("--letter", type=str, help="Scrape faculty for specific letter")
    parser.add_argument("--all", action="store_true", help="Scrape all faculty")
    parser.add_argument("--test", action="store_true", help="Test with just letter A")
    args = parser.parse_args()

    scraper = KSUFacultyScraper()

    if args.test:
        profiles = scraper.scrape_all(["A"])
    elif args.letter:
        profiles = scraper.scrape_all([args.letter.upper()])
    elif args.all:
        profiles = scraper.scrape_all()
    else:
        parser.print_help()
        return

    # Save final results
    scraper._save_results(profiles, "faculty_all.json")
    logger.info(f"Scraping complete. Total profiles: {len(profiles)}")


if __name__ == "__main__":
    main()
