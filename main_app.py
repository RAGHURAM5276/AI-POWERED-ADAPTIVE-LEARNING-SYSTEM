import streamlit as st
import nltk
from story_processing import main as story_processing_main
from textbook_conversion import textbook_conversion_module
from flashcard_generator10 import FlashcardGenerator, FlashcardPlayer, PDFProcessor
import json

# Download NLTK resources - fixed to use correct resource names
try:
    # Make sure we download the right resources
    nltk.download('punkt')
    nltk.download('stopwords')
except Exception as e:
    st.error(f"Error downloading NLTK resources: {str(e)}")

def story_processing_module():
    """
    Interactive PDF EDU module wrapper.
    """
    story_processing_main()

def flashcard_generator_module():
    """
    Enhanced Flashcard Generator module with PDF/DOCX support and interactive quiz functionality.
    """
    st.header("🃏 Enhanced Interactive Flashcard Generator")
    st.markdown("Generate and practice with interactive flashcards from any text content, including PDF and Word documents!")
    
    # Initialize generators
    generator = FlashcardGenerator()
    player = FlashcardPlayer()
    pdf_processor = PDFProcessor()
    
    # Create tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["📝 Generate Flashcards", "🎯 Practice Quiz", "💾 Import/Export"])
    
    with tab1:
        st.subheader("Generate Flashcards from Multiple Sources")
        
        # Text input options
        input_method = st.selectbox(
            "Choose input method:",
            ["Upload Document", "Paste Text", "Use Extracted Text"]
        )
        
        text_content = ""
        
        if input_method == "Upload Document":
            st.markdown("#### 📁 Upload Your Document")
            uploaded_file = st.file_uploader(
                "Choose a file (PDF, DOCX, or TXT)",
                type=['pdf', 'docx', 'txt'],
                help="Upload a PDF, Word document, or text file to generate flashcards from"
            )
            
            if uploaded_file:
                try:
                    text_content = pdf_processor.process_uploaded_file(uploaded_file)
                    if text_content:
                        st.success(f"File processed successfully! ({len(text_content)} characters)")
                        
                        # Show preview of extracted text
                        with st.expander("📄 Preview of Extracted Text"):
                            preview_text = text_content[:1000] + "..." if len(text_content) > 1000 else text_content
                            st.text_area("Extracted Text Preview", preview_text, height=200, disabled=True)
                    else:
                        st.error("Could not extract text from the uploaded file.")
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
        
        elif input_method == "Paste Text":
            text_content = st.text_area(
                "Paste your text content here:",
                height=200,
                placeholder="Enter the text you want to create flashcards from..."
            )
        
        elif input_method == "Use Extracted Text":
            if st.session_state.get('extracted_text', ''):
                text_content = st.session_state.extracted_text
                st.info(f"Using extracted text ({len(text_content)} characters)")
            else:
                st.warning("No extracted text available. Please use PDF PowerPoint Processor or Textbook Conversion modules first.")
        
        # Flashcard generation options
        if text_content and len(text_content.strip()) >= 100:
            st.markdown("### Flashcard Options")
            
            col1, col2 = st.columns(2)
            with col1:
                card_type = st.selectbox(
                    "Flashcard Type:",
                    ["mixed", "mcq", "true_false", "fill_blank"],
                    format_func=lambda x: {
                        "mixed": "Mixed (Recommended)",
                        "mcq": "Multiple Choice Only",
                        "true_false": "True/False Only", 
                        "fill_blank": "Fill in Blanks Only"
                    }[x]
                )
            
            with col2:
                num_cards = st.slider("Number of Cards:", min_value=5, max_value=50, value=15)
            
            # Advanced options
            with st.expander("⚙️ Advanced Options"):
                if card_type == "mixed":
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        num_mcq = st.slider("MCQ Cards:", 1, 20, max(1, num_cards // 2))
                    with col2:
                        num_tf = st.slider("True/False Cards:", 1, 15, max(1, num_cards // 4))
                    with col3:
                        num_fill = st.slider("Fill Blanks Cards:", 1, 15, max(1, num_cards // 4))
                
                difficulty = st.select_slider(
                    "Difficulty Level:",
                    options=["Easy", "Medium", "Hard"],
                    value="Medium",
                    help="This setting affects question complexity (feature in development)"
                )
            
            # Generate flashcards button
            if st.button("🚀 Generate Flashcards", type="primary"):
                with st.spinner("Generating flashcards..."):
                    try:
                        if card_type == "mixed":
                            flashcards = generator.generate_mixed_flashcards(
                                text_content, num_mcq, num_tf, num_fill
                            )
                        elif card_type == "mcq":
                            flashcards = generator.generate_mcq_flashcards(text_content, num_cards)
                        elif card_type == "true_false":
                            flashcards = generator.generate_true_false_questions(text_content, num_cards)
                        elif card_type == "fill_blank":
                            flashcards = generator.generate_fill_blanks_questions(text_content, num_cards)
                        
                        if flashcards:
                            st.session_state.flashcards = flashcards
                            st.success(f"✨ Generated {len(flashcards)} flashcards successfully!")
                            
                            # Show preview
                            st.subheader("📋 Flashcards Preview")
                            for i, card in enumerate(flashcards[:3]):  # Show first 3 cards
                                with st.expander(f"Card {i+1} - {card['type'].replace('_', ' ').title()}"):
                                    st.write(f"**Question:** {card['question']}")
                                    if card['type'] == 'mcq':
                                        st.write(f"**Options:** {', '.join(card['options'])}")
                                    elif card['type'] == 'true_false':
                                        st.write(f"**Statement Type:** True/False Question")
                                    elif card['type'] == 'fill_blank':
                                        st.write(f"**Type:** Fill in the Blank")
                                    st.write(f"**Answer:** {card['correct_answer']}")
                                    if 'explanation' in card:
                                        st.write(f"**Explanation:** {card['explanation']}")
                            
                            if len(flashcards) > 3:
                                st.info(f"...and {len(flashcards) - 3} more cards!")
                            
                            # Show flashcard types breakdown
                            types = {}
                            for card in flashcards:
                                card_type = card['type']
                                types[card_type] = types.get(card_type, 0) + 1
                            
                            st.write("**Generated Types:**")
                            for card_type, count in types.items():
                                st.write(f"- {card_type.replace('_', ' ').title()}: {count}")
                            
                            st.info("💡 Go to the 'Practice Quiz' tab to start learning!")
                        else:
                            st.warning("Could not generate flashcards. Please try with different text or settings.")
                    
                    except Exception as e:
                        st.error(f"Error generating flashcards: {str(e)}")
        elif text_content and len(text_content.strip()) < 100:
            st.warning("⚠️ The text is too short to generate meaningful flashcards. Please provide more content (at least 100 characters).")
    
    with tab2:
        st.subheader("Practice with Your Flashcards")
        
        if not st.session_state.get('flashcards', []):
            st.info("🔍 No flashcards available. Generate some flashcards first or upload a file for a quick quiz!")
            
            # Quick quiz from file upload
            st.markdown("#### 📁 Quick Quiz from File")
            uploaded_file = st.file_uploader(
                "Upload a file to create a quick quiz:",
                type=['pdf', 'docx', 'txt'],
                help="Upload a document to instantly create and start a quiz",
                key="quick_quiz_upload"
            )
            
            if uploaded_file is not None:
                col1, col2 = st.columns(2)
                with col1:
                    num_questions = st.slider(
                        "Number of questions:",
                        min_value=5,
                        max_value=30,
                        value=10
                    )
                with col2:
                    quiz_type = st.selectbox(
                        "Question type:",
                        ["mixed", "mcq", "true_false", "fill_blank"],
                        format_func=lambda x: {
                            "mixed": "Mixed Questions",
                            "mcq": "Multiple Choice",
                            "true_false": "True/False",
                            "fill_blank": "Fill Blanks"
                        }[x]
                    )
                
                if st.button("📚 Generate and Start Quiz", type="primary"):
                    with st.spinner("Creating quiz from your file..."):
                        try:
                            flashcards = generator.generate_from_file(uploaded_file, quiz_type, num_questions)
                            if flashcards:
                                st.session_state.flashcards = flashcards
                                # Reset quiz state
                                player.reset_quiz()
                                st.success(f"✅ Created quiz with {len(flashcards)} questions!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error creating quiz: {str(e)}")
        else:
            # Quiz statistics
            total_cards = len(st.session_state.flashcards)
            current_pos = st.session_state.get('current_flashcard', 0) + 1
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Cards", total_cards)
            with col2:
                st.metric("Current Position", f"{current_pos}/{total_cards}")
            with col3:
                if st.session_state.get('total_answered', 0) > 0:
                    accuracy = (st.session_state.get('score', 0) / st.session_state.get('total_answered', 1)) * 100
                    st.metric("Accuracy", f"{accuracy:.1f}%")
                else:
                    st.metric("Accuracy", "0%")
            with col4:
                if st.session_state.get('total_answered', 0) > 0:
                    st.metric("Score", f"{st.session_state.get('score', 0)}/{st.session_state.get('total_answered', 0)}")
                else:
                    st.metric("Score", "0/0")
            
            # Quiz interface
            player.play_flashcards()
    
    with tab3:
        st.subheader("Import & Export Flashcards")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📤 Export Flashcards")
            if st.session_state.get('flashcards', []):
                # Display current flashcards info
                st.info(f"Current set: {len(st.session_state.flashcards)} flashcards")
                
                # Show flashcard types breakdown
                if st.session_state.flashcards:
                    types = {}
                    for card in st.session_state.flashcards:
                        card_type = card['type']
                        types[card_type] = types.get(card_type, 0) + 1
                    
                    st.write("**Types breakdown:**")
                    for card_type, count in types.items():
                        st.write(f"- {card_type.replace('_', ' ').title()}: {count}")
                
                if st.button("📥 Export to JSON"):
                    try:
                        b64, json_str = generator.export_flashcards_json(st.session_state.flashcards)
                        if b64 and json_str:
                            st.download_button(
                                label="💾 Download Flashcards",
                                data=json_str,
                                file_name="flashcards.json",
                                mime="application/json"
                            )
                            st.success("✅ Flashcards ready for download!")
                    except Exception as e:
                        st.error(f"Export failed: {str(e)}")
            else:
                st.info("No flashcards to export. Generate some first!")
        
        with col2:
            st.markdown("#### 📥 Import Flashcards")
            uploaded_json = st.file_uploader(
                "Upload JSON flashcards file",
                type=['json'],
                help="Upload a previously exported flashcards JSON file"
            )
            
            if uploaded_json:
                try:
                    json_data = uploaded_json.read().decode('utf-8')
                    imported_flashcards = generator.import_flashcards_json(json_data)
                    
                    if imported_flashcards:
                        st.success(f"Successfully imported {len(imported_flashcards)} flashcards!")
                        
                        # Show import preview
                        st.write("**Preview:**")
                        for i, card in enumerate(imported_flashcards[:2]):
                            st.write(f"Card {i+1}: {card['question'][:50]}...")
                        
                        if len(imported_flashcards) > 2:
                            st.info(f"... and {len(imported_flashcards) - 2} more cards!")
                        
                        if st.button("Use Imported Flashcards"):
                            st.session_state.flashcards = imported_flashcards
                            # Reset quiz state
                            player.reset_quiz()
                            st.success("Flashcards loaded successfully!")
                            st.rerun()
                    
                except Exception as e:
                    st.error(f"Import failed: {str(e)}")
        
        # Sample JSON format
        with st.expander("📋 JSON Format Example"):
            sample_format = [
                {
                    "type": "mcq",
                    "question": "What is the capital of France?",
                    "options": ["London", "Berlin", "Paris", "Madrid"],
                    "correct_answer": "Paris",
                    "correct_index": 2,
                    "explanation": "Paris is the capital and largest city of France."
                },
                {
                    "type": "true_false",
                    "question": "Python is a programming language.",
                    "correct_answer": True,
                    "explanation": "Python is indeed a popular programming language."
                },
                {
                    "type": "fill_blank",
                    "question": "Fill in the blank: The ________ is the largest planet in our solar system.",
                    "correct_answer": "Jupiter",
                    "explanation": "Jupiter is the largest planet in our solar system."
                }
            ]
            st.json(sample_format)

# Main Application
def main():
    st.set_page_config(page_title="AI-Powered Adaptive Learning Platform", 
                      layout="wide", 
                      initial_sidebar_state="expanded")
    
    st.title("AI-Powered Adaptive Learning Platform")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox("Choose a module", 
                                   ["Interactive EDU", 
                                    "Textbook Conversion", 
                                    "Flashcard Generator"])
    
    # Session state initialization
    if 'extracted_text' not in st.session_state:
        st.session_state.extracted_text = ""
    if 'key_sentences' not in st.session_state:
        st.session_state.key_sentences = []
    if 'keywords' not in st.session_state:
        st.session_state.keywords = []
    if 'flashcards' not in st.session_state:
        st.session_state.flashcards = []
    if 'current_flashcard' not in st.session_state:
        st.session_state.current_flashcard = 0
    if 'selected_option' not in st.session_state:
        st.session_state.selected_option = None
    if 'user_answer' not in st.session_state:
        st.session_state.user_answer = ""
    if 'show_answer' not in st.session_state:
        st.session_state.show_answer = False
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'total_answered' not in st.session_state:
        st.session_state.total_answered = 0
    if 'quiz_completed' not in st.session_state:
        st.session_state.quiz_completed = False
    
    # Show app info in sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📚 About")
        st.markdown("Transform documents into interactive learning materials!")
        
        if app_mode == "Interactive EDU":
            st.markdown("### 🎨 Features")
            st.markdown("- **Interactive Slides**: Colorful, animated presentations")
            st.markdown("- **Smart Navigation**: Easy slide-by-slide browsing")
            st.markdown("- **Content Extraction**: Automatic text processing")
            st.markdown("- **Export Options**: Download text and summaries")
            
            st.markdown("### 📊 Presentation Stats")
            st.markdown("- 15 beautiful slides per document")
            st.markdown("- Automatic content segmentation")
            st.markdown("- Visual progress tracking")
            st.markdown("- Multiple gradient themes")
        
        elif app_mode == "Flashcard Generator":
            st.markdown("### 🎯 Quick Tips")
            st.markdown("- **PDF/DOCX Support**: Upload documents directly")
            st.markdown("- **Mixed Mode**: Get variety with different question types")
            st.markdown("- **Export/Import**: Save and share your flashcards")
            st.markdown("- **Quick Quiz**: Upload a file for instant practice")
            
            # Show supported file types
            st.markdown("### 📁 Supported Files")
            st.markdown("- PDF documents (.pdf)")
            st.markdown("- Word documents (.docx)")
            st.markdown("- Text files (.txt)")
    
    # Route to appropriate module
    if app_mode == "Interactive EDU":
        story_processing_module()
    elif app_mode == "Textbook Conversion":
        textbook_conversion_module()
    elif app_mode == "Flashcard Generator":
        flashcard_generator_module()

if __name__ == "__main__":
    main()