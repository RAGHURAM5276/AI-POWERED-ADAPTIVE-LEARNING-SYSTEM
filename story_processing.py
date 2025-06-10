import streamlit as st
import fitz  # PyMuPDF
import re
import time
from datetime import datetime

# Custom CSS for PowerPoint-style slides
def load_slide_css():
    return """
    <style>
    .slide-container {
        width: 100%;
        height: 500px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        position: relative;
        overflow: hidden;
        animation: slideIn 0.8s ease-out;
    }
    
    .slide-title {
        font-size: 2.5em;
        font-weight: bold;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        animation: titleFadeIn 1s ease-out 0.3s both;
    }
    
    .slide-content {
        font-size: 1.2em;
        line-height: 1.6;
        color: white;
        text-align: justify;
        animation: contentSlideUp 1s ease-out 0.6s both;
        max-height: 350px;
        overflow-y: auto;
        padding-right: 10px;
    }
    
    .slide-number {
        position: absolute;
        top: 15px;
        right: 25px;
        background: rgba(255,255,255,0.2);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .intro-slide {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        text-align: center;
    }
    
    .content-slide-1 { background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%); }
    .content-slide-2 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .content-slide-3 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .content-slide-4 { background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); }
    .content-slide-5 { background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); }
    .content-slide-6 { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .content-slide-7 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .content-slide-8 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .content-slide-9 { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .content-slide-10 { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .summary-slide { background: linear-gradient(135deg, #30cfd0 0%, #91a7ff 100%); }
    .conclusion-slide { background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); }
    
    @keyframes slideIn {
        from { transform: translateX(-100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes titleFadeIn {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes contentSlideUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .progress-bar {
        width: 100%;
        height: 8px;
        background: rgba(255,255,255,0.3);
        border-radius: 4px;
        margin: 20px 0;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #00f2fe, #4facfe);
        border-radius: 4px;
        transition: width 0.3s ease;
    }
    
    .navigation-buttons {
        display: flex;
        justify-content: space-between;
        margin-top: 20px;
    }
    
    .nav-button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 25px;
        cursor: pointer;
        font-weight: bold;
        transition: transform 0.2s;
    }
    
    .nav-button:hover {
        transform: scale(1.05);
    }
    
    .interactive-element {
        background: rgba(255,255,255,0.1);
        border: 2px solid rgba(255,255,255,0.3);
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        backdrop-filter: blur(10px);
    }
    
    .highlight-box {
        background: rgba(255,255,255,0.2);
        border-left: 5px solid #fff;
        padding: 15px;
        margin: 15px 0;
        border-radius: 5px;
    }
    </style>
    """

def extract_text_from_pdf(file):
    """Extract text from uploaded PDF file"""
    try:
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            text = ""
            page_count = len(doc)
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
            return text, page_count
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return "", 0

def clean_and_segment_text(text):
    """Clean text and segment into meaningful chunks"""
    # Basic cleaning
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Split into paragraphs and filter meaningful content
    paragraphs = re.split(r'\n\s*\n|--- Page \d+ ---', text)
    paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 50]
    
    return paragraphs

def create_title_slide(filename):
    """Create the title slide"""
    current_time = datetime.now().strftime("%B %d, %Y")
    return f"""
    <div class="slide-container intro-slide">
        <div class="slide-number">1 / 15</div>
        <div class="slide-title">📄 {filename}</div>
        <div class="slide-content">
            <div class="interactive-element">
                <h3>📊 Interactive PDF Presentation</h3>
                <p>🎯 <strong>Objective:</strong> Transform PDF content into engaging slides</p>
                <p>📅 <strong>Date:</strong> {current_time}</p>
                <p>🔍 <strong>Features:</strong> Interactive learning, colorful design, comprehensive content extraction</p>
            </div>
        </div>
    </div>
    """

def create_content_slide(content, slide_num, total_slides, title="Content"):
    """Create individual content slides with different themes"""
    slide_class = f"content-slide-{((slide_num - 2) % 10) + 1}"
    
    # Extract key points if content is long
    if len(content) > 500:
        sentences = content.split('. ')
        key_points = sentences[:3] if len(sentences) >= 3 else sentences
        content_display = '. '.join(key_points) + '.'
        if len(sentences) > 3:
            content_display += f"\n\n📝 Plus {len(sentences) - 3} more key insights..."
    else:
        content_display = content
    
    return f"""
    <div class="slide-container {slide_class}">
        <div class="slide-number">{slide_num} / {total_slides}</div>
        <div class="slide-title">{title} {slide_num - 1}</div>
        <div class="slide-content">
            <div class="highlight-box">
                <p>{content_display}</p>
            </div>
            <div class="interactive-element">
                <p>💡 <strong>Learning Tip:</strong> This section contains {len(content.split())} words and {len(content.split('.'))} sentences.</p>
            </div>
        </div>
    </div>
    """

def create_summary_slide(total_pages, total_words, key_topics):
    """Create summary slide"""
    return f"""
    <div class="slide-container summary-slide">
        <div class="slide-number">14 / 15</div>
        <div class="slide-title">📊 Document Summary</div>
        <div class="slide-content">
            <div class="interactive-element">
                <h3>📈 Statistics</h3>
                <p>📄 <strong>Total Pages:</strong> {total_pages}</p>
                <p>📝 <strong>Total Words:</strong> {total_words:,}</p>
                <p>📑 <strong>Content Sections:</strong> {len(key_topics)}</p>
            </div>
            <div class="highlight-box">
                <h4>🎯 Key Topics Covered:</h4>
                <ul>
                    {"".join([f"<li>Topic {i+1}: {topic[:50]}...</li>" for i, topic in enumerate(key_topics[:5])])}
                </ul>
            </div>
        </div>
    </div>
    """

def create_conclusion_slide():
    """Create conclusion slide"""
    return f"""
    <div class="slide-container conclusion-slide">
        <div class="slide-number">15 / 15</div>
        <div class="slide-title">🎉 Thank You!</div>
        <div class="slide-content">
            <div class="interactive-element">
                <h3>✅ Presentation Complete</h3>
                <p>🎊 You have successfully processed and viewed the PDF content through an interactive slideshow experience.</p>
                <p>🔄 Use the navigation controls to review any slides.</p>
                <p>💾 All content has been extracted and organized for easy comprehension.</p>
            </div>
            <div class="highlight-box">
                <h4>🚀 Next Steps:</h4>
                <p>• Review key sections using the slide navigator</p>
                <p>• Export content for further analysis</p>
                <p>• Process additional documents</p>
            </div>
        </div>
    </div>
    """

def main():
    # REMOVED st.set_page_config() from here since it's already called in main_app.py
    
    st.title("📊 Interactive  Edu")
    st.markdown("Transform your PDF documents into engaging, colorful presentation slides!")
    
    # File upload
    uploaded_file = st.file_uploader("Upload your PDF document", type="pdf")
    
    if uploaded_file is not None:
        filename = uploaded_file.name.replace('.pdf', '')
        
        # Process PDF
        with st.spinner("🔄 Processing PDF and creating slides..."):
            text, page_count = extract_text_from_pdf(uploaded_file)
            
            if text:
                paragraphs = clean_and_segment_text(text)
                total_words = len(text.split())
                
                # Store extracted text in session state for other modules
                st.session_state.extracted_text = text
                
                # Store in session state
                if 'slides_data' not in st.session_state:
                    st.session_state.slides_data = {
                        'paragraphs': paragraphs,
                        'filename': filename,
                        'page_count': page_count,
                        'total_words': total_words,
                        'current_slide': 0
                    }
                
                # Load CSS
                st.markdown(load_slide_css(), unsafe_allow_html=True)
                
                # Navigation controls
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                
                with col1:
                    if st.button("⏮️ First"):
                        st.session_state.slides_data['current_slide'] = 0
                
                with col2:
                    if st.button("⬅️ Previous"):
                        if st.session_state.slides_data['current_slide'] > 0:
                            st.session_state.slides_data['current_slide'] -= 1
                
                with col3:
                    slide_options = [f"Slide {i+1}" for i in range(15)]
                    selected_slide = st.selectbox(
                        "Select Slide:",
                        slide_options,
                        index=st.session_state.slides_data['current_slide']
                    )
                    st.session_state.slides_data['current_slide'] = slide_options.index(selected_slide)
                
                with col4:
                    if st.button("➡️ Next"):
                        if st.session_state.slides_data['current_slide'] < 14:
                            st.session_state.slides_data['current_slide'] += 1
                
                with col5:
                    if st.button("⏭️ Last"):
                        st.session_state.slides_data['current_slide'] = 14
                
                # Progress bar
                progress = (st.session_state.slides_data['current_slide'] + 1) / 15 * 100
                st.markdown(f"""
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {progress}%;"></div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display current slide
                current_slide = st.session_state.slides_data['current_slide']
                
                if current_slide == 0:
                    # Title slide
                    slide_html = create_title_slide(filename)
                elif current_slide == 13:
                    # Summary slide
                    slide_html = create_summary_slide(
                        page_count, 
                        total_words, 
                        paragraphs[:5]
                    )
                elif current_slide == 14:
                    # Conclusion slide
                    slide_html = create_conclusion_slide()
                else:
                    # Content slides (slides 2-13)
                    content_index = current_slide - 1
                    if content_index < len(paragraphs):
                        content = paragraphs[content_index]
                    else:
                        # If we have fewer paragraphs, create a filler slide
                        content = f"Additional content section {content_index + 1}. This document contains valuable information across {page_count} pages with comprehensive coverage of the topic."
                    
                    slide_html = create_content_slide(
                        content, 
                        current_slide + 1, 
                        15, 
                        f"Section"
                    )
                
                # Display the slide
                st.markdown(slide_html, unsafe_allow_html=True)
                
                # Additional information
                with st.expander("📋 Document Information"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📄 Total Pages", page_count)
                    with col2:
                        st.metric("📝 Total Words", f"{total_words:,}")
                    with col3:
                        st.metric("📑 Content Sections", len(paragraphs))
                
                # Export options
                st.markdown("### 💾 Export Options")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📥 Download Extracted Text"):
                        st.download_button(
                            label="Download as TXT",
                            data=text,
                            file_name=f"{filename}_extracted.txt",
                            mime="text/plain"
                        )
                
                with col2:
                    if st.button("📊 Generate Slide Summary"):
                        summary_text = f"""
PDF Presentation Summary
========================
Document: {filename}
Pages: {page_count}
Words: {total_words:,}
Slides Generated: 15

Content Overview:
{chr(10).join([f"Section {i+1}: {p[:100]}..." for i, p in enumerate(paragraphs[:10])])}
                        """
                        st.download_button(
                            label="Download Summary",
                            data=summary_text,
                            file_name=f"{filename}_summary.txt",
                            mime="text/plain"
                        )

if __name__ == "__main__":
    main()