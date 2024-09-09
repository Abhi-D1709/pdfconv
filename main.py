import streamlit as st
import fitz  # PyMuPDF
import json
import re
import os
from io import BytesIO
import zipfile
import pandas as pd
from PIL import Image

# Define the directory for temporary files
TEMP_DIR = "./data"
os.makedirs(TEMP_DIR, exist_ok=True)

def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def clean_text(text):
    # Remove excessive spaces around newlines and replace multiple newlines with a single newline
    text = re.sub(r'\s*\n\s*', '\n', text)
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)
    # Remove any leading or trailing whitespace
    text = text.strip()
    return text

def save_cover_page_as_image(pdf_path, dpi=300):
    try:
        document = fitz.open(pdf_path)
        page = document.load_page(0)  # Load the first page

        # Render the page as an image
        pix = page.get_pixmap(dpi=dpi)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Save the image to a BytesIO object
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        print("Cover page image saved successfully.")  # Debugging
        return img_buffer
    except Exception as e:
        st.error(f"Failed to save cover page as image: {e}")
        return None

def extract_cover_page(pdf_path, output_dir):
    document = fitz.open(pdf_path)
    page = document[0]
    page_text = clean_text(page.get_text("text"))
    cover_page_data = {
        "page_number": 1,
        "content": page_text
    }
    save_json(cover_page_data, os.path.join(output_dir, "cover_page.json"))

def extract_index_page(pdf_path, output_dir):
    document = fitz.open(pdf_path)
    page = document[1]
    page_text = clean_text(page.get_text("text"))
    index_page_data = {
        "page_number": 2,
        "content": page_text
    }
    save_json(index_page_data, os.path.join(output_dir, "index.json"))

    # Automatically extract section titles and corresponding page numbers
    sections = []
    for line in page_text.splitlines():
        line = line.strip()
        match = re.match(r"(.*?)(\d+)$", line)
        if match:
            title = match.group(1).strip()
            page_number = int(match.group(2).strip())
            if re.search(r'section', title, re.IGNORECASE):  # Ensuring it's a section
                # Clean the title by removing unnecessary non-alphabetic characters except colons and spaces
                cleaned_title = re.sub(r'[^A-Za-z0-9\s:]', '', title).strip()
                sections.append({"title": cleaned_title, "page_number": page_number})

    return sections

def extract_sections_by_page_numbers(pdf_path, sections, output_dir):
    document = fitz.open(pdf_path)
    total_pages = len(document)

    for i, section in enumerate(sections):
        start_page = section['page_number'] - 1  # Zero-based indexing
        # Determine the end page; if it's the last section, go to the end of the document
        end_page = sections[i + 1]['page_number'] - 2 if i + 1 < len(sections) else total_pages - 1

        pages_content = []
        for page_number in range(start_page, end_page + 1):
            page = document[page_number]
            page_text = clean_text(page.get_text("text"))
            pages_content.append({
                "page_number": page_number + 1,
                "content": page_text
            })

        section_data = {
            "section_title": section['title'],
            "start_page": start_page + 1,
            "end_page": end_page + 1,
            "pages": pages_content
        }
        filename = f"{section['title'].replace(' ', '_').replace(':', '').replace('/', '_').lower()}.json"
        save_json(section_data, os.path.join(output_dir, filename))

def process_pdf(pdf_file, output_dir):
    # Save uploaded file temporarily
    temp_pdf_path = os.path.join(TEMP_DIR, pdf_file.name)
    with open(temp_pdf_path, "wb") as f:
        f.write(pdf_file.getbuffer())

    # Extract JSON files
    extract_cover_page(temp_pdf_path, output_dir)
    sections = extract_index_page(temp_pdf_path, output_dir)
    extract_sections_by_page_numbers(temp_pdf_path, sections, output_dir)

    # Save cover page as image and return the buffer
    cover_image_buffer = save_cover_page_as_image(temp_pdf_path)
    return cover_image_buffer

def create_zip(json_files_dir, cover_image_buffer, pdf_name):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        # Add the cover page image to the zip
        if cover_image_buffer:
            zipf.writestr("cover_page.png", cover_image_buffer.getvalue())
            print("Cover image added to zip.")  # Debugging

        # Add JSON files to the zip
        for root, _, files in os.walk(json_files_dir):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, "rb") as f:
                    # Ensure unique file names by including the directory path
                    arcname = os.path.relpath(file_path, json_files_dir)
                    zipf.writestr(arcname, f.read())
                    print(f"Added {arcname} to zip.")  # Debugging
                    
    zip_buffer.seek(0)
    return zip_buffer

import shutil

def clear_temp_directory():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

def fetch_google_sheet(sheet_url):
    sheet_id = sheet_url.split("/")[5]
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    df = pd.read_csv(url)
    return df

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
        text-overflow: ellipsis;
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
    # ChatGPT Link aligned to the left
    st.markdown(
        """
        <div class="left-aligned-button">
            <a href="https://chatgpt.com/g/g-7kHaBfiH4-debt-disclosure-assistant" target="_blank" class="link-button">ChatGPT Disclosure Checker</a>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.write("Please upload a PDF for conversion")
    
    # File uploader
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        st.write("Processing the file...")
        pdf_name = os.path.splitext(uploaded_file.name)[0]

        # Create a temporary directory to store JSON files
        json_files_dir = os.path.join(TEMP_DIR, f"{pdf_name}_json")
        os.makedirs(json_files_dir, exist_ok=True)

        # Process the PDF to extract and save JSON files and cover image
        cover_image_buffer = process_pdf(uploaded_file, json_files_dir)

        # Create a zip file with the extracted JSON files and cover image
        zip_buffer = create_zip(json_files_dir, cover_image_buffer, pdf_name)

        # Display processing completion message
        st.success("Finished processing the PDF.")
        
        # Provide a download button for the zip file
        st.download_button(
            label="Download Processed Files",
            data=zip_buffer,
            file_name=f"{pdf_name}_output.zip",
            mime="application/zip"
        )

with col2:
    st.markdown("<h5>Process to be followed</h5>", unsafe_allow_html=True)
    
    # Fetch and display the Google Sheet data
    sheet_url = "https://docs.google.com/spreadsheets/d/1UxC2abUh0BwBE1ujBUuifj-mU88cGrEW/pubhtml"
    df = fetch_google_sheet(sheet_url)
    
    # Display the dataframe with text wrapping and without the index column
    st.dataframe(df.style.set_properties(**{'white-space': 'pre-wrap'}), height=400)

st.info("Note: All uploaded files and generated files will be removed automatically after you close this app.")
# Footer
st.markdown('<div style="text-align: center; padding: 10px;">Developed by Abhignan</div>', unsafe_allow_html=True)
