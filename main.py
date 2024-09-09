import streamlit as st
import pdfplumber
import re
import os
from io import BytesIO
import shutil
import pandas as pd

# Define the directory for temporary files
TEMP_DIR = "./data"
os.makedirs(TEMP_DIR, exist_ok=True)

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    return text.strip()

def convert_table_to_markdown(table):
    if not table:
        return ""
    
    max_cols = max(len(row) for row in table if row)
    md_table = []
    header = table[0] if table[0] else [''] * max_cols
    
    header = [clean_text(str(cell)) if cell is not None else '' for cell in header]
    md_table.append("| " + " | ".join(header) + " |")
    md_table.append("|" + "|".join(["---"] * max_cols) + "|")
    
    for row in table[1:]:
        if row:
            row = [clean_text(str(cell)) if cell is not None else '' for cell in row]
            md_table.append("| " + " | ".join(row) + " |")
    
    return "\n".join(md_table)

def extract_content_from_pdf(pdf_path, text_path):
    with open(text_path, 'w', encoding='utf-8') as text_file:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Write each page's content directly to the file to reduce memory usage
                text_file.write(f"# Page {page_num + 1}\n")
                
                text = page.extract_text()
                if text:
                    text_file.write(clean_text(text))
                    text_file.write("\n")
                
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        text_file.write(convert_table_to_markdown(table))
                        text_file.write("\n")
    # No need to return the content, as it's already written to the file

def process_pdf(uploaded_file):
    pdf_name = os.path.splitext(uploaded_file.name)[0]
    text_path = os.path.join(TEMP_DIR, f"{pdf_name}.txt")

    # Save uploaded PDF to a temporary path
    temp_pdf_path = os.path.join(TEMP_DIR, uploaded_file.name)
    with open(temp_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Extract content and save directly to a text file
    extract_content_from_pdf(temp_pdf_path, text_path)
    return text_path

def clear_temp_directory():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

# Add custom CSS for styling
st.markdown(
    """
    <style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f0f2f6;
        color: #333;
    }
    .main {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .stButton > button {
        background-color: #007BFF;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #0056b3;
    }
    .stFileUploader > label {
        color: #007BFF;
        font-size: 16px;
        font-weight: bold;
    }
    .header {
        text-align: center;
        margin-bottom: 30px;
    }
    .link-button {
        display: inline-block;
        background-color: #00FFFF;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 16px;
        text-align: center;
        text-decoration: none;
        margin: 20px 0;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .left-aligned-button {
        text-align: left;
        margin-bottom: 20px;
    }
    .dataframe {
        max-width: 100%;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis.
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Main title
st.markdown("<div class='header'><h1>Tool to Analyze Offer Documents of Public Debt Issuances</h1></div>", unsafe_allow_html=True)

# Create columns for layout
col1, col2 = st.columns([1, 1.5])

with col1:
    st.markdown(
        """
        <div class="left-aligned-button">
            <a href="https://chatgpt.com/g/g-7kHaBfiH4-debt-disclosure-assistant" target="_blank" class="link-button">ChatGPT Disclosure Checker</a>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.write("Please upload a PDF for conversion")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        st.write("Processing the file...")
        text_file_path = process_pdf(uploaded_file)
        
        st.success("File is Processed!")
        
        with open(text_file_path, "rb") as file:
            st.download_button(
                label="Download Text File",
                data=file,
                file_name=os.path.basename(text_file_path),
                mime="text/plain"
            )

with col2:
    st.markdown("<h5>Process to be followed</h5>", unsafe_allow_html=True)
    
    sheet_url = "https://docs.google.com/spreadsheets/d/1UxC2abUh0BwBE1ujBUuifj-mU88cGrEW/pubhtml"
    df = pd.read_csv(sheet_url)
    
    st.dataframe(df.style.set_properties(**{'white-space': 'pre-wrap'}), height=400)

st.info("Note: All uploaded files and generated files will be removed automatically after you close this app.")
st.markdown('<div style="text-align: center; padding: 10px;">Developed by Abhignan</div>', unsafe_allow_html=True)

# Clear temporary directory after the app is closed
clear_temp_directory()
