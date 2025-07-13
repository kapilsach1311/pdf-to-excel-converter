from flask import Flask, render_template, request, send_file, redirect, flash
import pdfplumber
import openpyxl
from io import BytesIO
import uuid
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        file = request.files["file"]
        if file and file.filename.endswith(".pdf"):
            pdf = pdfplumber.open(file)
            rows = []
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if any(row):
                            rows.append(row)
            pdf.close()

            if not rows:
                flash("No tables found in the PDF.")
                return redirect("/")

            output_filename = f"converted_{uuid.uuid4().hex[:8]}.xlsx"
            wb = openpyxl.Workbook()
            ws = wb.active
            for row in rows:
                ws.append(row)

            temp = BytesIO()
            wb.save(temp)
            temp.seek(0)

            return send_file(
                temp,
                download_name=output_filename,
                as_attachment=True,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            flash("Please upload a valid PDF file.")
            return redirect("/")

    except Exception as e:
        flash(f"Error processing file: {str(e)}")
        return redirect("/")

@app.route("/feedback", methods=["POST"])
def feedback():
    name = request.form.get("name")
    email = request.form.get("email")
    feedback_text = request.form.get("feedback")
    print(f"Feedback from {name} <{email}>: {feedback_text}")
    flash("Thank you for your feedback!")
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
