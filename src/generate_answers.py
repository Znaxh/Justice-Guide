from src.reranker import get_reranked_docs
from src.query_enhancement import get_enhanced_query
import google.generativeai as genai
from src.prompt_templates import GENERATE_ANSWER_PROMPT_TEMPLATE
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Gemini API key from environment variable
api_key = os.getenv('GEMINI_API_KEY')

# Initialize Gemini client
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("Gemini API configured successfully for answer generation")
else:
    model = None
    print("Warning: No Gemini API key found. Answer generation will use fallback responses.")

def generate_answer(query):
    if not model:
        return "Error: Gemini API key not configured. Please set GEMINI_API_KEY environment variable."

    try:
        enhanced_query = get_enhanced_query(query)
        retrieve_and_rerank = get_reranked_docs(enhanced_query)
        context = "\n\n".join(retrieve_and_rerank)  # Combine excerpts into a single string

        # Create the prompt for Gemini
        prompt = GENERATE_ANSWER_PROMPT_TEMPLATE.format(context=context, enhanced_query=enhanced_query)

        # Generate response using Gemini
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating answer: {str(e)}"

# print(generate_answer("what is indian panel code?"))