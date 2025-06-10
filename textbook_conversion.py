import streamlit as st
import fitz  # PyMuPDF
import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import pandas as pd
import plotly.express as px
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image
import hashlib
import pickle
import os
from collections import Counter
import torch

# Function to extract text from PDF with better error handling
def extract_text_from_pdf(file):
    try:
        file_bytes = file.read()
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            text_parts = []
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                if page_text.strip():  # Only add non-empty pages
                    text_parts.append(page_text)
                
                # Process in chunks to avoid memory issues
                if page_num > 0 and page_num % 50 == 0:
                    st.info(f"Processed {page_num + 1} pages...")
            
            return "\n".join(text_parts)
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return ""

# Function to clean text more efficiently
def clean_text(text):
    # Use more efficient regex patterns
    text = re.sub(r'\n{3,}', '\n\n', text)  # Replace 3+ newlines with 2
    text = re.sub(r'\s{3,}', ' ', text)     # Replace 3+ spaces with 1
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)  # Remove special chars but keep punctuation
    return text.strip()

# Optimized model loading with device selection
@st.cache_resource
def load_summarizer():
    try:
        device = 0 if torch.cuda.is_available() else -1
        
        # Use a lighter, faster model
        model_name = "facebook/bart-large-cnn"  # Faster than pegasus-xsum
        
        summarizer = pipeline(
            "summarization", 
            model=model_name,
            device=device,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        return summarizer
    except Exception as e:
        st.error(f"Error loading summarizer model: {str(e)}")
        return None

@st.cache_resource
def load_qa_model():
    try:
        device = 0 if torch.cuda.is_available() else -1
        
        # Use a lighter QA model
        qa_model = pipeline(
            "question-answering", 
            model="distilbert-base-cased-distilled-squad",  # Lighter than roberta
            device=device,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        return qa_model
    except Exception as e:
        st.error(f"Error loading QA model: {str(e)}")
        return None

# Faster tokenization with caching
@st.cache_data
def safe_sent_tokenize(text_hash, text):
    try:
        return sent_tokenize(text)
    except LookupError:
        # Simple sentence splitting as fallback
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

@st.cache_data
def safe_word_tokenize(text_hash, text):
    try:
        return word_tokenize(text.lower())
    except LookupError:
        # Simple word splitting as fallback
        return re.findall(r'\b\w+\b', text.lower())

# Optimized key elements extraction
@st.cache_data
def extract_key_elements(text_hash, text, num_sentences=5, num_topics=10):
    # Limit text size for processing
    if len(text) > 50000:  # Limit to ~50K characters
        text = text[:50000]
    
    sentences = safe_sent_tokenize(text_hash, text)
    words = safe_word_tokenize(text_hash, text)
    
    # Use predefined stopwords for speed
    stop_words = {
        'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
        'while', 'of', 'to', 'in', 'for', 'on', 'by', 'with', 'about', 'against',
        'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'from', 'up', 'down', 'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'i', 'me', 'my',
        'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself',
        'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
        'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves'
    }
    
    # Filter words more efficiently
    filtered_words = [word for word in words 
                     if len(word) > 2 and word.isalnum() and word not in stop_words]
    
    # Use Counter instead of FreqDist for better performance
    word_freq = Counter(filtered_words)
    keywords = [word for word, _ in word_freq.most_common(num_topics)]
    
    # Optimize sentence scoring
    keyword_set = set(keywords)
    sentence_scores = []
    
    for sentence in sentences:
        if len(sentence) > 20:  # Skip very short sentences
            sentence_words = set(safe_word_tokenize(hash(sentence), sentence))
            score = len(sentence_words.intersection(keyword_set))
            if score > 0:  # Only include sentences with keywords
                sentence_scores.append((sentence, score))
    
    # Get top sentences
    sentence_scores.sort(key=lambda x: x[1], reverse=True)
    key_sentences = [sentence for sentence, _ in sentence_scores[:num_sentences]]
    
    return key_sentences, keywords

# Faster mind map creation
@st.cache_data
def create_mind_map(topics, central_topic="Main Topic"):
    if len(topics) > 10:  # Limit topics for readability
        topics = topics[:10]
    
    G = nx.Graph()
    G.add_node(central_topic)
    
    for topic in topics:
        G.add_node(topic)
        G.add_edge(central_topic, topic)
    
    # Use smaller figure size for faster rendering
    plt.figure(figsize=(10, 6))
    pos = nx.spring_layout(G, k=2, iterations=20)  # Fewer iterations
    
    nx.draw(G, pos, with_labels=True, node_color='lightblue', 
            node_size=1200, edge_color='gray', linewidths=1, 
            font_size=9, font_weight='bold')
    
    plt.tight_layout()
    
    # Save with lower DPI for faster processing
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close()
    buf.seek(0)
    
    return buf

# Optimized summarization
@st.cache_data
def generate_summary(text_hash, text, _summarizer):
    if not _summarizer:
        # Fast extractive summary fallback
        sentences = safe_sent_tokenize(text_hash, text)
        if len(sentences) > 5:
            return " ".join(sentences[:3]) + "..."
        return text[:500] + "..." if len(text) > 500 else text
    
    try:
        # Optimize chunk size for the model
        max_chunk_length = 1000
        summaries = []
        
        if len(text) > max_chunk_length:
            # Process in smaller, overlapping chunks
            chunk_size = 800
            overlap = 200
            
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size]
                if len(chunk) > 100:
                    try:
                        summary = _summarizer(
                            chunk, 
                            max_length=100, 
                            min_length=30, 
                            do_sample=False,
                            truncation=True
                        )
                        summaries.append(summary[0]['summary_text'])
                    except Exception as e:
                        # Fallback to first sentences
                        chunk_sentences = safe_sent_tokenize(hash(chunk), chunk)
                        summaries.append(" ".join(chunk_sentences[:2]))
                
                # Limit number of chunks processed
                if len(summaries) >= 5:
                    break
            
            return " ".join(summaries)
        else:
            if len(text) > 100:
                summary_output = _summarizer(
                    text, 
                    max_length=150, 
                    min_length=50, 
                    do_sample=False,
                    truncation=True
                )
                return summary_output[0]['summary_text']
            else:
                return text
    except Exception as e:
        st.warning(f"Summarization failed, using extractive summary: {str(e)}")
        sentences = safe_sent_tokenize(text_hash, text)
        return " ".join(sentences[:3]) + "..." if len(sentences) > 3 else text

# Main textbook conversion module
def textbook_conversion_module():
    st.header("Textbook Conversion Module")
    st.subheader("Convert static text to interactive content")
    
    # Initialize session state
    if 'extracted_text' not in st.session_state:
        st.session_state.extracted_text = ""
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    uploaded_file = st.file_uploader("Upload a PDF document", type="pdf")
    
    if uploaded_file is not None:
        # Create hash for caching
        file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()
        
        # Check if we've already processed this file
        if st.session_state.get('file_hash') != file_hash:
            st.session_state.file_hash = file_hash
            st.session_state.processing_complete = False
            st.session_state.extracted_text = ""
        
        if not st.session_state.processing_complete:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Extract text
            status_text.text("Extracting text from PDF...")
            progress_bar.progress(10)
            
            if st.session_state.extracted_text == "":
                text = extract_text_from_pdf(uploaded_file)
                clean_content = clean_text(text)
                st.session_state.extracted_text = clean_content
            
            progress_bar.progress(30)
            
            # Step 2: Extract key elements
            status_text.text("Extracting key elements...")
            key_sentences, keywords = extract_key_elements(
                file_hash, st.session_state.extracted_text
            )
            st.session_state.key_sentences = key_sentences
            st.session_state.keywords = keywords
            
            progress_bar.progress(50)
            
            # Step 3: Load models (cached)
            status_text.text("Loading AI models...")
            summarizer = load_summarizer()
            qa_model = load_qa_model()
            
            progress_bar.progress(70)
            
            # Step 4: Generate summary
            status_text.text("Generating summary...")
            summary = generate_summary(file_hash, st.session_state.extracted_text, summarizer)
            st.session_state.summary = summary
            
            progress_bar.progress(90)
            
            # Step 5: Create visualizations
            status_text.text("Creating visualizations...")
            st.session_state.qa_model = qa_model
            
            progress_bar.progress(100)
            status_text.text("Processing complete!")
            st.session_state.processing_complete = True
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
        
        # Display results
        if st.session_state.processing_complete:
            # Display summary
            st.subheader("📄 Document Summary")
            st.write(st.session_state.summary)
            
            # Key topics with importance
            st.subheader("🔑 Important Topics")
            if st.session_state.keywords:
                keyword_data = pd.DataFrame({
                    'Keyword': st.session_state.keywords[:10],  # Limit to top 10
                    'Importance': range(len(st.session_state.keywords[:10]), 0, -1)
                })
                
                fig = px.bar(
                    keyword_data, 
                    x='Keyword', 
                    y='Importance', 
                    color='Importance',
                    color_continuous_scale='Viridis',
                    title="Top Keywords by Importance"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Mind map
                st.subheader("🧠 Topic Mind Map")
                mind_map_buffer = create_mind_map(
                    st.session_state.keywords[:7], 
                    central_topic=uploaded_file.name.split('.')[0]
                )
                mind_map_image = Image.open(mind_map_buffer)
                st.image(mind_map_image, use_container_width=True)
            else:
                st.warning("No keywords could be extracted from the document.")
            
            # Key components
            st.subheader("💡 Key Components")
            if st.session_state.key_sentences:
                for i, sentence in enumerate(st.session_state.key_sentences):
                    with st.expander(f"Key Point {i+1}"):
                        st.write(sentence)
            else:
                st.warning("No key sentences could be extracted from the document.")
            
            # Q&A system
            st.subheader("❓ Ask Questions About the Content")
            user_question = st.text_input("Enter your question about the content:")
            
            if user_question and st.session_state.get('qa_model'):
                with st.spinner("Generating answer..."):
                    try:
                        # Limit context size for faster processing
                        context = st.session_state.extracted_text[:3000]
                        
                        answer = st.session_state.qa_model({
                            'question': user_question,
                            'context': context
                        })
                        
                        st.success(f"**Answer:** {answer['answer']}")
                        st.info(f"**Confidence:** {answer['score']:.2f}")
                        
                    except Exception as e:
                        st.error(f"Error generating answer: {str(e)}")
                        st.markdown("I couldn't generate an answer. Please try a different question.")
            elif user_question:
                st.warning("Q&A model could not be loaded. Please try again later.")

# Add this if running as main module
if __name__ == "__main__":
    # Initialize NLTK data (run once)
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')
    
    textbook_conversion_module()