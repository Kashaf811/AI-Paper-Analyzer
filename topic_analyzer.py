#!/usr/bin/env python3
"""
Topic Analyzer for Research Papers
Performs topic modeling, summarization, and topic suggestion
"""

import sys
import os
import json
import re
from pathlib import Path
from collections import Counter

def install_dependencies():
    """Install required dependencies if not available"""
    try:
        import nltk
        import sklearn
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import LatentDirichletAllocation
    except ImportError as e:
        print(f"Installing missing dependency: {e}")
        os.system("pip3 install nltk scikit-learn")
        import nltk
        import sklearn

def download_nltk_data():
    """Download required NLTK data"""
    try:
        import nltk
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        nltk.data.find('taggers/averaged_perceptron_tagger')
    except LookupError:
        print("Downloading NLTK data...")
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)

def preprocess_text(text):
    """Preprocess text for topic modeling"""
    try:
        import nltk
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize, sent_tokenize
        
        # Download NLTK data if needed
        download_nltk_data()
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Tokenize
        words = word_tokenize(text)
        
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        
        # Add common academic stopwords
        academic_stopwords = {
            'paper', 'study', 'research', 'analysis', 'method', 'approach',
            'result', 'conclusion', 'introduction', 'discussion', 'section',
            'figure', 'table', 'data', 'experiment', 'test', 'model',
            'algorithm', 'technique', 'framework', 'system', 'application',
            'work', 'article', 'journal', 'conference', 'proceedings',
            'abstract', 'keyword', 'reference', 'citation', 'bibliography'
        }
        stop_words.update(academic_stopwords)
        
        # Filter words
        filtered_words = [
            word for word in words 
            if word not in stop_words 
            and len(word) > 2 
            and word.isalpha()
        ]
        
        return ' '.join(filtered_words)
        
    except Exception as e:
        print(f"Error in text preprocessing: {str(e)}")
        return text

def extract_topics_lda(text, num_topics=5):
    """Extract topics using Latent Dirichlet Allocation"""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import LatentDirichletAllocation
        
        # Preprocess text
        processed_text = preprocess_text(text)
        
        if not processed_text.strip():
            return []
        
        # Split into sentences for better topic modeling
        sentences = processed_text.split('.')
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if len(sentences) < 3:
            # If too few sentences, use word-based approach
            words = processed_text.split()
            if len(words) < 50:
                return extract_topics_tfidf(text)
            
            # Create pseudo-sentences from words
            chunk_size = max(10, len(words) // 10)
            sentences = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        
        # Vectorize text
        vectorizer = TfidfVectorizer(
            max_features=100,
            min_df=1,
            max_df=0.8,
            ngram_range=(1, 2)
        )
        
        doc_term_matrix = vectorizer.fit_transform(sentences)
        
        # Perform LDA
        lda = LatentDirichletAllocation(
            n_components=min(num_topics, len(sentences)),
            random_state=42,
            max_iter=10
        )
        
        lda.fit(doc_term_matrix)
        
        # Extract topics
        feature_names = vectorizer.get_feature_names_out()
        topics = []
        
        for topic_idx, topic in enumerate(lda.components_):
            top_words_idx = topic.argsort()[-10:][::-1]
            top_words = [feature_names[i] for i in top_words_idx]
            
            # Create topic name from top words
            topic_name = ' '.join(top_words[:3])
            
            # Calculate relevance score
            relevance_score = float(topic.max())
            
            topics.append({
                'topic': topic_name,
                'relevanceScore': relevance_score,
                'keywords': top_words[:5]
            })
        
        # Sort by relevance
        topics.sort(key=lambda x: x['relevanceScore'], reverse=True)
        
        return topics
        
    except Exception as e:
        print(f"Error in LDA topic extraction: {str(e)}")
        return extract_topics_tfidf(text)

def extract_topics_tfidf(text, num_topics=5):
    """Extract topics using TF-IDF as fallback"""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        # Preprocess text
        processed_text = preprocess_text(text)
        
        if not processed_text.strip():
            return []
        
        # Split into sentences
        sentences = [s.strip() for s in processed_text.split('.') if len(s.strip()) > 10]
        
        if len(sentences) < 2:
            # Use word frequency approach
            words = processed_text.split()
            word_freq = Counter(words)
            top_words = word_freq.most_common(10)
            
            topics = []
            for i, (word, freq) in enumerate(top_words[:num_topics]):
                topics.append({
                    'topic': word,
                    'relevanceScore': freq / len(words),
                    'keywords': [word]
                })
            
            return topics
        
        # Use TF-IDF
        vectorizer = TfidfVectorizer(
            max_features=50,
            min_df=1,
            ngram_range=(1, 2)
        )
        
        tfidf_matrix = vectorizer.fit_transform(sentences)
        feature_names = vectorizer.get_feature_names_out()
        
        # Get average TF-IDF scores
        mean_scores = tfidf_matrix.mean(axis=0).A1
        
        # Get top features
        top_indices = mean_scores.argsort()[-20:][::-1]
        
        topics = []
        for i in range(min(num_topics, len(top_indices))):
            idx = top_indices[i]
            topic_name = feature_names[idx]
            score = mean_scores[idx]
            
            topics.append({
                'topic': topic_name,
                'relevanceScore': float(score),
                'keywords': [topic_name]
            })
        
        return topics
        
    except Exception as e:
        print(f"Error in TF-IDF topic extraction: {str(e)}")
        return []

def generate_summary(text, max_sentences=3):
    """Generate extractive summary of the text"""
    try:
        import nltk
        from nltk.tokenize import sent_tokenize
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        download_nltk_data()
        
        # Split into sentences
        sentences = sent_tokenize(text)
        
        if len(sentences) <= max_sentences:
            return ' '.join(sentences)
        
        # Preprocess sentences
        processed_sentences = [preprocess_text(sent) for sent in sentences]
        processed_sentences = [s for s in processed_sentences if len(s.strip()) > 10]
        
        if len(processed_sentences) < 2:
            return ' '.join(sentences[:max_sentences])
        
        # Use TF-IDF to rank sentences
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(processed_sentences)
        
        # Calculate sentence scores
        sentence_scores = tfidf_matrix.sum(axis=1).A1
        
        # Get top sentences
        top_sentence_indices = sentence_scores.argsort()[-max_sentences:][::-1]
        top_sentence_indices.sort()  # Maintain original order
        
        summary_sentences = [sentences[i] for i in top_sentence_indices if i < len(sentences)]
        
        return ' '.join(summary_sentences)
        
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        # Fallback: return first few sentences
        sentences = text.split('.')[:max_sentences]
        return '. '.join(sentences) + '.'

def suggest_topics(extracted_topics, predefined_topics):
    """Suggest related topics based on extracted topics"""
    try:
        suggestions = []
        
        # Simple keyword matching approach
        for extracted_topic in extracted_topics:
            topic_keywords = extracted_topic.get('keywords', [extracted_topic['topic']])
            
            for predefined_topic in predefined_topics:
                topic_name = predefined_topic['name'].lower()
                topic_desc = predefined_topic.get('description', '').lower()
                
                # Calculate similarity score
                similarity_score = 0
                
                for keyword in topic_keywords:
                    keyword = keyword.lower()
                    if keyword in topic_name:
                        similarity_score += 0.8
                    elif keyword in topic_desc:
                        similarity_score += 0.5
                    
                    # Check for partial matches
                    for word in topic_name.split():
                        if word in keyword or keyword in word:
                            similarity_score += 0.3
                
                if similarity_score > 0.3:
                    suggestions.append({
                        'topicId': predefined_topic.get('_id', predefined_topic['name']),
                        'topicName': predefined_topic['name'],
                        'suggestionScore': min(similarity_score, 1.0)
                    })
        
        # Remove duplicates and sort by score
        seen_topics = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            topic_id = suggestion['topicId']
            if topic_id not in seen_topics:
                seen_topics.add(topic_id)
                unique_suggestions.append(suggestion)
        
        unique_suggestions.sort(key=lambda x: x['suggestionScore'], reverse=True)
        
        return unique_suggestions[:5]  # Return top 5 suggestions
        
    except Exception as e:
        print(f"Error suggesting topics: {str(e)}")
        return []

def analyze_paper(text_path, output_path, predefined_topics_path=None):
    """Main function to analyze a research paper"""
    try:
        # Install dependencies
        install_dependencies()
        
        # Read the extracted text
        with open(text_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        if not text.strip():
            print("Error: No text content found")
            return False
        
        print(f"Analyzing text with {len(text)} characters...")
        
        # Extract topics
        print("Extracting topics...")
        extracted_topics = extract_topics_lda(text, num_topics=5)
        
        if not extracted_topics:
            print("LDA failed, trying TF-IDF...")
            extracted_topics = extract_topics_tfidf(text, num_topics=5)
        
        # Generate summary
        print("Generating summary...")
        summary = generate_summary(text, max_sentences=3)
        
        # Load predefined topics for suggestions
        predefined_topics = []
        if predefined_topics_path and os.path.exists(predefined_topics_path):
            try:
                with open(predefined_topics_path, 'r', encoding='utf-8') as file:
                    predefined_topics = json.load(file)
            except Exception as e:
                print(f"Warning: Could not load predefined topics: {e}")
        
        # Generate topic suggestions
        print("Generating topic suggestions...")
        suggested_topics = suggest_topics(extracted_topics, predefined_topics)
        
        # Prepare analysis results
        analysis_result = {
            'summary': summary,
            'extractedTopics': extracted_topics,
            'suggestedTopics': suggested_topics,
            'analysisDate': str(os.path.getctime(text_path))
        }
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save analysis results
        with open(output_path, 'w', encoding='utf-8') as output_file:
            json.dump(analysis_result, output_file, indent=2, ensure_ascii=False)
        
        print(f"Analysis completed successfully!")
        print(f"Results saved to: {output_path}")
        print(f"Found {len(extracted_topics)} topics")
        print(f"Generated {len(suggested_topics)} topic suggestions")
        print(f"Summary length: {len(summary)} characters")
        
        return True
        
    except Exception as e:
        print(f"Error analyzing paper: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python topic_analyzer.py <text_path> <output_path> [predefined_topics_path]")
        sys.exit(1)
    
    text_path = sys.argv[1]
    output_path = sys.argv[2]
    predefined_topics_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    success = analyze_paper(text_path, output_path, predefined_topics_path)
    sys.exit(0 if success else 1)

