from pypdf import PdfReader
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os


# Extract text from uploaded documents
def extract_text(filepath):

    extension = os.path.splitext(filepath)[1].lower()

    if extension == ".txt":

        with open(filepath, "r", encoding="utf-8", errors="replace") as file:
            return file.read()

    elif extension == ".pdf":

        reader = PdfReader(filepath)
        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""

        return text

    elif extension == ".docx":

        document = Document(filepath)
        text = ""

        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"

        return text

    return ""


# Compare uploaded document with reference documents
def detect_plagiarism(uploaded_text, documents_folder="documents"):

    results = []

    for filename in os.listdir(documents_folder):

        filepath = os.path.join(documents_folder, filename)

        if not filename.lower().endswith((".txt", ".pdf", ".docx")):
            continue

        reference_text = extract_text(filepath)

        if not uploaded_text.strip() or not reference_text.strip():
            continue

        vectorizer = TfidfVectorizer()

        vectors = vectorizer.fit_transform(
            [uploaded_text, reference_text]
        )

        similarity = cosine_similarity(
            vectors[0], vectors[1]
        )[0][0] * 100

        results.append({
            "filename": filename,
            "similarity": round(similarity, 2)
        })

    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results
