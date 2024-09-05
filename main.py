import streamlit as st
from pdfminer.high_level import extract_text
from PIL import Image
import os
import zipfile
from pdf2image import convert_from_path
from io import BytesIO
import pandas as pd

# Define the directory for temporary files
TEMP_DIR = "./data"
os.makedirs(TEMP_DIR, exist_ok=True)

def save_first_page_as_image(pdf_file, dpi=300):
    try:
        # Save the uploaded file temporarily
        temp_pdf_path = os.path.join(TEMP_DIR, pdf_file.name)
        with open(temp_pdf_path, "wb") as f:
            f.write(pdf_file.getbuffer())

        # Convert the first page of the PDF to an image using pdf2image
        images = convert_from_path(temp_pdf_path, dpi=dpi, first_page=1, last_page=1)
        img_buffer = BytesIO()
        images[0].save(img_buffer, format='PNG')
        img_buffer.seek(0)
        return img_buffer
    except Exception as e:
        st.error(f"Failed to save first page as image: {e}")
        return None

def extract_text_from_pdf(pdf_file, start_page=1, pages_per_file=200):
    text_files = []
    try:
        temp_pdf_path = os.path.join(TEMP_DIR, pdf_file.name)
        with open(temp_pdf_path, "wb") as f:
            f.write(pdf_file.getbuffer())
            
        all_text = extract_text(temp_pdf_path)
        if not all_text.strip():
            raise ValueError("PDFMiner extraction failed.")

        # Add page numbers
        total_pages = all_text.count('\x0c')
        text_with_page_numbers = ''
        for i, page_text in enumerate(all_text.split('\x0c')):
            if page_text.strip():
                text_with_page_numbers += page_text + f"\nPage No {i + 1}\n"

        all_text = text_with_page_numbers

        # Splitting the text into chunks if needed
        file_count = 1
        pages_processed = 0
        text_chunks = all_text.split('\nPage No ')
        current_text = ''

        for chunk in text_chunks:
            current_text += f'\nPage No {chunk}'
            pages_processed += 1

            if pages_processed >= pages_per_file:
                text_files.append(current_text)
                current_text = ''
                pages_processed = 0
                file_count += 1

        if current_text:
            text_files.append(current_text)
    except Exception as e:
        st.error(f"Failed to extract text from PDF: {e}")

    return text_files

def create_zip(text_files, image_buffer, pdf_name):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        # Add image to the zip
        if image_buffer:
            zipf.writestr(f"{pdf_name}_first_page.png", image_buffer.getvalue())

        # Add text files to the zip
        for i, text in enumerate(text_files):
            zipf.writestr(f"{pdf_name}_part_{i+1}.txt", text)

    zip_buffer.seek(0)
    return zip_buffer

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
            <a href="https://chatgpt.com/g/g-v9JP0eW6o-mb-disclosure-checker" target="_blank" class="link-button">ChatGPT Disclosure Checker</a>
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

        # Save the first page as an image
        image_buffer = save_first_page_as_image(uploaded_file)

        # Extract text from the PDF
        text_files = extract_text_from_pdf(uploaded_file)

        # Create a zip file with the extracted content
        zip_buffer = create_zip(text_files, image_buffer, pdf_name)

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

    # Provide a download button for the Google Sheet
    st.download_button(
        label="Download Process as Excel",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="process_to_be_followed.csv",
        mime="text/csv"
    )

st.info("Note: All uploaded files and generated files will be removed automatically after you close this app.")
# Footer
st.markdown('<div style="text-align: center; padding: 10px;">Developed by Abhignan</div>', unsafe_allow_html=True)
