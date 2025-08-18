import pandas as pd
import re
import os
import pickle
from pathlib import Path
from typing import List
import PyPDF2
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Global variables for caching
embeddings_model = None
document_chunks = None
embeddings_index = None
chunk_texts = None

def initialize_document_system():
    """Initialize the document retrieval system with embeddings"""
    global embeddings_model, document_chunks, embeddings_index, chunk_texts

    if embeddings_model is None:
        print("Loading sentence transformer model...")
        embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Sentence transformer model loaded successfully")

    # Check if we have cached embeddings
    cache_file = "document_embeddings.pkl"
    if os.path.exists(cache_file):
        print("Loading cached document embeddings...")
        with open(cache_file, 'rb') as f:
            cached_data = pickle.load(f)
            chunk_texts = cached_data['chunk_texts']
            embeddings_index = cached_data['embeddings_index']
        print(f"Loaded {len(chunk_texts)} cached document chunks")
    else:
        print("Processing PDF documents and creating embeddings...")
        chunk_texts, embeddings_index = process_pdf_documents()

        # Cache the embeddings for faster startup next time
        print("Caching embeddings for faster future startup...")
        with open(cache_file, 'wb') as f:
            pickle.dump({
                'chunk_texts': chunk_texts,
                'embeddings_index': embeddings_index
            }, f)
        print("Embeddings cached successfully")

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

def process_pdf_documents():
    """Process all PDF chunks and create embeddings"""
    dataset_path = Path("dataset/Indian Penal Code Book (2)_chunks")

    if not dataset_path.exists():
        print(f"Dataset path {dataset_path} not found. Using sample data.")
        return get_sample_data()

    chunk_texts = []
    pdf_files = list(dataset_path.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF chunks to process...")

    for pdf_file in sorted(pdf_files):
        text = extract_text_from_pdf(pdf_file)
        if text:
            # Split large chunks into smaller pieces for better retrieval
            text_chunks = split_text_into_chunks(text, max_length=1000)
            chunk_texts.extend(text_chunks)

    if not chunk_texts:
        print("No text extracted from PDFs. Using sample data.")
        return get_sample_data()

    print(f"Extracted {len(chunk_texts)} text chunks from PDFs")

    # Create embeddings
    print("Creating embeddings for document chunks...")
    embeddings = embeddings_model.encode(chunk_texts, show_progress_bar=True)

    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity

    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)
    index.add(embeddings.astype('float32'))

    print(f"Created FAISS index with {index.ntotal} documents")
    return chunk_texts, index

def split_text_into_chunks(text, max_length=1000, overlap=100):
    """Split text into overlapping chunks"""
    chunks = []
    words = text.split()

    for i in range(0, len(words), max_length - overlap):
        chunk_words = words[i:i + max_length]
        chunk = ' '.join(chunk_words)
        if chunk.strip():
            chunks.append(chunk.strip())

    return chunks

def get_sample_data():
    """Fallback sample data if PDF processing fails"""
    sample_texts = [
        "The Indian Penal Code (IPC) is the main criminal code of India. It is a comprehensive code intended to cover all substantive aspects of criminal law.",
        "Section 300 of the Indian Penal Code defines murder. Except in the cases hereinafter excepted, culpable homicide is murder, if the act by which the death is caused is done with the intention of causing death, or with the intention of causing such bodily injury as the offender knows to be likely to cause the death of the person to whom the harm is caused, or with the intention of causing bodily injury to any person and the bodily injury intended to be inflicted is sufficient in the ordinary course of nature to cause death, or if the person committing the act knows that it is so imminently dangerous that it must, in all probability, cause death or such bodily injury as is likely to cause death, and commits such act without any excuse for incurring the risk of causing death or such injury as aforesaid.",
        "Section 302 of the Indian Penal Code prescribes punishment for murder. Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.",
        "Section 420 of the Indian Penal Code deals with cheating and dishonestly inducing delivery of property. It is punishable with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine.",
        "The Indian Penal Code was drafted in 1860 on the recommendations of first law commission of India established in 1834 under the Charter Act of 1833 under the Chairmanship of Lord Thomas Babington Macaulay.",
        "The IPC contains 511 sections divided into 23 chapters. It covers various offenses including crimes against the state, public tranquility, human body, property, marriage, defamation, and other matters. The 23 chapters are: Chapter I (Introduction), Chapter II (General Explanations), Chapter III (Punishments), Chapter IV (General Exceptions), Chapter V (Abetment), Chapter VI (Offences against the State), Chapter VII (Offences relating to the Army, Navy and Air Force), Chapter VIII (Offences against Public Tranquillity), Chapter IX (Offences by or relating to Public Servants), Chapter IXA (Offences relating to Elections), Chapter X (Contempts of the Lawful Authority of Public Servants), Chapter XI (False Evidence and Offences against Public Justice), Chapter XII (Offences relating to Coin and Government Stamps), Chapter XIII (Offences relating to Weights and Measures), Chapter XIV (Offences affecting the Public Health, Safety, Convenience, Decency and Morals), Chapter XV (Offences relating to Religion), Chapter XVI (Offences affecting the Human Body), Chapter XVII (Offences against Property), Chapter XVIII (Offences relating to Documents and Property Marks), Chapter XIX (Criminal Breach of Trust and Dishonest Misappropriation of Property), Chapter XX (Cheating), Chapter XXI (Fraudulent Deeds and Dispositions of Property), Chapter XXII (Criminal Intimidation, Insult and Annoyance), and Chapter XXIII (Attempts to commit Offences).",
        "Chapter XVI of the Indian Penal Code deals with offenses affecting the human body, including hurt, grievous hurt, wrongful restraint, wrongful confinement, criminal force and assault.",
        "Culpable homicide is defined in Section 299 of the Indian Penal Code. Whoever causes death by doing an act with the intention of causing death, or with the intention of causing such bodily injury as is likely to cause death, or with the knowledge that he is likely by such act to cause death, commits the offence of culpable homicide.",
        "The difference between murder and culpable homicide lies in the degree of intention and knowledge. Murder requires specific intention to cause death or knowledge that the act is imminently dangerous, while culpable homicide requires only intention to cause bodily injury likely to cause death or knowledge that the act is likely to cause death."
    ]

    # Create simple embeddings for sample data
    embeddings = embeddings_model.encode(sample_texts)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    faiss.normalize_L2(embeddings)
    index.add(embeddings.astype('float32'))

    return sample_texts, index

def get_retriever():
    """Initialize and return the document retrieval system"""
    initialize_document_system()
    return True

def get_excerpt(query, top_k=5):
    """Retrieve relevant document excerpts for a query"""
    global embeddings_model, chunk_texts, embeddings_index

    # Initialize if not already done
    if embeddings_model is None or chunk_texts is None or embeddings_index is None:
        initialize_document_system()

    try:
        # Check if query is asking for IPC structure/overview
        query_lower = query.lower()
        structure_keywords = [
            'different sections', 'sections in ipc', 'structure of ipc', 'chapters in ipc',
            'different chapters', 'overview of ipc', 'how many sections', 'how many chapters',
            'what are the chapters', 'what are the sections', 'list of chapters', 'list of sections',
            'chapters within', 'sections within', 'titles and corresponding', 'organization of',
            'structure and organization', 'categories of offenses', 'different categories',
            'organized into', 'divided into', 'framework', 'classification'
        ]

        is_structure_query = any(keyword in query_lower for keyword in structure_keywords)

        if is_structure_query:
            print(f"Detected structure query: {query}")
            # For structure queries, include sample data that has comprehensive overview
            sample_texts, _ = get_sample_data()

            # Search in both PDF data and sample data, then combine
            pdf_results = []

            # Get PDF results
            query_embedding = embeddings_model.encode([query])
            faiss.normalize_L2(query_embedding)
            scores, indices = embeddings_index.search(query_embedding.astype('float32'), top_k)

            for i, idx in enumerate(indices[0]):
                if idx < len(chunk_texts):
                    pdf_results.append(chunk_texts[idx])

            # Add the comprehensive structure information from sample data
            structure_info = sample_texts[5]  # "The IPC contains 511 sections divided into 23 chapters..."

            # Combine results, prioritizing structure info
            relevant_chunks = [structure_info] + pdf_results[:top_k-1]

            print(f"Retrieved {len(relevant_chunks)} relevant chunks for structure query: {query}")
            return relevant_chunks

        else:
            # Regular search for non-structure queries
            # Encode the query
            query_embedding = embeddings_model.encode([query])
            faiss.normalize_L2(query_embedding)

            # Search for similar documents
            scores, indices = embeddings_index.search(query_embedding.astype('float32'), top_k)

            # Get the relevant chunks
            relevant_chunks = []
            for i, idx in enumerate(indices[0]):
                if idx < len(chunk_texts):
                    relevant_chunks.append(chunk_texts[idx])

            print(f"Retrieved {len(relevant_chunks)} relevant chunks for query: {query}")
            return relevant_chunks

    except Exception as e:
        print(f"Error in document retrieval: {e}")
        # Fallback to sample excerpts
        return get_sample_excerpts(query)

def get_sample_excerpts(query):
    """Return sample excerpts for demo purposes when retrieval fails"""
    sample_excerpts = [
        "The Indian Penal Code (IPC) is the main criminal code of India. It is a comprehensive code intended to cover all substantive aspects of criminal law.",
        "Section 300 of the Indian Penal Code defines murder. Except in the cases hereinafter excepted, culpable homicide is murder, if the act by which the death is caused is done with the intention of causing death.",
        "Section 302 of the Indian Penal Code prescribes punishment for murder. Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.",
        "Section 420 of the Indian Penal Code deals with cheating and dishonestly inducing delivery of property. It is punishable with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine.",
        "Chapter XVI of the Indian Penal Code deals with offenses affecting the human body, including hurt, grievous hurt, wrongful restraint, wrongful confinement, criminal force and assault."
    ]
    return sample_excerpts