# Import necessary libraries
from PIL import Image
import pytesseract
import spacy
import os
import fitz  # PyMuPDF for PDF processing
import docx  # python-docx for Word document processing
from transformers import pipeline
import re

nlp = spacy.load("en_core_web_sm")

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Define regex pattern for valid date formats
date_patterns = [
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",  # Matches DD/MM/YYYY, MM-DD-YYYY
    r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",  # Matches YYYY-MM-DD or YYYY/MM/DD
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, \d{4}\b",  # Jan 1, 2023
    r"\b\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}\b"  # 1 January 2023
]

# Function to extract key dates and names using spaCy NLP and regex
def extract_dates_and_names(text):
    doc = nlp(text)
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    extracted_dates = set()
    
    # Extract dates using spaCy
    for ent in doc.ents:
        if ent.label_ == "DATE" and len(ent.text) > 5:  # Filter out short or incorrect matches
            extracted_dates.add(ent.text)
    
    # Extract valid dates using regex
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        extracted_dates.update(matches)
    
    return list(extracted_dates), names

# Preprocess extracted text for better classification
def preprocess_text(text):
    text = text.replace("\n", " ")  # Flatten text
    text = text.lower().strip()  # Convert to lowercase and remove spaces
    return text

# Check if the document is a resume before classification
def is_resume(text):
    resume_keywords = ["education", "work experience", "skills", "references", "career highlights"]
    return any(keyword in text for keyword in resume_keywords)

# Check if the document is a certificate
def is_certificate(text):
    certificate_keywords = ["this is to certify", "certificate of completion", "has successfully completed", "awarded", "achievement"]
    if any(keyword in text for keyword in certificate_keywords):
        if "certifications" in text and "certificate of completion" not in text:
            return False  
        return True  
    return False

# Function to categorize document using AI and keyword matching
def categorize_document(text):
    text = preprocess_text(text)
    
    if is_resume(text):
        return "resume"
    
    if is_certificate(text):
        return "certificate"
    
    categories = ["invoice", "business report", "personal letter", "legal document", "job application", "certificate"]
    result = classifier(text, candidate_labels=categories)
    return result["labels"][0]

# Function to extract text from an image using Tesseract OCR
def extract_text_from_image(image_path):
    try:
        if not os.path.exists(image_path):
            return f"Error: File not found - {image_path}"
        
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        return f"Error processing image: {str(e)}"

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
        return text.strip() if text else "Error: No text found in PDF"
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

# Function to extract text from a Word file (.docx)
def extract_text_from_docx(docx_path):
    try:
        doc = docx.Document(docx_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip() if text else "Error: No text found in DOCX"
    except Exception as e:
        return f"Error processing DOCX: {str(e)}"

# Function to process documents based on file type
def process_documents():
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif")):
            text = extract_text_from_image(file_path)
        elif filename.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file_path)
        elif filename.lower().endswith(".docx"):
            text = extract_text_from_docx(file_path)
        else:
            continue  # Skip unsupported files

        dates, names = extract_dates_and_names(text)
        category = categorize_document(text)
        
        print(f"Processing file: {filename}")
        print(f"Extracted Dates: {', '.join(dates) if dates else 'No dates found'}")
        print(f"Extracted Names: {', '.join(names) if names else 'No names found'}")
        print(f"Predicted Category: {category}")
        print("\n" + "=" * 50 + "\n")

# Run the document processing
if __name__ == '__main__':
    process_documents()
