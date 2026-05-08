from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

import pdfplumber
import pytesseract
import pandas as pd
import os
import uuid

from pdf2image import convert_from_bytes
from docx import Document
from reportlab.pdfgen import canvas

app = Flask(__name__)

# Enable CORS
CORS(app)

# Create outputs folder
OUTPUT_FOLDER = "outputs"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return "PDF Converter SaaS Running"

@app.route("/convert", methods=["POST"])
def convert():

    try:

        # Check file
        if "file" not in request.files:

            return jsonify({
                "success": False,
                "error": "No file uploaded"
            })

        file = request.files["file"]

        # Output format
        output_format = request.form.get("format", "txt")

        # Read PDF bytes
        pdf_bytes = file.read()

        text = ""

        # ===================================================
        # NORMAL PDF TEXT EXTRACTION
        # ===================================================

        try:

            import io

            pdf_stream = io.BytesIO(pdf_bytes)

            with pdfplumber.open(pdf_stream) as pdf:

                for page in pdf.pages:

                    extracted = page.extract_text()

                    if extracted:

                        text += extracted + "\n"

        except Exception as e:

            print("PDFPlumber Error:", e)

        # ===================================================
        # OCR FALLBACK FOR SCANNED PDFs
        # ===================================================

        if not text.strip():

            try:

                images = convert_from_bytes(pdf_bytes)

                for image in images:

                    ocr_text = pytesseract.image_to_string(image)

                    text += ocr_text + "\n"

            except Exception as e:

                return jsonify({
                    "success": False,
                    "error": f"OCR failed: {str(e)}"
                })

        # ===================================================
        # NO TEXT FOUND
        # ===================================================

        if not text.strip():

            return jsonify({
                "success": False,
                "error": "No readable text found in PDF"
            })

        # ===================================================
        # GENERATE FILE
        # ===================================================

        filename = str(uuid.uuid4())

        # TXT
        if output_format == "txt":

            output_path = f"{OUTPUT_FOLDER}/{filename}.txt"

            with open(output_path, "w", encoding="utf-8") as f:

                f.write(text)

        # CSV
        elif output_format == "csv":

            output_path = f"{OUTPUT_FOLDER}/{filename}.csv"

            lines = text.split("\n")

            df = pd.DataFrame(lines, columns=["Text"])

            df.to_csv(output_path, index=False)

        # EXCEL
        elif output_format == "excel":

            output_path = f"{OUTPUT_FOLDER}/{filename}.xlsx"

            lines = text.split("\n")

            df = pd.DataFrame(lines, columns=["Text"])

            df.to_excel(output_path, index=False)

        # WORD
        elif output_format == "word":

            output_path = f"{OUTPUT_FOLDER}/{filename}.docx"

            doc = Document()

            doc.add_heading("Converted PDF", level=1)

            doc.add_paragraph(text)

            doc.save(output_path)

        # PDF
        elif output_format == "pdf":

            output_path = f"{OUTPUT_FOLDER}/{filename}.pdf"

            c = canvas.Canvas(output_path)

            text_object = c.beginText(40, 800)

            for line in text.split("\n"):

                text_object.textLine(line)

            c.drawText(text_object)

            c.save()

        else:

            return jsonify({
                "success": False,
                "error": "Invalid output format"
            })

        # ===================================================
        # DOWNLOAD URL
        # ===================================================

        download_url = f"/download/{os.path.basename(output_path)}"

        return jsonify({
            "success": True,
            "download_url": download_url,
            "text_preview": text[:5000]
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })

# ===================================================
# DOWNLOAD ROUTE
# ===================================================

@app.route("/download/<filename>")
def download(filename):

    file_path = os.path.join(OUTPUT_FOLDER, filename)

    return send_file(
        file_path,
        as_attachment=True
    )

# ===================================================
# IMPORTANT FOR RENDER + DOCKER
# ===================================================

app = app
