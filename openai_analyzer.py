#!/usr/bin/env python3
"""
OpenAI-based Research Paper Analyzer
Uses OpenAI API for advanced topic analysis and summarization
"""

import sys
import os
import json
import openai
from pathlib import Path

def setup_openai():
    """Setup OpenAI client with environment variables"""
    try:
        # OpenAI API key and base URL are already set as environment variables
        api_key = os.getenv('OPENAI_API_KEY')
        api_base = os.getenv('OPENAI_API_BASE')
        
        if not api_key:
            print("Warning: OPENAI_API_KEY not found in environment")
            return None
        
        client = openai.OpenAI(
            api_key=api_key,
            base_url=api_base if api_base else None
        )
        
        return client
        
    except Exception as e:
        print(f"Error setting up OpenAI client: {str(e)}")
        return None

def analyze_with_openai(text, client):
    """Analyze research paper using OpenAI API"""
    try:
        # Truncate text if too long (OpenAI has token limits)
        max_chars = 12000  # Approximately 3000 tokens
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        
        prompt = f"""
Analyze the following research paper text and provide:

1. A concise summary (2-3 sentences)
2. 5-7 main topics/themes with relevance scores (0-1)
3. 3-5 suggested research areas that would be related to this paper

Research Paper Text:
{text}

Please respond in the following JSON format:
{{
    "summary": "Brief summary of the paper",
    "extractedTopics": [
        {{"topic": "topic name", "relevanceScore": 0.95, "keywords": ["keyword1", "keyword2"]}},
        ...
    ],
    "suggestedAreas": [
        {{"area": "research area name", "reasoning": "why this area is related"}},
        ...
    ]
}}
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert research analyst specializing in academic paper analysis. Provide accurate, insightful analysis in the requested JSON format."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # If JSON parsing fails, extract information manually
            print("Warning: Could not parse JSON response, using fallback extraction")
            return extract_from_text_response(result_text)
        
    except Exception as e:
        print(f"Error with OpenAI analysis: {str(e)}")
        return None

def extract_from_text_response(text):
    """Extract analysis from non-JSON OpenAI response"""
    try:
        result = {
            "summary": "",
            "extractedTopics": [],
            "suggestedAreas": []
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if 'summary' in line.lower():
                current_section = 'summary'
            elif 'topic' in line.lower() or 'theme' in line.lower():
                current_section = 'topics'
            elif 'suggest' in line.lower() or 'area' in line.lower():
                current_section = 'areas'
            elif current_section == 'summary' and not result['summary']:
                result['summary'] = line
            elif current_section == 'topics' and line.startswith(('-', '*', '•')):
                topic_text = line.lstrip('-*•').strip()
                result['extractedTopics'].append({
                    "topic": topic_text,
                    "relevanceScore": 0.8,
                    "keywords": [topic_text.split()[0]]
                })
            elif current_section == 'areas' and line.startswith(('-', '*', '•')):
                area_text = line.lstrip('-*•').strip()
                result['suggestedAreas'].append({
                    "area": area_text,
                    "reasoning": "Related to paper content"
                })
        
        return result
        
    except Exception as e:
        print(f"Error extracting from text response: {str(e)}")
        return None

def suggest_topics_openai(extracted_topics, predefined_topics, client):
    """Use OpenAI to suggest topics from predefined list"""
    try:
        if not predefined_topics:
            return []
        
        topics_text = "\n".join([f"- {topic['name']}: {topic.get('description', '')}" for topic in predefined_topics[:20]])
        extracted_text = "\n".join([f"- {topic['topic']}" for topic in extracted_topics])
        
        prompt = f"""
Given these extracted topics from a research paper:
{extracted_text}

And this list of predefined research topics:
{topics_text}

Suggest the 5 most relevant predefined topics that match the extracted topics. 
Provide a relevance score (0-1) for each suggestion.

Respond in JSON format:
{{
    "suggestions": [
        {{"topicName": "topic name", "suggestionScore": 0.85, "reasoning": "why it matches"}},
        ...
    ]
}}
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at matching research topics. Provide accurate relevance scores."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.2
        )
        
        result_text = response.choices[0].message.content.strip()
        
        try:
            result = json.loads(result_text)
            suggestions = result.get('suggestions', [])
            
            # Convert to expected format
            formatted_suggestions = []
            for suggestion in suggestions:
                # Find the topic ID from predefined topics
                topic_id = None
                for topic in predefined_topics:
                    if topic['name'].lower() == suggestion['topicName'].lower():
                        topic_id = topic.get('_id', topic['name'])
                        break
                
                if topic_id:
                    formatted_suggestions.append({
                        'topicId': topic_id,
                        'topicName': suggestion['topicName'],
                        'suggestionScore': suggestion['suggestionScore']
                    })
            
            return formatted_suggestions
            
        except json.JSONDecodeError:
            print("Warning: Could not parse topic suggestions JSON")
            return []
        
    except Exception as e:
        print(f"Error with OpenAI topic suggestions: {str(e)}")
        return []

def analyze_paper_openai(text_path, output_path, predefined_topics_path=None):
    """Main function to analyze paper using OpenAI"""
    try:
        # Setup OpenAI client
        client = setup_openai()
        if not client:
            print("OpenAI client not available, falling back to local analysis")
            # Import and use local analyzer as fallback
            from topic_analyzer import analyze_paper
            return analyze_paper(text_path, output_path, predefined_topics_path)
        
        # Read the extracted text
        with open(text_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        if not text.strip():
            print("Error: No text content found")
            return False
        
        print(f"Analyzing text with OpenAI ({len(text)} characters)...")
        
        # Analyze with OpenAI
        openai_result = analyze_with_openai(text, client)
        
        if not openai_result:
            print("OpenAI analysis failed, falling back to local analysis")
            from topic_analyzer import analyze_paper
            return analyze_paper(text_path, output_path, predefined_topics_path)
        
        # Load predefined topics for suggestions
        predefined_topics = []
        if predefined_topics_path and os.path.exists(predefined_topics_path):
            try:
                with open(predefined_topics_path, 'r', encoding='utf-8') as file:
                    predefined_topics = json.load(file)
            except Exception as e:
                print(f"Warning: Could not load predefined topics: {e}")
        
        # Get topic suggestions using OpenAI
        suggested_topics = []
        if predefined_topics and openai_result.get('extractedTopics'):
            suggested_topics = suggest_topics_openai(
                openai_result['extractedTopics'], 
                predefined_topics, 
                client
            )
        
        # Prepare final analysis results
        analysis_result = {
            'summary': openai_result.get('summary', ''),
            'extractedTopics': openai_result.get('extractedTopics', []),
            'suggestedTopics': suggested_topics,
            'suggestedAreas': openai_result.get('suggestedAreas', []),
            'analysisDate': str(os.path.getctime(text_path)),
            'analyzedWith': 'OpenAI'
        }
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save analysis results
        with open(output_path, 'w', encoding='utf-8') as output_file:
            json.dump(analysis_result, output_file, indent=2, ensure_ascii=False)
        
        print(f"OpenAI analysis completed successfully!")
        print(f"Results saved to: {output_path}")
        print(f"Found {len(analysis_result['extractedTopics'])} topics")
        print(f"Generated {len(suggested_topics)} topic suggestions")
        print(f"Summary: {analysis_result['summary'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"Error in OpenAI analysis: {str(e)}")
        # Fallback to local analysis
        try:
            from topic_analyzer import analyze_paper
            return analyze_paper(text_path, output_path, predefined_topics_path)
        except Exception as fallback_error:
            print(f"Fallback analysis also failed: {str(fallback_error)}")
            return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python openai_analyzer.py <text_path> <output_path> [predefined_topics_path]")
        sys.exit(1)
    
    text_path = sys.argv[1]
    output_path = sys.argv[2]
    predefined_topics_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    success = analyze_paper_openai(text_path, output_path, predefined_topics_path)
    sys.exit(0 if success else 1)

