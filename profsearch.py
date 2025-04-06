import streamlit as st
import pandas as pd
import json
import openai
from dotenv import load_dotenv
from langchain.docstore.document import Document
# Updated imports (if you have langchain-community installed)
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
import os

# Fetch the OpenAI API key from environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")


# Check if the OpenAI API key is set
if openai_api_key:
    print("OpenAI API key is set")
else:
    print("OpenAI API key is not set")

# --- Resource Loading Function ---
# Cache the resource loading to avoid reloading on every run.
@st.cache_resource
def load_resources():
    # Load the CSV file with professor metadata.
    csv_file = 'Data.csv'
    df = pd.read_csv(csv_file)
    # Create a full name column.
    df['name'] = df['First Name:'] + ' ' + df['Last Name:']
    # Create a CV key column.
    df['cv_key'] = df['name'] + " CV.pdf"
    # Build metadata DataFrame.
    metadata_columns = ['name', 'WashU Email Address:', 'School:', 'Department:', 'Title:']
    professors_metadata = df[metadata_columns].copy()

    # Load the JSON file containing CV texts.
    json_file = 'CV.json'
    with open(json_file, 'r', encoding='utf-8') as f:
        cv_data = json.load(f)
    # Map each professor's cv_key to its corresponding CV text.
    cv_series = df['cv_key'].map(cv_data).fillna("")
    professors_metadata['cv'] = cv_series

    # Filter for professors with non-empty CV text.
    df_nonempty = professors_metadata[professors_metadata['cv'] != ""].reset_index(drop=True)

    # Create a Document for each professor's CV (with metadata).
    documents = []
    for idx, row in df_nonempty.iterrows():
        metadata = {
            "name": row['name'],
            "WashU Email Address:": row['WashU Email Address:'],
            "School:": row['School:'],
            "Department:": row['Department:'],
            "Title:": row['Title:']
        }
        doc = Document(page_content=row['cv'], metadata=metadata)
        documents.append(doc)

    # Ensure the persist directory exists.
    persist_dir = "./chroma_db"
    if not os.path.exists(persist_dir):
        os.makedirs(persist_dir)


        # Build the vector store using Chroma with persistence.
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        vectorstore = Chroma.from_documents(documents, embeddings, persist_directory=persist_dir)


        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}  # change the default 'k' as needed
        )
    else:
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}  # change the default 'k' as needed
        )

    # Set up the LLM.
    llm = ChatOpenAI(model_name="o1-mini", openai_api_key=openai_api_key)

    return retriever, llm

# Load resources once.
retriever, llm = load_resources()


# --- Similarity Search Function ---
def search_research(query, top_k=3):
    results = retriever.invoke(query)
    output_lines = []
    output_lines.append(f"Research Query: {query}\n")
    output_lines.append("Matching Professors:\n")
    for i, doc in enumerate(results, start=1):
        metadata = doc.metadata
        output_lines.append(f"Result {i}:")
        output_lines.append("Name: " + metadata.get("name", "N/A"))
        output_lines.append("WashU Email Address: " + metadata.get("WashU Email Address:", "N/A"))
        output_lines.append("School: " + metadata.get("School:", "N/A"))
        output_lines.append("Department: " + metadata.get("Department:", "N/A"))
        output_lines.append("Title: " + metadata.get("Title:", "N/A"))
        output_lines.append("-" * 40)

        # Extract the professor's CV (adjust length as needed)
        snippet = doc.page_content[:8290]

        # Create the prompt for the LLM.
        prompt = (
            f"Research Query: '{query}'.\n"
            f"Professor: {metadata.get('name', 'N/A')}.\n"
            f"CV Snippet: {snippet}\n\n"
            "Based on the research query and the attached CV above, please provide a short summary "
            "explaining why this professor was selected, highlighting how the CV content matches "
            "the research interests. Focus on the positives and the matching components."
        )
        # Generate the summary using the LLM.
        result = llm.invoke(prompt)
        summary = result.content if hasattr(result, "content") else result
        output_lines.append("Summary:")
        output_lines.append(summary)
        output_lines.append("=" * 40 + "\n")
    return "\n".join(output_lines)


st.markdown(
    """
    <style>
    .custom-heading {
        color: #89CFF0;
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
    }
    .custom-paragraph {
        color: #89CFF0;
        font-size: 1.2rem;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "<h1 class='custom-heading'>Research Collider</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p class='custom-paragraph'>Find Professors with Matching Research Interests in the Association of Chinese Professors at WashU</p>",
    unsafe_allow_html=True
)



# Text box for the search query.
query = st.text_area("Specify the expertise you are looking for:", "light-based methods to observe and measure blood flow in the living brain")

# When the button is clicked, perform the search.
if st.button("Search"):
    if query:
        with st.spinner("Searching..."):
            results_text = search_research(query, top_k=3)
        # Display results in a text area.
        st.text_area("Results", results_text, height=600)
    else:
        st.error("Please enter a search query.")
