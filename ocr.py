# Import necessary libraries
from PIL import Image
import pytesseract
import spacy
import os
import fitz  # PyMuPDF for PDF processing
import docx  # python-docx for Word document processing
from transformers import pipeline

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Ensure the uploads directory exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Set Tesseract OCR path (update this based on your system)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load the pretrained document classification model from Hugging Face
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Function to extract text from an image using Tesseract OCR
def extract_text_from_image(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        return text.strip()
    except Exception as e:
        return str(e)

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
        return text.strip()
    except Exception as e:
        return str(e)

# Function to extract text from a Word file
def extract_text_from_docx(docx_path):
    try:
        doc = docx.Document(docx_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip()
    except Exception as e:
        return str(e)

# Function to extract key dates using spaCy NLP
def extract_dates(text):
    doc = nlp(text)
    return [ent.text for ent in doc.ents if ent.label_ == "DATE"]

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
    certificate_keywords = ["this is to certify", "has successfully completed", "certificate of completion", "awarded", "achievement"]
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

        dates = extract_dates(text)
        category = categorize_document(text)
        
        print(f"Processing file: {filename}")
        print(f"Extracted Dates: {', '.join(dates) if dates else 'No dates found'}")
        print(f"Predicted Category: {category}")
        print("\n" + "=" * 50 + "\n")

# Run the document processing
if __name__ == '__main__':
    process_documents()
