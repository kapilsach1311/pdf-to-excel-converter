
from flask import Flask, render_template, request, send_file, redirect, flash
import pdfplumber
import pandas as pd
import os
import re

app = Flask(__name__)
app.secret_key = "secret123"

VISITOR_FILE = "visitor_count.txt"
FEEDBACK_FILE = "feedback.txt"

def increment_visitor_count():
    if not os.path.exists(VISITOR_FILE):
        with open(VISITOR_FILE, "w") as f:
            f.write("0")
    with open(VISITOR_FILE, "r+") as f:
        count = int(f.read().strip()) + 1
        f.seek(0)
        f.write(str(count))
    return count

@app.route("/", methods=["GET"])
def index():
    count = increment_visitor_count()
    return render_template("index.html", visitor_count=count)

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        flash("No file part")
        return redirect("/")

    file = request.files["file"]
    if file.filename == "":
        flash("No selected file")
        return redirect("/")

    if file and file.filename.endswith(".pdf"):
        try:
            output_filename = "converted.xlsx"
            temp_pdf_path = "uploaded_temp.pdf"
            file.save(temp_pdf_path)

            with pdfplumber.open(temp_pdf_path) as pdf_check:
                first_page_text = pdf_check.pages[0].extract_text() or ""

            if "TD ALL-INCLUSIVE BANKING PLAN" in first_page_text:
                transactions = []
                with pdfplumber.open(temp_pdf_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if not text:
                            continue
                        lines = text.split('\n')
                        for line in lines:
                            parts = line.strip().split()
                            if len(parts) >= 4:
                                try:
                                    date_part = parts[-2]
                                    amount_part = parts[-1].replace(",", "").replace("$", "")
                                    float(amount_part)
                                    description = " ".join(parts[:-2])
                                    transactions.append({
                                        "Description": description,
                                        "Date": date_part,
                                        "Amount": float(amount_part)
                                    })
                                except ValueError:
                                    continue
                if not transactions:
                    flash("No valid transactions found in TD bank statement.")
                    return redirect("/")
                final_df = pd.DataFrame(transactions)
                final_df.to_excel(output_filename, index=False)
                return send_file(output_filename, as_attachment=True)

            else:
                repeated_headers = set()
                dfs = []

                with pdfplumber.open(temp_pdf_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        table = page.extract_table()
                        if not table:
                            continue
                        df = pd.DataFrame(table[1:], columns=table[0])

                        header_signature = "|".join(df.columns)
                        if header_signature in repeated_headers:
                            continue
                        repeated_headers.add(header_signature)

                        df = df[~df.apply(lambda row: all(cell in df.columns for cell in row), axis=1)]

                        for col in df.columns:
                            df[col] = df[col].apply(lambda x: re.sub(r"[^\d\.\-]", "", str(x)))
                            df[col] = pd.to_numeric(df[col], errors="ignore")

                        dfs.append(df)

                if not dfs:
                    flash("No tables found in PDF")
                    return redirect("/")

                final_df = pd.concat(dfs, ignore_index=True)
                final_df.to_excel(output_filename, index=False)
                return send_file(output_filename, as_attachment=True)

        except Exception as e:
            flash(f"Error processing file: {str(e)}")
            return redirect("/")
    else:
        flash("Invalid file type. Please upload a PDF.")
        return redirect("/")

@app.route("/feedback", methods=["POST"])
def feedback():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("feedback")
    with open(FEEDBACK_FILE, "a") as f:
        f.write(f"{name} | {email} | {message}\n")
    flash("✅ Thank you for your feedback!")
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
