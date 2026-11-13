from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
from plagiarism import extract_text, detect_plagiarism

import os
import sqlite3
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = "uploads"
REPORT_FOLDER = "reports"
DATABASE = "plagiarism.db"

ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)


# Initialize Database
def init_db():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            highest_similarity REAL,
            matched_document TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


# Check Allowed File Format
def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# Generate PDF Report
def generate_pdf_report(filename, results):

    report_name = (
        f"report_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"
    )

    report_path = os.path.join(REPORT_FOLDER, report_name)

    pdf = canvas.Canvas(report_path, pagesize=A4)

    width, height = A4

    y = height - 60

    # Heading
    pdf.setFont("Helvetica-Bold", 18)

    pdf.drawString(
        50, y,
        "PLAGIARISM DETECTION REPORT"
    )

    y -= 50

    # Document Information
    pdf.setFont("Helvetica", 12)

    pdf.drawString(
        50, y,
        f"Uploaded Document: {filename}"
    )

    y -= 25

    pdf.drawString(
        50, y,
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    y -= 40

    # Similarity Analysis
    if results:

        pdf.setFont("Helvetica-Bold", 13)

        pdf.drawString(
            50, y,
            "Similarity Analysis"
        )

        y -= 30

        pdf.setFont("Helvetica", 11)

        for result in results:

            if y < 70:

                pdf.showPage()
                y = height - 60

                pdf.setFont("Helvetica", 11)

            pdf.drawString(
                50, y,
                f"{result['filename']} : {result['similarity']}%"
            )

            y -= 25

        # Highest Similarity
        highest = results[0]

        y -= 15

        pdf.setFont("Helvetica-Bold", 12)

        pdf.drawString(
            50, y,
            f"Highest Similarity: {highest['similarity']}%"
        )

        y -= 25

        pdf.drawString(
            50, y,
            f"Most Matched Document: {highest['filename']}"
        )

    else:

        pdf.drawString(
            50, y,
            "No reference documents available."
        )

    # Disclaimer
    y -= 60

    if y < 70:
        pdf.showPage()
        y = height - 60

    pdf.setFont("Helvetica-Oblique", 9)

    pdf.drawString(
        50, y,
        "Note: Similarity score is not a final plagiarism verdict."
    )

    pdf.save()

    return report_name


# Home Page
@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        if "file" not in request.files:

            return "No file selected"

        file = request.files["file"]

        if file.filename == "":

            return "Please select a file"

        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)

            if not filename:

                return "Invalid filename", 400

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            file.save(filepath)

            # Extract Text
            extracted_text = extract_text(filepath)

            if not extracted_text.strip():

                return "The uploaded document contains no readable text."

            # Detect Plagiarism
            results = detect_plagiarism(extracted_text)

            # Generate PDF Report
            report_name = generate_pdf_report(
                filename,
                results
            )

            # Save Analysis in Database
            if results:

                highest_result = results[0]

                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO analysis_history
                    (
                        filename,
                        upload_date,
                        highest_similarity,
                        matched_document
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    filename,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    highest_result["similarity"],
                    highest_result["filename"]
                ))

                conn.commit()
                conn.close()

            # Display Result
            return render_template(
                "result.html",
                filename=filename,
                extracted_text=extracted_text,
                results=results,
                report_name=report_name
            )

        return "Invalid file format"

    return render_template("index.html")


# Analysis History Page
@app.route("/history")
def history():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM analysis_history
        ORDER BY id DESC
    """)

    records = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        records=records
    )


# Download PDF Report
@app.route("/download-report/<report_name>")
def download_report(report_name):

    return send_from_directory(
        REPORT_FOLDER,
        report_name,
        as_attachment=True
    )


# Run Flask Application
if __name__ == "__main__":

    app.run(debug=False)