# feed_manager.py
import os
from typing import List
from xml.etree import ElementTree as ET

class FeedManager:
    def __init__(self, base_dir: str = "opml"):
        self.base_dir = base_dir
        self.cache = {}

        # Custom mapping from user interest names to OPML filenames
        self.interest_to_opml_files = {
            "Technology": ["Android Development.opml", "Android.opml", "Apple.opml","Cars.opml","iOS Development.opml","Programming.opml","Tech.opml","UI - UX.opml","Web Development.opml"],
            "Science": ["Science.opml","Space.opml"],
            "Business": ["Business & Economy.opml", "Personal finance.opml","Startups.opml"],
            "Politics": ["History.opml","News.opml"],
            "Food": ["Food.opml"],
            "Fashion": ["Fashion.opml","Beauty.opml","DIY.opml"],
            "Movies": ["Movies.opml", "Television.opml"],
            "Gaming": ["Gaming.opml"],
            "Music": ["Music.opml"],
            "Sports": ["Sports.opml","Cricket.opml","Football.opml","Gaming.opml","Tennis.opml"],
            "Travel": ["Travel.opml","Cars.opml","Photography.opml"],
            "Education": ["Android Development.opml", "Architecture.opml", "Books.opml","History.opml","Interior design.opml","iOS Development.opml","News.opml", "Personal finance.opml","Programming.opml","UI - UX.opml","Web Development.opml"],
            "Arts": ["DIY.opml","Funny.opml","Movies.opml","Music.opml","Photography.opml"],
            # Customize or expand as needed
        }

        # Default country opml files to use when country file is not found
        self.country_fallbacks = ["Global.opml", "US.opml", "International.opml"]

    def get_feeds_for_user(self, interests: List[str], nationality: str) -> List[str]:
        feed_urls = []

        # 1. Load nationality feeds
        nationality_path = os.path.join(self.base_dir, "countries_without_category", f"{nationality}.opml")
        if os.path.exists(nationality_path):
            feed_urls += self._load_opml_cached(nationality_path)
        else:
            # Try fallback countries if the requested one doesn't exist
            for fallback in self.country_fallbacks:
                fallback_path = os.path.join(self.base_dir, "countries_without_category", fallback)
                if os.path.exists(fallback_path):
                    feed_urls += self._load_opml_cached(fallback_path)
                    break

        # 2. Load interest feeds
        for interest in interests:
            opml_files = self.interest_to_opml_files.get(interest, [])
            for opml_file in opml_files:
                interest_path = os.path.join(self.base_dir, "interests_without_category", opml_file)
                feed_urls += self._load_opml_cached(interest_path)

        # If we still have no feeds, load some default feeds
        if not feed_urls:
            default_interests = ["Technology", "News", "Science"]
            for interest in default_interests:
                opml_files = self.interest_to_opml_files.get(interest, [])
                for opml_file in opml_files:
                    interest_path = os.path.join(self.base_dir, "interests_without_category", opml_file)
                    feed_urls += self._load_opml_cached(interest_path)

        return list(set(feed_urls))  # Remove duplicates

    def _load_opml_cached(self, file_path: str) -> List[str]:
        if not os.path.exists(file_path):
            print(f"[FeedManager] OPML file not found: {file_path}")
            return []

        if file_path in self.cache:
            return self.cache[file_path]

        urls = self._parse_opml(file_path)
        self.cache[file_path] = urls
        return urls

    def _parse_opml(self, file_path: str) -> List[str]:
        urls = []
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            body = root.find('body')
            for outline in body.findall('outline'):
                xml_url = outline.attrib.get('xmlUrl')
                if xml_url:
                    urls.append(xml_url)
        except Exception as e:
            print(f"[FeedManager] Failed to parse {file_path}: {e}")
        return urls