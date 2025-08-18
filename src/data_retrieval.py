import pandas as pd
import re

def get_retriever():
    # AWS Kendra has been removed - using local sample data instead
    print("Using local sample data for document retrieval")
    return None

def get_excerpt(query):
    # Always use sample excerpts since AWS Kendra has been removed
    return get_sample_excerpts(query)

def get_sample_excerpts(query):
    """Return sample excerpts for demo purposes when Kendra is not available"""
    sample_excerpts = [
        "The Indian Penal Code (IPC) is the main criminal code of India. It is a comprehensive code intended to cover all substantive aspects of criminal law.",
        "Section 420 of the Indian Penal Code deals with cheating and dishonestly inducing delivery of property. It is punishable with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine.",
        "The Indian Penal Code was drafted in 1860 on the recommendations of first law commission of India established in 1834 under the Charter Act of 1833 under the Chairmanship of Lord Thomas Babington Macaulay.",
        "The IPC contains 511 sections divided into 23 chapters. It covers various offenses including crimes against the state, public tranquility, human body, property, marriage, defamation, and other matters.",
        "Chapter XVI of the Indian Penal Code deals with offenses affecting the human body, including hurt, grievous hurt, wrongful restraint, wrongful confinement, criminal force and assault."
    ]

    # Return all sample excerpts for any query (in a real scenario, you'd implement proper search)
    return sample_excerpts


# excerpts = get_excerpt("what is indian panel code?")
# print(excerpts)

# # Create a pandas DataFrame with the excerpts
# df = pd.DataFrame(excerpts, columns=["Excerpt"])
# # Save the DataFrame to an Excel file
# df.to_excel("../excerpts.xlsx", index=True)
# print("Excerpts saved to ../excerpts.xlsx")