from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber

app = Flask(__name__)

CORS(app)

@app.route("/")
def home():
    return "PDF Converter API Running"

@app.route("/convert", methods=["POST"])
def convert():

    try:

        if "file" not in request.files:
            return jsonify({
                "success": False,
                "error": "No file uploaded"
            })

        file = request.files["file"]

        text = ""

        with pdfplumber.open(file) as pdf:

            for page in pdf.pages:

                extracted = page.extract_text()

                if extracted:
                    text += extracted + "\n"

        return jsonify({
            "success": True,
            "text": text
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })

# IMPORTANT FOR RENDER
app = app
