import streamlit as st
from src.generate_answers import generate_answer
import time

# Configure page settings
st.set_page_config(
    page_title="JusticeGuide - AI Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark mode styling
st.markdown("""
<style>
    /* Force dark mode for entire app */
    .stApp {
        background-color: #0e1117 !important;
        color: #fafafa !important;
    }

    /* Dark mode for main content */
    .main .block-container {
        background-color: #0e1117 !important;
        color: #fafafa !important;
    }

    /* Dark mode for sidebar */
    .css-1d391kg {
        background-color: #262730 !important;
    }

    .main-header {
        text-align: center;
        color: #00d4ff;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,212,255,0.3);
    }

    .sub-header {
        text-align: center;
        color: #a0a0a0;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-style: italic;
    }

    .question-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,212,255,0.2);
        color: #ffffff;
        border: 1px solid #374151;
    }

    .response-card {
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(168,85,247,0.2);
        color: #ffffff;
        border: 1px solid #374151;
    }

    .example-card {
        background: #1f2937;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #00d4ff;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
        color: #fafafa;
        border: 1px solid #374151;
    }

    .example-card:hover {
        background: #374151;
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(0,212,255,0.3);
    }

    .stats-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin: 0.5rem;
        border: 1px solid #374151;
        box-shadow: 0 2px 8px rgba(0,212,255,0.2);
    }

    .footer {
        text-align: center;
        color: #a0a0a0;
        font-size: 0.9rem;
        margin-top: 3rem;
        padding: 1rem;
        border-top: 1px solid #374151;
    }

    /* Dark mode for input elements */
    .stTextInput > div > div > input {
        background-color: #1f2937 !important;
        color: #fafafa !important;
        border: 1px solid #374151 !important;
    }

    .stTextArea > div > div > textarea {
        background-color: #1f2937 !important;
        color: #fafafa !important;
        border: 1px solid #374151 !important;
    }

    .stSelectbox > div > div > div {
        background-color: #1f2937 !important;
        color: #fafafa !important;
        border: 1px solid #374151 !important;
    }

    /* Dark mode for buttons */
    .stButton > button {
        background-color: #1e3a8a !important;
        color: white !important;
        border: 1px solid #374151 !important;
        border-radius: 8px !important;
    }

    .stButton > button:hover {
        background-color: #3730a3 !important;
        box-shadow: 0 4px 12px rgba(0,212,255,0.3) !important;
    }

    /* Dark mode for expander */
    .streamlit-expanderHeader {
        background-color: #1f2937 !important;
        color: #fafafa !important;
        border: 1px solid #374151 !important;
    }

    .streamlit-expanderContent {
        background-color: #1f2937 !important;
        border: 1px solid #374151 !important;
    }

    /* Dark mode for progress bar */
    .stProgress > div > div > div {
        background-color: #00d4ff !important;
    }

    /* Dark mode for success/error messages */
    .stSuccess {
        background-color: #065f46 !important;
        color: #d1fae5 !important;
        border: 1px solid #10b981 !important;
    }

    .stError {
        background-color: #7f1d1d !important;
        color: #fecaca !important;
        border: 1px solid #ef4444 !important;
    }

    .stWarning {
        background-color: #78350f !important;
        color: #fed7aa !important;
        border: 1px solid #f59e0b !important;
    }

    .stInfo {
        background-color: #1e3a8a !important;
        color: #dbeafe !important;
        border: 1px solid #3b82f6 !important;
    }

    /* Dark mode for markdown */
    .markdown-text-container {
        color: #fafafa !important;
    }

    /* Dark mode for headers */
    h1, h2, h3, h4, h5, h6 {
        color: #fafafa !important;
    }
</style>
""", unsafe_allow_html=True)

# Header section
st.markdown('<h1 class="main-header">⚖️ JusticeGuide</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">🌙 Your AI-Powered Legal Assistant for Indian Penal Code</p>', unsafe_allow_html=True)

# Sidebar with information
with st.sidebar:
    st.markdown("### 🌟 About JusticeGuide")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%); padding: 1rem; border-radius: 10px; margin: 1rem 0; color: white; border: 1px solid #374151;">
    JusticeGuide is an AI-powered legal assistant that helps you understand the Indian Penal Code (IPC).
    </div>

    **🚀 Features:**
    - 🔍 Intelligent query processing
    - 📖 Comprehensive IPC knowledge
    - 🎯 Accurate legal information
    - ⚡ Fast response times
    - 🌙 Dark mode interface
    """)

    st.markdown("### 📊 Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="stats-card"><h3>500+</h3><p>IPC Sections</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="stats-card"><h3>24/7</h3><p>Available</p></div>', unsafe_allow_html=True)

    st.markdown("### 💡 Pro Tips")
    st.markdown("""
    <div style="background: #1f2937; padding: 1rem; border-radius: 10px; border-left: 4px solid #00d4ff; margin: 1rem 0; color: #fafafa;">

    🎯 **Be specific** in your questions<br>
    🔢 **Use section numbers** when known<br>
    ⚖️ **Ask about penalties**, definitions, or procedures<br>
    💬 **Try example questions** to get started<br>
    🌙 **Enjoy the dark mode** experience

    </div>
    """, unsafe_allow_html=True)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🤔 Ask Your Legal Question")

    # Example questions section
    with st.expander("📝 Example Questions", expanded=True):
        example_questions = [
            "What is Indian Penal Code?",
            "What is IPC Section 420?",
            "What are the different sections in IPC?",
            "What is the punishment for theft under IPC?",
            "What constitutes murder under Indian law?",
            "What is the difference between IPC 302 and 304?",
            "What are the provisions for dowry death?",
            "What is criminal breach of trust?"
        ]

        selected_example = st.selectbox(
            "Choose an example question:",
            [""] + example_questions,
            help="Select a pre-written question or write your own below"
        )

    # Question input
    user_question = st.text_area(
        "Enter your legal question:",
        value=selected_example if selected_example else "",
        height=100,
        placeholder="Type your question about Indian Penal Code here...",
        help="Ask anything about IPC sections, definitions, penalties, or legal procedures"
    )

    # Submit button with better styling
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn2:
        submit_button = st.button("🔍 Get Legal Guidance", type="primary", use_container_width=True)

    # Clear button
    with col_btn3:
        if st.button("🗑️ Clear", use_container_width=True):
            st.rerun()

with col2:
    st.markdown("### 🌙 Recent Topics")
    recent_topics = [
        "🔍 IPC Section 420 - Cheating",
        "⚔️ IPC Section 302 - Murder",
        "🚨 IPC Section 376 - Rape",
        "💔 IPC Section 498A - Dowry",
        "⚠️ IPC Section 354 - Assault"
    ]

    for topic in recent_topics:
        st.markdown(f'<div class="example-card">{topic}</div>', unsafe_allow_html=True)

# Response section
if submit_button:
    if user_question.strip():
        # Display the question
        st.markdown('<div class="question-card"><h3>📝 Your Question:</h3><p>' + user_question + '</p></div>', unsafe_allow_html=True)

        # Show loading spinner
        with st.spinner('🔍 Analyzing your question and searching legal database...'):
            # Simulate processing time for better UX
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)

            # Generate response
            response = generate_answer(query=user_question)

        # Display the response
        st.markdown('<div class="response-card"><h3>⚖️ Legal Guidance:</h3></div>', unsafe_allow_html=True)
        st.markdown(f"**Answer:** {response}")

        # Add disclaimer
        st.warning("⚠️ **Disclaimer:** This information is for educational purposes only and should not be considered as legal advice. Please consult with a qualified lawyer for specific legal matters.")

        # Feedback section
        st.markdown("### 📝 Was this helpful?")
        col_feedback1, col_feedback2, col_feedback3 = st.columns(3)
        with col_feedback1:
            if st.button("👍 Yes, helpful"):
                st.success("Thank you for your feedback!")
        with col_feedback2:
            if st.button("👎 Not helpful"):
                st.info("We'll work on improving our responses!")
        with col_feedback3:
            if st.button("💬 Need clarification"):
                st.info("Please feel free to ask a follow-up question!")
    else:
        st.error("⚠️ Please enter a question before submitting.")

# Footer
st.markdown("""
<div class="footer">
    <p>🌙 © 2024 JusticeGuide - AI Legal Assistant | Powered by Google Gemini |
    <strong>For Educational Purposes Only</strong></p>
    <p>🔒 Your privacy is protected | 📞 Contact: support@justiceguide.ai | 🌙 Dark Mode Enabled</p>
</div>
""", unsafe_allow_html=True)
