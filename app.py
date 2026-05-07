from flask import Flask, request, jsonify
import pdfplumber

app = Flask(__name__)

@app.route('/')
def home():
    return "PDF Converter API Running"

@app.route('/convert', methods=['POST'])
def convert():

    file = request.files['file']

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

if __name__ == '__main__':
    app.run(debug=True)