from feed_parser import FeedParser
from datetime import datetime, timedelta
import asyncio
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
import string

nltk.download('stopwords', quiet=True) # Download stopwords if you haven't already

class TopicBasedRecommender:
    def __init__(self):
        self.feed_parser = FeedParser()
        self.stop_words = set(stopwords.words('english'))
        self.punctuation = string.punctuation

    def preprocess_text(self, text):
        text = text.lower()
        text = ''.join([char for char in text if char not in self.punctuation]) # Remove punctuation
        tokens = text.split()
        tokens = [token for token in tokens if token not in self.stop_words] # Remove stopwords
        return " ".join(tokens) # Return as string for TfidfVectorizer

    def calculate_tfidf_score(self, article_text, interest_keywords, idf_values): # idf_values passed in
        article_text = self.preprocess_text(article_text)
        score = 0
        for interest, keywords in interest_keywords.items(): # interest_keywords is now a dict
            for keyword in keywords:
                keyword = self.preprocess_text(keyword) # preprocess keywords too for matching
                if keyword in article_text:
                    tf = article_text.split().count(keyword) / len(article_text.split()) if article_text.split() else 0 # TF calculation
                    idf = idf_values.get(keyword, 0) # Get pre-calculated IDF, default to 0 if keyword not in IDF vocab
                    score += tf * idf * 2 # TF-IDF score, doubled for interest relevance
        return score


    def calculate_topic_score(self, text, interests, published_date_str, corpus_texts): # corpus_texts added
        processed_texts = [self.preprocess_text(doc) for doc in corpus_texts] # preprocess corpus
        vectorizer = TfidfVectorizer()
        vectorizer.fit(processed_texts) # Fit on the corpus to learn IDF values
        idf_values_dict = dict(zip(vectorizer.get_feature_names_out(), vectorizer.idf_)) # create dict for IDF lookup


        topic_keywords_tfidf = { # Use processed keywords for TF-IDF
            'Technology': [self.preprocess_text(kw) for kw in ['tech', 'software', 'digital', 'ai', 'computer', 'app', 'cyber', 'innovation', 'programming', 'gadget', 'electronics', 'internet']],
            'Science': [self.preprocess_text(kw) for kw in ['research', 'study', 'scientist', 'discovery', 'lab', 'physics', 'chemistry', 'biology', 'astronomy', 'experiment', 'scientific']],
            'Business': [self.preprocess_text(kw) for kw in ['market', 'company', 'startup', 'finance', 'industry', 'trade', 'economy', 'investment', 'business', 'entrepreneur', 'commerce']],
            'Arts': [self.preprocess_text(kw) for kw in ['artist', 'exhibition', 'museum', 'gallery', 'painting', 'sculpture', 'art', 'design', 'creative', 'artwork', 'culture']],
            'Politics': [self.preprocess_text(kw) for kw in ['government', 'policy', 'election', 'congress', 'political', 'vote', 'democracy', 'president', 'legislation', 'campaign', 'civic']],
            'Food': [self.preprocess_text(kw) for kw in ['recipe', 'restaurant', 'cuisine', 'cooking', 'chef', 'meal', 'food', 'dining', 'ingredients', 'gourmet', 'culinary']],
            'Fashion': [self.preprocess_text(kw) for kw in ['style', 'design', 'fashion', 'trend', 'collection', 'wear', 'clothing', 'apparel', 'luxury', 'couture', 'stylish']],
            'Movies': [self.preprocess_text(kw) for kw in ['film', 'movie', 'cinema', 'director', 'actor', 'hollywood', 'screen', 'drama', 'comedy', 'thriller', 'animation']],
            'Sports': [self.preprocess_text(kw) for kw in ['game', 'player', 'team', 'tournament', 'championship', 'athlete', 'sport', 'football', 'basketball', 'soccer', 'tennis']],
            'Health': [self.preprocess_text(kw) for kw in ['medical', 'health', 'wellness', 'therapy', 'treatment', 'doctor', 'disease', 'medicine', 'healthcare', 'fitness', 'nutrition']],
            'Music': [self.preprocess_text(kw) for kw in ['song', 'album', 'artist', 'band', 'concert', 'musical', 'music', 'genre', 'melody', 'rhythm', 'lyrics']],
            'Gaming': [self.preprocess_text(kw) for kw in ['game', 'gaming', 'player', 'console', 'esports', 'developer', 'videogame', 'pc', 'playstation', 'xbox', 'nintendo']],
            'Environment': [self.preprocess_text(kw) for kw in ['climate', 'environmental', 'sustainable', 'energy', 'eco', 'nature', 'pollution', 'conservation', 'planet', 'ecology', 'green']],
            'Travel': [self.preprocess_text(kw) for kw in ['destination', 'tourism', 'travel', 'hotel', 'vacation', 'tour', 'adventure', 'explore', 'holiday', 'journey', 'trip']],
            'Education': [self.preprocess_text(kw) for kw in ['school', 'university', 'learning', 'student', 'teacher', 'course', 'education', 'knowledge', 'study', 'academic', 'college']]
        }


        article_score = self.calculate_tfidf_score(text, topic_keywords_tfidf, idf_values_dict)


        if published_date_str: # Freshness bonus remains the same
            try:
                published_date = datetime.fromisoformat(published_date_str.replace('Z', '+00:00'))
                now = datetime.now()
                age_days = (now - published_date).days
                freshness_bonus = 0
                if age_days <= 7:
                    freshness_bonus = 5
                elif age_days <= 14:
                    freshness_bonus = 3
                elif age_days <= 30:
                    freshness_bonus = 1
                article_score += freshness_bonus
            except (ValueError, AttributeError, TypeError):
                pass
        return article_score

    def is_within_date_range(self, article_date_str):
        try:
            article_date = datetime.fromisoformat(article_date_str.replace('Z', '+00:00'))
            today = datetime.now()
            one_month_ago = today - timedelta(days=30)
            return one_month_ago <= article_date <= today
        except (ValueError, AttributeError, TypeError):
            return False

    def is_valid_article(self, article): # No change needed here
        if not article.get('description') or len(article['description'].strip()) == 0:
            return False
        if not article.get('thumbnail'):
            return False
        if not article.get('title') or len(article['title'].strip()) == 0:
            return False
        if not article.get('link') or len(article['link'].strip()) == 0:
            return False
        if not article.get('published'):
            return False
        return self.is_within_date_range(article['published'])

    async def get_recommendations(self, user_profile: str, feed_urls: list, user_interests: list, n_recommendations=9):
        tasks = [self.feed_parser.parse_feed(url) for url in feed_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_articles = []
        corpus_texts = [] # Collect corpus texts here
        for entries in results:
            if isinstance(entries, list):
                for entry in entries:
                    if self.is_valid_article(entry):
                        content = f"{entry['title']} {entry['description']}"
                        corpus_texts.append(content) # Add to corpus

        for entries in results: # Separate loop to calculate scores after corpus is built
            if isinstance(entries, list):
                for entry in entries:
                    if self.is_valid_article(entry):
                        content = f"{entry['title']} {entry['description']}"
                        score = self.calculate_topic_score(content, user_interests, entry.get('published'), corpus_texts) # pass corpus texts
                        all_articles.append((entry, score))


        all_articles.sort(key=lambda x: x[1], reverse=True)
        recommendations = [article for article, _ in all_articles[:n_recommendations]]
        return recommendations

    async def close(self): # No change needed here
        await self.feed_parser.close()