from flask import Flask, render_template, request, send_file, redirect, flash
import pdfplumber
import pandas as pd
import os
import uuid

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        flash("No file part")
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash("No selected file")
        return redirect(request.url)

    if file and file.filename.endswith('.pdf'):
        file_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.pdf")
        file.save(input_path)

        try:
            with pdfplumber.open(input_path) as pdf:
                combined_data = []
                first_header = None

                for page in pdf.pages:
                    table = page.extract_table()
                    if table:
                        for i, row in enumerate(table):
                            if not any(row):
                                continue
                            if i == 0:
                                if not first_header:
                                    first_header = row
                                    combined_data.append(row)
                                elif row == first_header:
                                    continue  # skip repeated headers
                                else:
                                    combined_data.append(row)
                            else:
                                combined_data.append(row)

            # Convert number-like cells to int/float
            cleaned_data = []
            for row in combined_data:
                cleaned_row = []
                for cell in row:
                    cell = cell.strip() if isinstance(cell, str) else cell
                    try:
                        if isinstance(cell, str):
                            if '.' in cell:
                                cleaned_row.append(float(cell.replace(',', '')))
                            else:
                                cleaned_row.append(int(cell.replace(',', '')))
                        else:
                            cleaned_row.append(cell)
                    except:
                        cleaned_row.append(cell)
                cleaned_data.append(cleaned_row)

            df = pd.DataFrame(cleaned_data[1:], columns=cleaned_data[0])
            output_filename = f"converted_{file_id}.xlsx"
            output_path = os.path.join(UPLOAD_FOLDER, output_filename)
            df.to_excel(output_path, index=False)

            return send_file(output_path, as_attachment=True)

        except Exception as e:
            flash(f"Error processing file: {e}")
            return redirect(request.url)

    flash("Invalid file format. Please upload a PDF.")
    return redirect(request.url)

@app.route("/feedback", methods=["POST"])
def feedback():
    name = request.form.get("name")
    email = request.form.get("email")
    feedback_text = request.form.get("feedback")

    with open("feedback.txt", "a", encoding="utf-8") as f:
        f.write(f"Name: {name}\nEmail: {email}\nFeedback: {feedback_text}\n{'-'*40}\n")

    flash("✅ Thank you for your feedback!")
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
