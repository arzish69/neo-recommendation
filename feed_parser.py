import feedparser
import aiohttp
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import base64
from io import BytesIO
from PIL import Image
import re
import asyncio

class FeedParser:
    def __init__(self):
        self.session = None
        self.feed_cache = {}
        self.cache_expiry = timedelta(hours=2)

    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def fetch_image(self, image_url: str) -> Optional[str]:
        if not image_url:
            return None
        try:
            session = await self.get_session()
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    img = Image.open(BytesIO(image_data)).convert('RGB')
                    if img.size[0] > 300 or img.size[1] > 300:
                        img.thumbnail((300, 300))
                    buffered = BytesIO()
                    img.save(buffered, format="JPEG")
                    return f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"
                return None
        except Exception:
            return None

    async def parse_feed(self, url: str, auth: Optional[Dict] = None) -> List[Dict]:
        cached_feed = self.feed_cache.get(url)
        if cached_feed and datetime.now() < cached_feed['expiry']:
            return cached_feed['entries']

        try:
            session = await self.get_session()
            headers = {'User-Agent': 'Mozilla/5.0'}
            if auth:
                headers.update(auth)

            async with session.get(url, timeout=10, headers=headers) as response:
                if response.status != 200:
                    return []

                feed_content = await response.text()
                feed = feedparser.parse(feed_content)
                all_entries = feed.entries
                np.random.shuffle(all_entries)
                entries = []
                for entry in all_entries[:20]:
                    thumbnail = None
                    if hasattr(entry, 'media_thumbnail'):
                        thumbnail = entry.media_thumbnail[0]['url']
                    elif hasattr(entry, 'media_content'):
                        thumbnail = entry.media_content[0]['url']
                    else:
                        content = entry.get('description', '') or entry.get('summary', '')
                        soup = BeautifulSoup(content, 'html.parser')
                        img = soup.find('img')
                        if img and img.get('src'):
                            thumbnail = img['src']

                    thumbnail_data = await self.fetch_image(thumbnail) if thumbnail else None
                    published = entry.get('published_parsed') or entry.get('updated_parsed')
                    if published:
                        published = datetime(*published[:6]).isoformat()

                    entries.append({
                        'title': entry.get('title', ''),
                        'description': self._clean_html(entry.get('description', '') or entry.get('summary', '')),
                        'link': entry.get('link', ''),
                        'published': published,
                        'thumbnail': thumbnail_data,
                        'author': entry.get('author', ''),
                        'categories': entry.get('tags', []),
                    })
                self.feed_cache[url] = {
                    'entries': entries,
                    'expiry': datetime.now() + self.cache_expiry
                }
                return entries

        except Exception:
            return []

    def _clean_html(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:200] + '...' if len(text) > 200 else text

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None