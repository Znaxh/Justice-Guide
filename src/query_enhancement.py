from src.prompt_templates import ENHANCED_QUERY_PROMPT_TEMPLATE
import google.generativeai as genai
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
    print("Gemini API configured successfully")
else:
    model = None
    print("Warning: No Gemini API key found. Query enhancement will be disabled.")

def get_enhanced_query(query):
    if not model:
        # If no API key, return the original query
        return query

    try:
        # Create the prompt for Gemini
        prompt = f"{ENHANCED_QUERY_PROMPT_TEMPLATE}\n\nOriginal Query: {query}\n\nEnhanced Query:"

        # Generate response using Gemini
        response = model.generate_content(prompt)
        enhanced_query = response.text.strip()
        return enhanced_query
    except Exception as e:
        print(f"Error enhancing query: {e}")
        # Return original query if enhancement fails
        return query


# print(get_enhanced_query("What is the Indian Penal Code?"))