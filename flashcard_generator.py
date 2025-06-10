import streamlit as st
import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
import random
import json
import base64
import io
import PyPDF2
from docx import Document
import tempfile

# Configure page
st.set_page_config(
    page_title="AI Flashcard Generator",
    page_icon="🎓",
    layout="wide"
)

class DocumentProcessor:
    """Handle various document formats"""
    
    @staticmethod
    def extract_text_from_pdf(uploaded_file):
        """Extract text from PDF file"""
        try:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # Extract text using PyPDF2
            text = ""
            with open(tmp_file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
            return None
    
    @staticmethod
    def extract_text_from_docx(uploaded_file):
        """Extract text from DOCX file"""
        try:
            doc = Document(io.BytesIO(uploaded_file.getvalue()))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            st.error(f"Error reading DOCX: {str(e)}")
            return None
    
    @staticmethod
    def extract_text_from_txt(uploaded_file):
        """Extract text from TXT file"""
        try:
            return uploaded_file.getvalue().decode('utf-8')
        except Exception as e:
            st.error(f"Error reading TXT: {str(e)}")
            return None

class FlashcardGenerator:
    """Generate flashcards from text content"""
    
    def __init__(self):
        self.download_nltk_resources()
    
    def download_nltk_resources(self):
        """Download required NLTK resources"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        except:
            pass
    
    def safe_sent_tokenize(self, text):
        """Safe sentence tokenization with fallback"""
        try:
            return sent_tokenize(text)
        except:
            return [s.strip() + '.' for s in text.split('.') if s.strip()]
    
    def safe_word_tokenize(self, text):
        """Safe word tokenization with fallback"""
        try:
            return word_tokenize(text.lower())
        except:
            return text.lower().split()
    
    def get_stopwords(self):
        """Get stopwords with fallback"""
        try:
            return set(stopwords.words('english'))
        except:
            return {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
                    'while', 'of', 'to', 'in', 'for', 'on', 'by', 'with', 'about', 'is', 'are'}
    
    def extract_keywords(self, text, num_keywords=20):
        """Extract keywords from text"""
        words = self.safe_word_tokenize(text)
        stop_words = self.get_stopwords()
        
        filtered_words = [word for word in words 
                         if word.isalnum() and word not in stop_words and len(word) > 3]
        
        fdist = FreqDist(filtered_words)
        return [word for word, _ in fdist.most_common(num_keywords)]
    
    def extract_key_sentences(self, text, num_sentences=25):
        """Extract key sentences from text"""
        sentences = self.safe_sent_tokenize(text)
        keywords = self.extract_keywords(text)
        
        sentence_scores = []
        for sentence in sentences:
            if len(sentence.split()) >= 8:
                score = sum(1 for word in self.safe_word_tokenize(sentence) if word in keywords)
                sentence_scores.append((sentence, score))
        
        top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:num_sentences]
        return [sentence for sentence, _ in top_sentences], keywords
    
    def create_mcq_from_sentence(self, sentence, keywords):
        """Create MCQ from sentence"""
        words = self.safe_word_tokenize(sentence)
        stop_words = self.get_stopwords()
        content_words = [word for word in words 
                        if word.isalnum() and word not in stop_words and len(word) > 3]
        
        if not content_words:
            return None
        
        target_word = random.choice(content_words)
        question_text = sentence.replace(target_word, "________", 1)
        
        potential_distractors = [w for w in keywords if w != target_word and len(w) > 2]
        if len(potential_distractors) < 3:
            general_distractors = ["concept", "element", "process", "method", "system", 
                                  "principle", "approach", "structure", "model", "theory"]
            potential_distractors.extend(general_distractors)
        
        distractors = random.sample(potential_distractors, min(3, len(potential_distractors)))
        options = distractors + [target_word]
        random.shuffle(options)
        
        return {
            "type": "mcq",
            "question": f"Complete the sentence: {question_text}",
            "options": options,
            "correct_answer": target_word,
            "correct_index": options.index(target_word),
            "explanation": f"The correct answer is '{target_word}' based on the context."
        }
    
    def create_true_false_from_sentence(self, sentence, keywords):
        """Create True/False question from sentence"""
        if len(sentence.split()) < 8:
            return None
        
        # True question (original sentence)
        true_q = {
            "type": "true_false",
            "question": sentence,
            "correct_answer": True,
            "explanation": "This statement is directly from the source text."
        }
        
        # False question (modified sentence)
        words = sentence.split()
        content_words = [w for w in words if w.lower() not in self.get_stopwords() and len(w) > 3]
        
        if content_words and keywords:
            for word in content_words:
                replacement = random.choice(keywords)
                if replacement.lower() != word.lower():
                    modified_sentence = sentence.replace(word, replacement, 1)
                    false_q = {
                        "type": "true_false",
                        "question": modified_sentence,
                        "correct_answer": False,
                        "explanation": "This statement has been modified from the original text."
                    }
                    return [true_q, false_q]
        
        return [true_q]
    
    def create_fill_blank_from_sentence(self, sentence, keywords):
        """Create fill-in-the-blank question from sentence"""
        if len(sentence.split()) < 10:
            return None
        
        words = sentence.split()
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in keywords and len(clean_word) > 3:
                blanked_words = words.copy()
                blanked_words[i] = "________"
                blanked_sentence = " ".join(blanked_words)
                
                return {
                    "type": "fill_blank",
                    "question": f"Fill in the blank: {blanked_sentence}",
                    "correct_answer": word,
                    "explanation": f"The correct word is '{word}' based on the context."
                }
        return None
    
    def generate_flashcards(self, text, num_mcq=8, num_tf=4, num_fill=3):
        """Generate mixed flashcards"""
        if not text or len(text.strip()) < 100:
            return []
        
        key_sentences, keywords = self.extract_key_sentences(text)
        if not key_sentences:
            return []
        
        all_cards = []
        
        # Generate MCQ cards
        for sentence in key_sentences[:num_mcq * 2]:
            mcq = self.create_mcq_from_sentence(sentence, keywords)
            if mcq:
                all_cards.append(mcq)
                if len([c for c in all_cards if c['type'] == 'mcq']) >= num_mcq:
                    break
        
        # Generate True/False cards
        tf_count = 0
        for sentence in key_sentences:
            if tf_count >= num_tf:
                break
            tf_questions = self.create_true_false_from_sentence(sentence, keywords)
            if tf_questions:
                all_cards.extend(tf_questions[:num_tf - tf_count])
                tf_count += len(tf_questions[:num_tf - tf_count])
        
        # Generate Fill-in-the-blank cards
        for sentence in key_sentences:
            if len([c for c in all_cards if c['type'] == 'fill_blank']) >= num_fill:
                break
            fill_q = self.create_fill_blank_from_sentence(sentence, keywords)
            if fill_q:
                all_cards.append(fill_q)
        
        random.shuffle(all_cards)
        return all_cards[:num_mcq + num_tf + num_fill]

class FlashcardPlayer:
    """Handle flashcard quiz interface"""
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize session state"""
        defaults = {
            'flashcards': [],
            'current_card': 0,
            'selected_option': None,
            'user_answer': "",
            'show_answer': False,
            'score': 0,
            'total_answered': 0,
            'quiz_completed': False
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def reset_quiz(self):
        """Reset quiz state"""
        st.session_state.current_card = 0
        st.session_state.selected_option = None
        st.session_state.user_answer = ""
        st.session_state.show_answer = False
        st.session_state.score = 0
        st.session_state.total_answered = 0
        st.session_state.quiz_completed = False
    
    def display_question_card(self, card):
        """Display question in card format"""
        # Card container with enhanced styling
        st.markdown("""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 15px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            color: white;
            min-height: 150px;
            display: flex;
            align-items: center;
            justify-content: center;
        '>
            <h2 style='text-align: center; margin: 0; font-weight: 300;'>""" + card['question'] + """</h2>
        </div>
        """, unsafe_allow_html=True)
        
        if card['type'] == 'mcq':
            self.display_mcq_options(card)
        elif card['type'] == 'true_false':
            self.display_tf_options(card)
        elif card['type'] == 'fill_blank':
            self.display_fill_blank_input(card)
    
    def display_mcq_options(self, card):
        """Display MCQ options"""
        if not st.session_state.show_answer:
            st.markdown("<h4>Choose the correct answer:</h4>", unsafe_allow_html=True)
            
            for i, option in enumerate(card['options']):
                col1, col2 = st.columns([1, 10])
                with col2:
                    if st.button(f"{chr(65+i)}. {option}", key=f"mcq_{i}", use_container_width=True):
                        st.session_state.selected_option = i
                        st.session_state.show_answer = True
                        if i == card['correct_index']:
                            st.session_state.score += 1
                        st.session_state.total_answered += 1
                        st.rerun()
        else:
            # Show results
            for i, option in enumerate(card['options']):
                if i == card['correct_index']:
                    st.markdown(f"""
                    <div style='background-color: #d4edda; padding: 15px; border-radius: 8px; margin: 5px 0; border-left: 5px solid #28a745;'>
                        <strong>{chr(65+i)}. {option}</strong> ✅ Correct!
                    </div>
                    """, unsafe_allow_html=True)
                elif i == st.session_state.selected_option:
                    st.markdown(f"""
                    <div style='background-color: #f8d7da; padding: 15px; border-radius: 8px; margin: 5px 0; border-left: 5px solid #dc3545;'>
                        <strong>{chr(65+i)}. {option}</strong> ❌ Your Answer
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 5px 0;'>
                        {chr(65+i)}. {option}
                    </div>
                    """, unsafe_allow_html=True)
    
    def display_tf_options(self, card):
        """Display True/False options"""
        if not st.session_state.show_answer:
            st.markdown("<h4>Is this statement True or False?</h4>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ True", key="tf_true", use_container_width=True):
                    st.session_state.selected_option = True
                    st.session_state.show_answer = True
                    if card['correct_answer']:
                        st.session_state.score += 1
                    st.session_state.total_answered += 1
                    st.rerun()
            
            with col2:
                if st.button("❌ False", key="tf_false", use_container_width=True):
                    st.session_state.selected_option = False
                    st.session_state.show_answer = True
                    if not card['correct_answer']:
                        st.session_state.score += 1
                    st.session_state.total_answered += 1
                    st.rerun()
        else:
            # Show results
            correct = "True" if card['correct_answer'] else "False"
            user_choice = "True" if st.session_state.selected_option else "False"
            
            if st.session_state.selected_option == card['correct_answer']:
                st.markdown(f"""
                <div style='background-color: #d4edda; padding: 20px; border-radius: 10px; text-align: center;'>
                    <h3>✅ Correct!</h3>
                    <p>The answer is <strong>{correct}</strong></p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background-color: #f8d7da; padding: 20px; border-radius: 10px; text-align: center;'>
                    <h3>❌ Incorrect</h3>
                    <p>You answered <strong>{user_choice}</strong>, but the correct answer is <strong>{correct}</strong></p>
                </div>
                """, unsafe_allow_html=True)
    
    def display_fill_blank_input(self, card):
        """Display fill-in-the-blank input"""
        if not st.session_state.show_answer:
            st.markdown("<h4>Fill in the blank:</h4>", unsafe_allow_html=True)
            
            user_input = st.text_input("Your answer:", key="fill_input", placeholder="Type your answer here...")
            
            if st.button("Submit Answer", key="fill_submit"):
                st.session_state.user_answer = user_input.strip()
                st.session_state.show_answer = True
                
                correct_answer = re.sub(r'[^\w]', '', card['correct_answer'].lower())
                user_answer_clean = re.sub(r'[^\w]', '', user_input.lower())
                
                if correct_answer == user_answer_clean:
                    st.session_state.score += 1
                st.session_state.total_answered += 1
                st.rerun()
        else:
            # Show results
            correct_answer = re.sub(r'[^\w]', '', card['correct_answer'].lower())
            user_answer_clean = re.sub(r'[^\w]', '', st.session_state.user_answer.lower())
            
            if correct_answer == user_answer_clean:
                st.markdown(f"""
                <div style='background-color: #d4edda; padding: 20px; border-radius: 10px; text-align: center;'>
                    <h3>✅ Correct!</h3>
                    <p>The answer is <strong>{card['correct_answer']}</strong></p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background-color: #f8d7da; padding: 20px; border-radius: 10px; text-align: center;'>
                    <h3>❌ Incorrect</h3>
                    <p>You answered <strong>"{st.session_state.user_answer}"</strong><br>
                    The correct answer is <strong>"{card['correct_answer']}"</strong></p>
                </div>
                """, unsafe_allow_html=True)
    
    def display_progress_stats(self):
        """Display progress and statistics"""
        if not st.session_state.flashcards:
            return
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Cards", len(st.session_state.flashcards))
        
        with col2:
            st.metric("Current Position", f"{st.session_state.current_card + 1}/{len(st.session_state.flashcards)}")
        
        with col3:
            if st.session_state.total_answered > 0:
                accuracy = (st.session_state.score / st.session_state.total_answered) * 100
                st.metric("Accuracy", f"{accuracy:.1f}%")
            else:
                st.metric("Accuracy", "0.0%")
        
        with col4:
            st.metric("Score", f"{st.session_state.score}/{st.session_state.total_answered}")
        
        # Progress bar
        progress = (st.session_state.current_card + 1) / len(st.session_state.flashcards)
        st.progress(progress)
    
    def display_navigation(self):
        """Display navigation controls"""
        if not st.session_state.flashcards:
            return
        
        st.markdown("---")
        
        # Navigation buttons
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
        
        with col1:
            if st.button("⬅️ Previous", disabled=st.session_state.current_card == 0):
                st.session_state.current_card -= 1
                st.session_state.selected_option = None
                st.session_state.user_answer = ""
                st.session_state.show_answer = False
                st.rerun()
        
        with col2:
            if st.session_state.current_card == len(st.session_state.flashcards) - 1:
                if st.button("🏁 Finish Quiz"):
                    st.session_state.quiz_completed = True
                    st.rerun()
            else:
                if st.button("Next ➡️"):
                    st.session_state.current_card += 1
                    st.session_state.selected_option = None
                    st.session_state.user_answer = ""
                    st.session_state.show_answer = False
                    st.rerun()
        
        with col3:
            if st.button("🔄 Reset Quiz"):
                self.reset_quiz()
                st.rerun()
        
        with col4:
            if st.button("🔀 Shuffle"):
                random.shuffle(st.session_state.flashcards)
                self.reset_quiz()
                st.rerun()
        
        with col5:
            if st.button("📊 Show Stats"):
                st.session_state.show_stats = not getattr(st.session_state, 'show_stats', False)
                st.rerun()
    
    def display_quiz_results(self):
        """Display final quiz results"""
        if st.session_state.quiz_completed and st.session_state.total_answered > 0:
            st.balloons()
            
            score_percentage = (st.session_state.score / st.session_state.total_answered) * 100
            
            st.markdown("## 🎉 Quiz Completed!")
            
            # Results display
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 40px;
                    border-radius: 20px;
                    text-align: center;
                    color: white;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                '>
                    <h1>Final Score</h1>
                    <h2>{st.session_state.score}/{st.session_state.total_answered}</h2>
                    <h3>({score_percentage:.1f}%)</h3>
                </div>
                """, unsafe_allow_html=True)
            
            # Performance feedback
            st.markdown("<br>", unsafe_allow_html=True)
            if score_percentage >= 90:
                st.success("🌟 **Excellent!** You have mastered this material!")
            elif score_percentage >= 80:
                st.success("👍 **Great job!** You have a solid understanding.")
            elif score_percentage >= 70:
                st.warning("👌 **Good work!** Consider reviewing some concepts.")
            else:
                st.error("📚 **Keep studying!** Review the material and try again.")
            
            if st.button("🚀 Start New Quiz", use_container_width=True):
                self.reset_quiz()
                st.rerun()
    
    def play_flashcards(self):
        """Main flashcard interface"""
        if st.session_state.quiz_completed:
            self.display_quiz_results()
        elif st.session_state.flashcards:
            self.display_progress_stats()
            
            current_card = st.session_state.flashcards[st.session_state.current_card]
            st.subheader(f"Question {st.session_state.current_card + 1}/{len(st.session_state.flashcards)}")
            
            self.display_question_card(current_card)
            
            # Show explanation if answer is revealed
            if st.session_state.show_answer and 'explanation' in current_card:
                st.info(f"💡 **Explanation:** {current_card['explanation']}")
            
            self.display_navigation()
        else:
            st.warning("📝 No flashcards available. Please generate some first!")

# Main Application
def main():
    st.title("🎓 AI-Powered Flashcard Generator")
    st.markdown("Upload documents, generate smart flashcards, and test your knowledge!")
    
    # Initialize components
    doc_processor = DocumentProcessor()
    generator = FlashcardGenerator()
    player = FlashcardPlayer()
    
    # Sidebar for file upload and settings
    with st.sidebar:
        st.header("📁 Upload Document")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'docx', 'txt'],
            help="Upload PDF, DOCX, or TXT files"
        )
        
        st.header("⚙️ Settings")
        num_mcq = st.slider("MCQ Questions", 3, 15, 8)
        num_tf = st.slider("True/False Questions", 2, 10, 4)
        num_fill = st.slider("Fill-in-the-blank Questions", 1, 8, 3)
        
        if st.button("🎯 Generate Flashcards", use_container_width=True):
            if uploaded_file:
                with st.spinner("Processing document..."):
                    # Extract text based on file type
                    if uploaded_file.type == "application/pdf":
                        text = doc_processor.extract_text_from_pdf(uploaded_file)
                    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        text = doc_processor.extract_text_from_docx(uploaded_file)
                    elif uploaded_file.type == "text/plain":
                        text = doc_processor.extract_text_from_txt(uploaded_file)
                    else:
                        st.error("Unsupported file type!")
                        text = None
                    
                    if text:
                        with st.spinner("Generating flashcards..."):
                            flashcards = generator.generate_flashcards(text, num_mcq, num_tf, num_fill)
                            if flashcards:
                                st.session_state.flashcards = flashcards
                                player.reset_quiz()
                                st.success(f"✅ Generated {len(flashcards)} flashcards!")
                                st.rerun()
                            else:
                                st.error("❌ Could not generate flashcards. Try with a longer document.")
            else:
                st.warning("⚠️ Please upload a document first!")
        
        # Manual text input option
        st.header("✏️ Or Enter Text")
        manual_text = st.text_area("Paste your text here:", height=100)
        if st.button("Generate from Text", use_container_width=True):
            if manual_text:
                with st.spinner("Generating flashcards..."):
                    flashcards = generator.generate_flashcards(manual_text, num_mcq, num_tf, num_fill)
                    if flashcards:
                        st.session_state.flashcards = flashcards
                        player.reset_quiz()
                        st.success(f"✅ Generated {len(flashcards)} flashcards!")
                        st.rerun()
                    else:
                        st.error("❌ Could not generate flashcards. Try with longer text.")
            else:
                st.warning("⚠️ Please enter some text first!")
    
    # Main content area
    if st.session_state.flashcards:
        player.play_flashcards()
    else:
        # Welcome screen
        st.markdown("""
        <div style='text-align: center; padding: 50px;'>
            <h2>🚀 Get Started</h2>
            <p style='font-size: 18px;'>Upload a document or enter text to generate interactive flashcards!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature highlights
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style='text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px;'>
                <h3>📄 Multi-Format Support</h3>
                <p>PDF, DOCX, and TXT files supported</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style='text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px;'>
                <h3>🧠 Smart Questions</h3>
                <p>MCQ, True/False, and Fill-in-the-blank</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style='text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px;'>
                <h3>📊 Track Progress</h3>
                <p>Real-time scoring and feedback</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()