#!/usr/bin/env python3
"""
Text Extractor for Research Papers
Extracts text content from PDF, DOCX, and TXT files
"""

import sys
import os
import re
from pathlib import Path

def extract_from_pdf(file_path):
    """Extract text from PDF files using PyPDF2"""
    try:
        import PyPDF2
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            
            return text.strip()
    except ImportError:
        print("PyPDF2 not installed. Installing...")
        os.system("pip3 install PyPDF2")
        return extract_from_pdf(file_path)
    except Exception as e:
        print(f"Error extracting from PDF: {str(e)}")
        return None

def extract_from_docx(file_path):
    """Extract text from DOCX files using python-docx"""
    try:
        from docx import Document
        
        doc = Document(file_path)
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    except ImportError:
        print("python-docx not installed. Installing...")
        os.system("pip3 install python-docx")
        return extract_from_docx(file_path)
    except Exception as e:
        print(f"Error extracting from DOCX: {str(e)}")
        return None

def extract_from_txt(file_path):
    """Extract text from TXT files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read().strip()
        except Exception as e:
            print(f"Error reading TXT file: {str(e)}")
            return None
    except Exception as e:
        print(f"Error extracting from TXT: {str(e)}")
        return None

def clean_text(text):
    """Clean and normalize extracted text"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page numbers and headers/footers (basic patterns)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    text = re.sub(r'\n\s*Page \d+.*?\n', '\n', text, flags=re.IGNORECASE)
    
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def extract_metadata(text):
    """Extract basic metadata from the text"""
    metadata = {
        'title': '',
        'authors': [],
        'abstract': ''
    }
    
    lines = text.split('\n')
    
    # Try to find title (usually first non-empty line or largest text)
    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        if len(line) > 10 and not line.lower().startswith(('abstract', 'introduction')):
            metadata['title'] = line
            break
    
    # Try to find abstract
    abstract_start = -1
    abstract_end = -1
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if line_lower.startswith('abstract'):
            abstract_start = i
        elif abstract_start != -1 and (line_lower.startswith(('introduction', '1.', 'keywords', 'key words'))):
            abstract_end = i
            break
    
    if abstract_start != -1:
        if abstract_end == -1:
            abstract_end = min(abstract_start + 20, len(lines))  # Limit to 20 lines
        
        abstract_lines = lines[abstract_start:abstract_end]
        abstract_text = ' '.join(abstract_lines).strip()
        # Remove "Abstract" prefix
        abstract_text = re.sub(r'^abstract\s*:?\s*', '', abstract_text, flags=re.IGNORECASE)
        metadata['abstract'] = abstract_text
    
    return metadata

def process_document(input_path, output_path):
    """Main function to process a document and extract text"""
    try:
        # Validate input file exists
        if not os.path.exists(input_path):
            print(f"Error: Input file {input_path} does not exist")
            return False
        
        # Determine file type and extract text
        file_extension = Path(input_path).suffix.lower()
        
        if file_extension == '.pdf':
            text = extract_from_pdf(input_path)
        elif file_extension == '.docx':
            text = extract_from_docx(input_path)
        elif file_extension in ['.txt', '.text']:
            text = extract_from_txt(input_path)
        else:
            print(f"Error: Unsupported file type {file_extension}")
            return False
        
        if text is None:
            print("Error: Failed to extract text from document")
            return False
        
        # Clean the extracted text
        cleaned_text = clean_text(text)
        
        if not cleaned_text:
            print("Error: No text content found in document")
            return False
        
        # Extract metadata
        metadata = extract_metadata(cleaned_text)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save extracted text
        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write(cleaned_text)
        
        # Save metadata as JSON
        import json
        metadata_path = output_path.replace('.txt', '_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as metadata_file:
            json.dump(metadata, metadata_file, indent=2, ensure_ascii=False)
        
        print(f"Successfully extracted text from {input_path}")
        print(f"Text saved to: {output_path}")
        print(f"Metadata saved to: {metadata_path}")
        print(f"Extracted {len(cleaned_text)} characters")
        
        if metadata['title']:
            print(f"Title: {metadata['title'][:100]}...")
        if metadata['abstract']:
            print(f"Abstract: {metadata['abstract'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python text_extractor.py <input_path> <output_path>")
        print("Supported formats: PDF, DOCX, TXT")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    success = process_document(input_path, output_path)
    sys.exit(0 if success else 1)

