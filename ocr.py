# Import necessary libraries
from PIL import Image
import pytesseract
import spacy
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Ensure the uploads directory exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# Sample training data for document categorization
documents = [
    "This is an invoice for services rendered.",
    "Please find attached the contract for your review.",
    "Invoice number 12345 dated 2023-10-01.",
    "The agreement is valid until 2025-12-31."
]
labels = ["invoice", "contract", "invoice", "contract"]

# Train a simple text classification model
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(documents)
classifier = MultinomialNB()
classifier.fit(X, labels)

# Function to extract text from an image using Tesseract OCR
def extract_text(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        return text
    except Exception as e:
        return str(e)

# Function to extract key information using spaCy NLP
def extract_info(text):
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities

# Function to categorize document using the trained model
def categorize_document(text):
    X_new = vectorizer.transform([text])
    category = classifier.predict(X_new)[0]
    return category

# Main function to process documents
def process_documents():
    # List all files in the uploads folder
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Extract text from the document
        text = extract_text(file_path)
        print(f"Processing file: {filename}")
        print("Extracted Text:")
        print(text)
        
        # Extract key information
        extracted_data = extract_info(text)
        print("\nExtracted Data:")
        for entity, label in extracted_data:
            print(f"{label}: {entity}")
        
        # Categorize the document
        category = categorize_document(text)
        print(f"\nCategory: {category}")
        
        print("\n" + "=" * 50 + "\n")

# Run the document processing
if __name__ == '__main__':
    process_documents()