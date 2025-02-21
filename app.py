from PIL import Image
import pytesseract
import spacy
import os
import fitz  
import docx 
from transformers import pipeline
import re
import shutil  
import zipfile
from flask import Flask, request, send_file, render_template, url_for, redirect
from werkzeug.utils import secure_filename
import threading

nlp = spacy.load("en_core_web_sm")

UPLOAD_FOLDER = 'uploads'
SORTED_FOLDER = 'sorted_documents'

ZIP_FILE = 'sorted_documents.zip'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(SORTED_FOLDER):
    os.makedirs(SORTED_FOLDER)

pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Define regex pattern for valid date formats
date_patterns = [
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, \d{4}\b",
    r"\b\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}\b"
]

def extract_dates_and_names(text):
    doc = nlp(text)
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    extracted_dates = set()
    for ent in doc.ents:
        if ent.label_ == "DATE" and len(ent.text) > 5:
            extracted_dates.add(ent.text)
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        extracted_dates.update(matches)
    return list(extracted_dates), names

def extract_zip(zip_path, extract_to=UPLOAD_FOLDER):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted ZIP file: {zip_path}")
        os.remove(zip_path)
    except Exception as e:
        print(f"Error extracting ZIP file: {str(e)}")

def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        return f"Error processing image: {str(e)}"

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
        return text.strip() if text else "Error: No text found in PDF"
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

def extract_text_from_docx(docx_path):
    try:
        doc = docx.Document(docx_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip() if text else "Error: No text found in DOCX"
    except Exception as e:
        return f"Error processing DOCX: {str(e)}"


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
            continue
        dates, names = extract_dates_and_names(text)
        category = categorize_document(text)
        category_folder = os.path.join(SORTED_FOLDER, category)
        if not os.path.exists(category_folder):
            os.makedirs(category_folder)
        shutil.move(file_path, os.path.join(category_folder, filename))
        print(f"Processing file: {filename}")
        print(f"Extracted Dates: {', '.join(dates) if dates else 'No dates found'}")
        print(f"Extracted Names: {', '.join(names) if names else 'No names found'}")
        print(f"Predicted Category: {category}")
        print("\n" + "=" * 50 + "\n")
    zip_path = os.path.join(UPLOAD_FOLDER, ZIP_FILE.replace(".zip", ""))
    shutil.make_archive(zip_path, 'zip', SORTED_FOLDER)
    print(f"Zipped all sorted documents as {ZIP_FILE}")

def preprocess_text(text):
    text = text.replace("\n", " ").lower().strip()
    return text

def is_resume(text):
    resume_keywords = ["education", "work experience", "skills", "references", "career highlights"]
    return any(keyword in text for keyword in resume_keywords)

def is_certificate(text):
    certificate_keywords = ["this is to certify", "certificate of completion", "has successfully completed", "awarded", "achievement"]
    if any(keyword in text for keyword in certificate_keywords):
        if "certifications" in text and "certificate of completion" not in text:
            return False  
        return True  
    return False

def categorize_document(text):
    text = preprocess_text(text)
    if is_resume(text):
        return "resume"
    if is_certificate(text):
        return "certificate"
    categories = ["invoice", "business report", "personal letter", "legal document", "job application", "certificate"]
    result = classifier(text, candidate_labels=categories)
    return result["labels"][0]

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return "No file provided"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        if not file.filename.lower().endswith(".zip"):
            return "Only ZIP files are accepted"
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        extract_zip(file_path)
        process_documents()
        return redirect(url_for('sorting_complete'))
    except Exception as e:
        return f"An error occurred during processing: {str(e)}"
    
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('about.html')

@app.route('/tutorial')
def tutorial():
    return render_template('about.html')


@app.route('/sorting_complete')
def sorting_complete():
    with app.app_context():  
        zip_file_url = url_for('download_zip')  
        return render_template('result.html', zip_file_url=zip_file_url)

@app.route('/download')
def download_zip():
    zip_path = os.path.abspath("uploads/sorted_documents.zip")

    # Debug: Print the path to verify
    print(f"Looking for ZIP file at: {zip_path}")

    if os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True)
    else:
        return f"Error: File not found at {zip_path}", 404
if __name__ == '__main__':
    app.run(debug=False)
