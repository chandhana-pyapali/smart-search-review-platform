from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np

class TextSimilarityEngine:
    """
    Advanced text similarity engine using TF-IDF and cosine similarity
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            lowercase=True,
            max_features=5000,
            ngram_range=(1, 2)  # Include both unigrams and bigrams
        )
    
    def calculate_similarity(self, query, documents):
        """
        Calculate similarity between query and documents
        
        Args:
            query (str): Search query
            documents (list): List of document strings
            
        Returns:
            list: Similarity scores for each document
        """
        if not documents:
            return []
        
        # Prepare corpus
        corpus = documents + [query]
        
        try:
            # Fit and transform
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            
            # Get query vector (last item)
            query_vector = tfidf_matrix[-1]
            
            # Calculate similarities
            similarities = cosine_similarity(
                query_vector, 
                tfidf_matrix[:-1]
            ).flatten()
            
            return similarities.tolist()
            
        except Exception as e:
            # Fallback to simple string matching
            return self._fallback_similarity(query, documents)
    
    def _fallback_similarity(self, query, documents):
        """
        Fallback similarity calculation using simple string matching
        """
        query_lower = query.lower()
        similarities = []
        
        for doc in documents:
            doc_lower = doc.lower()
            if query_lower in doc_lower:
                # Calculate simple overlap score
                overlap = len(set(query_lower.split()) & set(doc_lower.split()))
                total_words = len(set(query_lower.split()) | set(doc_lower.split()))
                similarity = overlap / total_words if total_words > 0 else 0
            else:
                similarity = 0
            similarities.append(similarity)
        
        return similarities