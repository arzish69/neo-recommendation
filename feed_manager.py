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
        self.country_fallbacks = ["United States.opml"]

    def get_feeds_for_user(self, interests: List[str], nationality: str) -> List[str]:
        feed_urls = []
        
        # 1. Load nationality feeds
        nationality_path = os.path.join(self.base_dir, "countries_without_category", f"{nationality}.opml")
        print(f"[DEBUG] Looking for nationality file: {nationality_path}")
        
        if os.path.exists(nationality_path):
            print(f"[DEBUG] Found nationality file: {nationality_path}")
            nationality_feeds = self._load_opml_cached(nationality_path)
            
            # If parsing failed but file exists, try editing it
            if not nationality_feeds:
                print(f"[DEBUG] No feeds extracted from {nationality_path}, attempting to fix the file")
                # You could implement automatic fixing here
            
            feed_urls += nationality_feeds
        else:
            print(f"[DEBUG] Nationality file not found, trying fallbacks")
            # Try fallback countries if the requested one doesn't exist
            for fallback in self.country_fallbacks:
                fallback_path = os.path.join(self.base_dir, "countries_without_category", fallback)
                print(f"[DEBUG] Trying fallback: {fallback_path}")
                if os.path.exists(fallback_path):
                    print(f"[DEBUG] Found fallback file: {fallback_path}")
                    fallback_feeds = self._load_opml_cached(fallback_path)
                    if fallback_feeds:
                        feed_urls += fallback_feeds
                        break
                    else:
                        print(f"[DEBUG] No feeds extracted from fallback {fallback_path}")
                else:
                    print(f"[DEBUG] Fallback not found: {fallback_path}")

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
            # First try parsing normally
            tree = ET.parse(file_path)
            root = tree.getroot()
            body = root.find('body')
            for outline in body.findall('outline'):
                xml_url = outline.attrib.get('xmlUrl')
                if xml_url:
                    urls.append(xml_url)
        except ET.ParseError as e:
            print(f"[FeedManager] Initial parsing failed for {file_path}: {e}")
            # Try to fix common issues
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Fix common XML issues
                # Replace unescaped ampersands (but not already escaped ones)
                content = content.replace('&', '&amp;').replace('&amp;amp;', '&amp;')
                # Fix other potential issues
                content = content.replace(' & ', ' &amp; ')
                
                # Try parsing the fixed content
                root = ET.fromstring(content)
                body = root.find('body')
                for outline in body.findall('outline'):
                    xml_url = outline.attrib.get('xmlUrl')
                    if xml_url:
                        urls.append(xml_url)
                print(f"[FeedManager] Successfully parsed {file_path} after applying fixes")
            except Exception as inner_e:
                print(f"[FeedManager] Failed to parse {file_path} even after fixes: {inner_e}")
                # If still failing, try a more aggressive approach
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract URLs using regex as a last resort
                    import re
                    pattern = r'xmlUrl="([^"]+)"'
                    matches = re.findall(pattern, content)
                    if matches:
                        urls.extend(matches)
                        print(f"[FeedManager] Extracted {len(matches)} URLs using regex from {file_path}")
                except Exception as regex_e:
                    print(f"[FeedManager] Regex extraction also failed for {file_path}: {regex_e}")
        return urls