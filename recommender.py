from feed_parser import FeedParser
from feed_manager import FeedManager
import os
from datetime import datetime, timedelta
import asyncio
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
import string
from collections import defaultdict

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
    
    def get_top_interests_scores(self, article_text, user_interests):
        # Calculate score for each interest and return top matches
        interest_scores = {}
        
        # Process the article text once
        processed_text = self.preprocess_text(article_text)
        
        topic_keywords = {
            'Technology': ['tech', 'software', 'digital', 'ai', 'computer', 'app', 'cyber', 'innovation', 'programming', 'gadget', 'electronics', 'internet'],
            'Science': ['research', 'study', 'scientist', 'discovery', 'lab', 'physics', 'chemistry', 'biology', 'astronomy', 'experiment', 'scientific'],
            'Business': ['market', 'company', 'startup', 'finance', 'industry', 'trade', 'economy', 'investment', 'business', 'entrepreneur', 'commerce'],
            'Arts': ['artist', 'exhibition', 'museum', 'gallery', 'painting', 'sculpture', 'art', 'design', 'creative', 'artwork', 'culture'],
            'Politics': ['government', 'policy', 'election', 'congress', 'political', 'vote', 'democracy', 'president', 'legislation', 'campaign', 'civic'],
            'Food': ['recipe', 'restaurant', 'cuisine', 'cooking', 'chef', 'meal', 'food', 'dining', 'ingredients', 'gourmet', 'culinary'],
            'Fashion': ['style', 'design', 'fashion', 'trend', 'collection', 'wear', 'clothing', 'apparel', 'luxury', 'couture', 'stylish'],
            'Movies': ['film', 'movie', 'cinema', 'director', 'actor', 'hollywood', 'screen', 'drama', 'comedy', 'thriller', 'animation'],
            'Sports': ['game', 'player', 'team', 'tournament', 'championship', 'athlete', 'sport', 'football', 'basketball', 'soccer', 'tennis'],
            'Health': ['medical', 'health', 'wellness', 'therapy', 'treatment', 'doctor', 'disease', 'medicine', 'healthcare', 'fitness', 'nutrition'],
            'Music': ['song', 'album', 'artist', 'band', 'concert', 'musical', 'music', 'genre', 'melody', 'rhythm', 'lyrics'],
            'Gaming': ['game', 'gaming', 'player', 'console', 'esports', 'developer', 'videogame', 'pc', 'playstation', 'xbox', 'nintendo'],
            'Environment': ['climate', 'environmental', 'sustainable', 'energy', 'eco', 'nature', 'pollution', 'conservation', 'planet', 'ecology', 'green'],
            'Travel': ['destination', 'tourism', 'travel', 'hotel', 'vacation', 'tour', 'adventure', 'explore', 'holiday', 'journey', 'trip'],
            'Education': ['school', 'university', 'learning', 'student', 'teacher', 'course', 'education', 'knowledge', 'study', 'academic', 'college']
        }

        # Calculate score for each interest
        for interest in user_interests:
            if interest in topic_keywords:
                keywords = topic_keywords[interest]
                processed_keywords = [self.preprocess_text(kw) for kw in keywords]
                
                score = 0
                for keyword in processed_keywords:
                    if keyword in processed_text:
                        score += 1
                
                interest_scores[interest] = score
        
        # Return the interest with the highest score
        if interest_scores:
            return max(interest_scores.items(), key=lambda x: x[1])[0]
        return user_interests[0] if user_interests else "General"

    from collections import defaultdict

    async def get_recommendations(self, user_profile: str, feed_urls: list, user_interests: list, user_nationality: str):
        print("🔍 Starting recommendation process")
        print(f"🧠 User interests: {user_interests}")
        print(f"🌐 Feed URLs: {len(feed_urls)} total")
        print(f"🌍 User nationality: {user_nationality}")
        
        # Debug: Print the actual feed URLs
        print(f"📥 Received feed_urls: {feed_urls[:5]}...")  # Print first 5 URLs
        
        # Let's use the FeedManager to identify country feeds
        feed_manager = FeedManager()
        
        # Get country-specific feeds properly based on nationality
        potential_country_feed_urls = feed_manager._load_opml_cached(
            os.path.join(feed_manager.base_dir, "countries_without_category", f"{user_nationality}.opml")
        )
        
        # Debug: Print what we loaded from the OPML file
        print(f"🔍 Country feeds from OPML file: {len(potential_country_feed_urls)} total")
        print(f"📝 Sample country OPML URLs: {potential_country_feed_urls[:2]}...")  # Print first 2
        
        # If country file doesn't exist, try fallbacks
        if not potential_country_feed_urls:
            print(f"⚠️ No OPML file found for {user_nationality}, trying fallbacks...")
            for fallback in feed_manager.country_fallbacks:
                potential_country_feed_urls = feed_manager._load_opml_cached(
                    os.path.join(feed_manager.base_dir, "countries_without_category", fallback)
                )
                if potential_country_feed_urls:
                    print(f"✅ Using {fallback} as fallback")
                    break
        
        # Debug: Print the matching process
        country_feed_urls = []
        for url in feed_urls:
            if url in potential_country_feed_urls:
                country_feed_urls.append(url)
        
        print(f"🔍 Matched {len(country_feed_urls)} country feeds from {len(feed_urls)} input feeds")
        
        # If no direct matches found, try a different approach
        if not country_feed_urls:
            print("❌ No direct URL matches found")
            # Check if the issue is with URL formatting (http vs https, trailing slashes, etc.)
            normalized_potential_urls = [url.lower().strip().rstrip('/') for url in potential_country_feed_urls]
            normalized_feed_urls = [url.lower().strip().rstrip('/') for url in feed_urls]
            
            for i, normalized_feed_url in enumerate(normalized_feed_urls):
                if normalized_feed_url in normalized_potential_urls:
                    country_feed_urls.append(feed_urls[i])
            
            print(f"🔍 After normalization: Matched {len(country_feed_urls)} country feeds")
        
        interest_feed_urls = [url for url in feed_urls if url not in country_feed_urls]
        
        print(f"📌 Country feeds identified: {len(country_feed_urls)}")
        print(f"📌 Interest feeds identified: {len(interest_feed_urls)}")
        
        # ... rest of your method remains the same

        if not country_feed_urls and interest_feed_urls:
            country_idx = max(1, len(interest_feed_urls) // 5)
            country_feed_urls = interest_feed_urls[:country_idx]
            print(f"⚠️ No explicit country feeds — selected top {country_idx} as country fallback")

        all_feed_urls = list(set(country_feed_urls + interest_feed_urls))
        print(f"🧪 Fetching {len(all_feed_urls)} feeds...")

        tasks = [self.feed_parser.parse_feed(url) for url in all_feed_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_articles = []
        corpus_texts = []
        article_sources = {}

        for i, entries in enumerate(results):
            if isinstance(entries, list):
                for entry in entries:
                    if self.is_valid_article(entry):
                        article_url = all_feed_urls[i]
                        content = f"{entry['title']} {entry['description']}"
                        corpus_texts.append(content)
                        all_articles.append(entry)
                        article_sources[id(entry)] = article_url
            else:
                print(f"❌ Error fetching feed {all_feed_urls[i]}: {results[i]}")

        print(f"📥 Total valid articles fetched: {len(all_articles)}")

        country_articles = []
        interest_articles = defaultdict(list)

        for article in all_articles:
            try:
                content = f"{article['title']} {article['description']}"
                score = self.calculate_topic_score(content, user_interests, article.get('published'), corpus_texts)
                primary_interest = self.get_top_interests_scores(content, user_interests)
                article_with_score = (article, score)

                if article_sources.get(id(article)) in country_feed_urls:
                    country_articles.append(article_with_score)
                else:
                    interest_articles[primary_interest].append(article_with_score)
            except Exception as e:
                print(f"❌ Error scoring article: {e}")

        country_articles.sort(key=lambda x: x[1], reverse=True)
        country_recommendations = [article for article, _ in country_articles[:3]]
        print(f"🌍 Top country recommendations: {len(country_recommendations)}")

        if len(country_recommendations) < 3:
            print("⚠️ Not enough country recommendations, backfilling...")
            more_needed = 3 - len(country_recommendations)
            all_interest_articles = [item for sublist in interest_articles.values() for item in sublist]
            all_interest_articles.sort(key=lambda x: x[1], reverse=True)
            more_articles = [article for article, _ in all_interest_articles[:more_needed]]
            country_recommendations.extend(more_articles)

        top_interests = sorted(
            interest_articles.keys(),
            key=lambda k: sum(score for _, score in interest_articles[k]),
            reverse=True
        )[:3]

        while len(top_interests) < 3 and user_interests:
            for interest in user_interests:
                if interest not in top_interests:
                    top_interests.append(interest)
                    if len(top_interests) == 3:
                        break

        default_interests = ["General", "Technology", "News"]
        for interest in default_interests:
            if len(top_interests) == 3:
                break
            if interest not in top_interests:
                top_interests.append(interest)

        print(f"🎯 Top 3 interests selected: {top_interests}")

        interest_recommendations = []

        for interest in top_interests[:3]:
            try:
                articles = interest_articles.get(interest, [])
                print(f"[DEBUG] Processing interest '{interest}' with {len(articles)} articles")
                
                articles.sort(key=lambda x: x[1], reverse=True)
                top_articles = [article for article, _ in articles[:3]]
                print(f"[DEBUG] Selected {len(top_articles)} top articles for '{interest}'")

                if len(top_articles) < 3:
                    more_needed = 3 - len(top_articles)
                    print(f"[DEBUG] Need {more_needed} more articles for '{interest}'")
                    
                    other_articles = []
                    for other_interest, other_interest_articles in interest_articles.items():
                        if other_interest != interest:
                            other_articles.extend([article for article, _ in other_interest_articles])
                    
                    other_articles = list({id(a): a for a in other_articles}.values())  # Deduplicate
                    print(f"[DEBUG] Found {len(other_articles)} other articles from different interests")
                    
                    other_articles.sort(key=lambda a: self.calculate_topic_score(
                        f"{a['title']} {a['description']}",
                        user_interests,
                        a.get('published'),
                        corpus_texts
                    ), reverse=True)
                    
                    top_articles.extend(other_articles[:more_needed])
                    print(f"[DEBUG] Now have {len(top_articles)} articles for '{interest}'")

                interest_recommendations.append(top_articles[:3])
                print(f"[DEBUG] Added {len(top_articles[:3])} articles to recommendations for '{interest}'")

            except Exception as e:
                print(f"❌ Error forming recommendations for interest '{interest}': {e}")
                import traceback
                print(traceback.format_exc())
                interest_recommendations.append([])

        while len(interest_recommendations) < 3:
            print(f"[DEBUG] Filling recommendations gap, current length: {len(interest_recommendations)}")
            interest_recommendations.append([])

        for i in range(len(interest_recommendations)):
            while len(interest_recommendations[i]) < 3:
                used_articles = {id(article) for group in interest_recommendations for article in group}
                found_unused = False
                
                for article in all_articles:
                    if id(article) not in used_articles:
                        interest_recommendations[i].append(article)
                        found_unused = True
                        print(f"[DEBUG] Added unused article to interest group {i}")
                        break
                
                if not found_unused:
                    print("⚠️ No more unused articles to fill recommendations, duplicating top scoring...")
                    highest_scoring = sorted(
                        all_articles,
                        key=lambda a: self.calculate_topic_score(
                            f"{a['title']} {a['description']}",
                            user_interests,
                            a.get('published'),
                            corpus_texts
                        ),
                        reverse=True
                    )
                    if highest_scoring:
                        interest_recommendations[i].append(highest_scoring[0])
                        print(f"[DEBUG] Added duplicate of top scoring article to interest group {i}")
                    else:
                        print(f"[ERROR] No articles available at all!")
                        break

        print("✅ Recommendation process complete.")
        return {
            "country_recommendations": country_recommendations[:3],
            "interest_recommendations": [group[:3] for group in interest_recommendations[:3]]
        }


    async def close(self):
        await self.feed_parser.close()