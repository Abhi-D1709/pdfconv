import streamlit as st
import fitz  # PyMuPDF
import pdfplumber
import re
import os
import pandas as pd
from io import BytesIO
import time

# Function to clean text
def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

# Function to convert a table into Markdown format
def convert_table_to_markdown(table, page_num):
    if not table:
        return ""
    
    max_cols = max(len(row) for row in table if row)
    md_table = []
    
    # Add table title indicating the page number
    md_table.append(f"**Table from Page {page_num + 1}**\n")
    
    header = table[0] if table[0] else [''] * max_cols
    header = [clean_text(str(cell)) if cell is not None else '' for cell in header]
    
    md_table.append("| " + " | ".join(header) + " |")
    md_table.append("|" + "|".join(["---"] * max_cols) + "|")
    
    for row in table[1:]:
        if row:
            row = [clean_text(str(cell)) if cell is not None else '' for cell in row]
            md_table.append("| " + " | ".join(row) + " |")
    
    return "\n".join(md_table)

# Function to extract text and tables from a specific page
def extract_text_and_tables_from_page(doc, pdfplumber_pdf, page_num):
    start_time = time.time()  # Start timing the page processing

    # Extract text using PyMuPDF
    text_content = []
    page = doc.load_page(page_num)
    text = page.get_text("text")
    
    # Add page header
    text_content.append(f"# Page {page_num + 1}\n")
    text_content.append(text + "\n\n")
    
    # Extract tables using pdfplumber
    table_content = []
    try:
        page = pdfplumber_pdf.pages[page_num]
        tables = page.extract_tables()
        if tables:
            for table in tables:
                table_content.append(convert_table_to_markdown(table, page_num) + "\n\n")
    except Exception as e:
        # Log the error and continue
        print(f"Error processing tables on Page {page_num + 1}: {e}")
    
    # Combine text and tables content
    combined_content = ''.join(text_content) + ''.join(table_content)

    end_time = time.time()  # End timing the page processing
    processing_time = end_time - start_time
    print(f"Page {page_num + 1} processed in {processing_time:.2f} seconds.")

    return combined_content

# Function to process the PDF in batches of pages
def process_pdf_in_batches(pdf_content, output_dir, start_page, batch_size=200):
    doc = fitz.open(stream=BytesIO(pdf_content), filetype="pdf")
    pdfplumber_pdf = pdfplumber.open(BytesIO(pdf_content))
    num_pages = doc.page_count

    end_page = min(start_page + batch_size, num_pages)
    batch_content = []
    for page_num in range(start_page, end_page):
        batch_content.append(extract_text_and_tables_from_page(doc, pdfplumber_pdf, page_num))
    
    batch_file_path = os.path.join(output_dir, f"output_document_{start_page+1}_to_{end_page}.txt")
    with open(batch_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(''.join(batch_content))
    
    pdfplumber_pdf.close()
    return batch_file_path, end_page

# Streamlit application
st.title("Tool to check public offer documents")
st.write("Upload a PDF file and process it in batches of 200 pages.")

# Sidebar to display Google Sheet data and ChatGPT link
st.sidebar.title("Additional Information")
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTsmppOcJQJYxrNvpjwc1kWfn86MDyjyDtPTiGpDsjxQ0XNtPagImIDgeWo6Lv3Tg/pub?output=csv"
data = pd.read_csv(sheet_url)
st.sidebar.dataframe(data)
st.sidebar.markdown("[ChatGPT Link](https://chatgpt.com/g/g-v9JP0eW6o-mb-disclosure-checker)", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if 'start_page' not in st.session_state:
    st.session_state.start_page = 1  # Start at the first page

if uploaded_file is not None:
    if 'pdf_content' not in st.session_state:
        st.session_state.pdf_content = uploaded_file.read()

    # Extract and save the cover page separately
    if st.session_state.start_page == 1:
        with st.spinner("Extracting cover page..."):
            output_dir = "data"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            cover_page_path = os.path.join(output_dir, "cover_page.txt")
            doc = fitz.open(stream=BytesIO(st.session_state.pdf_content), filetype="pdf")
            cover_page_content = extract_text_and_tables_from_page(doc, pdfplumber.open(BytesIO(st.session_state.pdf_content)), 0)
            with open(cover_page_path, 'w', encoding='utf-8') as output_file:
                output_file.write(cover_page_content)
            st.write("Cover page extracted.")
            with open(cover_page_path, 'rb') as f:
                st.download_button(
                    label="Download Cover Page",
                    data=f,
                    file_name="cover_page.txt",
                    mime="text/plain"
                )
            st.session_state.start_page = 2  # Move to the next page after the cover page

    # Process remaining pages in batches
    process_button = st.button(f"Process Pages {st.session_state.start_page} to {st.session_state.start_page + 199}")
    if process_button:
        with st.spinner("Processing..."):
            output_dir = "data"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            batch_file_path, next_start_page = process_pdf_in_batches(st.session_state.pdf_content, output_dir, st.session_state.start_page - 1)
            with open(batch_file_path, 'rb') as f:
                st.download_button(
                    label="Download text file",
                    data=f,
                    file_name=os.path.basename(batch_file_path),
                    mime="text/plain"
                )
            st.session_state.start_page = next_start_page + 1  # Update the start page for the next batch
            doc = fitz.open(stream=BytesIO(st.session_state.pdf_content), filetype="pdf")
            if st.session_state.start_page > doc.page_count:
                st.write("Processing complete. All pages have been processed.")
