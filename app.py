from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

import pdfplumber
import pytesseract
import pandas as pd
import os
import uuid
import io

from pdf2image import convert_from_bytes
from docx import Document
from reportlab.pdfgen import canvas

app = Flask(__name__)

# =========================================================
# CORS
# =========================================================

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True
)

# =========================================================
# OUTPUT FOLDER
# =========================================================

OUTPUT_FOLDER = "outputs"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status": "running"
    })

# =========================================================
# CONVERT ROUTE
# =========================================================

@app.route("/convert", methods=["POST", "OPTIONS"])
def convert():

    # HANDLE PREFLIGHT REQUEST
    if request.method == "OPTIONS":

        response = jsonify({
            "success": True
        })

        response.headers.add(
            "Access-Control-Allow-Origin",
            "*"
        )

        response.headers.add(
            "Access-Control-Allow-Headers",
            "*"
        )

        response.headers.add(
            "Access-Control-Allow-Methods",
            "*"
        )

        return response

    try:

        # =================================================
        # CHECK FILE
        # =================================================

        if "file" not in request.files:

            return jsonify({
                "success": False,
                "error": "No file uploaded"
            })

        file = request.files["file"]

        output_format = request.form.get(
            "format",
            "txt"
        )

        # =================================================
        # READ PDF
        # =================================================

        pdf_bytes = file.read()

        text = ""

        # =================================================
        # NORMAL TEXT EXTRACTION
        # =================================================

        try:

            pdf_stream = io.BytesIO(pdf_bytes)

            with pdfplumber.open(pdf_stream) as pdf:

                for page in pdf.pages:

                    extracted = page.extract_text()

                    if extracted:

                        text += extracted + "\n"

        except Exception as e:

            print("PDF TEXT EXTRACTION ERROR:", e)

        # =================================================
        # OCR FOR SCANNED PDFs
        # =================================================

        if not text.strip():

            try:

                images = convert_from_bytes(
                    pdf_bytes,
                    dpi=70,
                    grayscale=True,
                    fmt="jpeg",
                    single_file=True,
                    thread_count=1,
                    size=(800, None)
                )

                if len(images) > 3:

                    return jsonify({
                        "success": False,
                        "error": "OCR limit exceeded. Max 3 pages."
                    })

                for image in images:

                    # REDUCE MEMORY
                    image.thumbnail((800, 800))

                    ocr_text = pytesseract.image_to_string(
                        image,
                        config='--oem 1 --psm 6'
                    )

                    text += ocr_text + "\n"

                    # FREE MEMORY
                    image.close()

            except Exception as e:

                return jsonify({
                    "success": False,
                    "error": f"OCR failed: {str(e)}"
                })

        # =================================================
        # NO TEXT FOUND
        # =================================================

        if not text.strip():

            return jsonify({
                "success": False,
                "error": "No readable text found"
            })

        # =================================================
        # CREATE OUTPUT FILE
        # =================================================

        filename = str(uuid.uuid4())

        # TXT
        if output_format == "txt":

            output_path = (
                f"{OUTPUT_FOLDER}/{filename}.txt"
            )

            with open(
                output_path,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(text)

        # CSV
        elif output_format == "csv":

            output_path = (
                f"{OUTPUT_FOLDER}/{filename}.csv"
            )

            df = pd.DataFrame(
                text.split("\n"),
                columns=["Text"]
            )

            df.to_csv(
                output_path,
                index=False
            )

        # EXCEL
        elif output_format == "excel":

            output_path = (
                f"{OUTPUT_FOLDER}/{filename}.xlsx"
            )

            df = pd.DataFrame(
                text.split("\n"),
                columns=["Text"]
            )

            df.to_excel(
                output_path,
                index=False
            )

        # WORD
        elif output_format == "word":

            output_path = (
                f"{OUTPUT_FOLDER}/{filename}.docx"
            )

            doc = Document()

            doc.add_heading(
                "Converted PDF",
                level=1
            )

            doc.add_paragraph(text)

            doc.save(output_path)

        # PDF
        elif output_format == "pdf":

            output_path = (
                f"{OUTPUT_FOLDER}/{filename}.pdf"
            )

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

        # =================================================
        # RESPONSE
        # =================================================

        response = jsonify({
            "success": True,
            "download_url":
            f"/download/{os.path.basename(output_path)}",
            "text_preview": text[:5000]
        })

        response.headers.add(
            "Access-Control-Allow-Origin",
            "*"
        )

        return response

    except Exception as e:

        response = jsonify({
            "success": False,
            "error": str(e)
        })

        response.headers.add(
            "Access-Control-Allow-Origin",
            "*"
        )

        return response

# =========================================================
# DOWNLOAD FILE
# =========================================================

@app.route("/download/<filename>", methods=["GET"])
def download(filename):

    path = os.path.join(
        OUTPUT_FOLDER,
        filename
    )

    response = send_file(
        path,
        as_attachment=True
    )

    response.headers.add(
        "Access-Control-Allow-Origin",
        "*"
    )

    return response

# =========================================================
# IMPORTANT FOR RENDER
# =========================================================

app = app
