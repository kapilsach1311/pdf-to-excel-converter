from flask import Flask, render_template, request, send_file
import os
import pandas as pd
import pdfplumber
import datetime

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    if not file.filename.endswith(".pdf"):
        return "Only PDF files are allowed."

    filepath = os.path.join("uploads", file.filename)
    file.save(filepath)

    output_file = os.path.join("downloads", file.filename.replace(".pdf", ".xlsx"))
    all_rows = []

    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row and any(cell.strip() for cell in row if cell):
                        all_rows.append(row)

    if not all_rows:
        return "No tables found in PDF."

    df = pd.DataFrame(all_rows)
    df.to_excel(output_file, index=False, header=False)

    return send_file(output_file, as_attachment=True)

@app.route("/feedback", methods=["POST"])
def save_feedback():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("feedback")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("feedback_log.csv", "a", encoding="utf-8") as f:
        f.write(f"{timestamp}, {name}, {email}, {message}\n")

    return render_template("index.html", feedback_thankyou=True)

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("downloads", exist_ok=True)
    app.run(debug=True)