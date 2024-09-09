import streamlit as st
import pdfplumber
import re
import tempfile
import pandas as pd
import os

# Function to clean text by replacing multiple spaces with a single space
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    return text.strip()

# Function to convert a table to Markdown format
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

# Function to extract content from a PDF and convert it to Markdown and text formats
def extract_content_from_pdf(pdf_path, md_path, text_path):
    md_content = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                md_content.append(f"# Page {page_num + 1}\n")
                
                text = page.extract_text()
                if text:
                    md_content.append(clean_text(text))
                    md_content.append("\n")
                
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        md_content.append(convert_table_to_markdown(table))
                        md_content.append("\n")
        
        # Write the content to a Markdown file with UTF-8 encoding
        with open(md_path, 'w', encoding='utf-8') as md_file:
            md_file.write("\n".join(md_content))

        # Read the Markdown content and write it to a text file
        with open(md_path, 'r', encoding='utf-8') as md_file:
            markdown_content = md_file.read()
        
        with open(text_path, 'w', encoding='utf-8') as text_file:
            text_file.write(markdown_content)
        
    except Exception as e:
        st.error(f"An error occurred while processing the PDF: {str(e)}")
    finally:
        # Cleanup: Delete the Markdown file after the text file is created
        if os.path.exists(md_path):
            os.remove(md_path)

# Function to handle PDF file upload and processing
def process_pdf(uploaded_file):
    try:
        # Create a temporary file to save the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            temp_pdf.write(uploaded_file.getbuffer())
            text_file_path = temp_pdf.name.replace('.pdf', '.txt')
            
            with st.spinner("Extracting content..."):
                extract_content_from_pdf(temp_pdf.name, text_file_path.replace('.txt', '.md'), text_file_path)

        st.success("Processing complete!")
        return text_file_path

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

# Function to fetch a Google Sheet as a DataFrame
def fetch_google_sheet(sheet_url):
    try:
        sheet_id = sheet_url.split("/")[5]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"An error occurred while fetching the Google Sheet: {str(e)}")
        return None

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
            <a href="https://chatgpt.com/g/g-v9JP0eW6o-mb-disclosure-checker" target="_blank" class="link-button">ChatGPT Disclosure Checker</a>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.write("Please upload a PDF for conversion")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        st.write("Processing the file...")
        text_file_path = process_pdf(uploaded_file)
        
        if text_file_path:
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
    df = fetch_google_sheet(sheet_url)
    
    if df is not None:
        st.dataframe(df.style.set_properties(**{'white-space': 'pre-wrap'}), height=400)

st.info("Note: All uploaded files and generated files will be removed automatically after you close this app.")
st.markdown('<div style="text-align: center; padding: 10px;">Developed by Abhignan</div>', unsafe_allow_html=True)
