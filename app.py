from flask import Flask, render_template, request, send_file, redirect, flash
import pdfplumber
import pandas as pd
import tempfile
import os
from collections import Counter

app = Flask(__name__)
app.secret_key = "your_secret_key"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        flash("No file part")
        return redirect("/")
    file = request.files['file']
    if file.filename == '':
        flash("No selected file")
        return redirect("/")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        file.save(temp.name)
        temp_filename = temp.name

    with pdfplumber.open(temp_filename) as pdf:
        page_count = len(pdf.pages)
        if page_count > 10:
            os.remove(temp_filename)
            return render_template("pay_prompt.html", page_count=page_count)

    try:
        all_tables = []
        header_counter = Counter()

        with pdfplumber.open(temp_filename) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 1:
                        header = tuple(table[0])
                        header_counter[header] += 1

        most_common_header = header_counter.most_common(1)[0][0] if header_counter else None

        with pdfplumber.open(temp_filename) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        if tuple(table[0]) == most_common_header:
                            data_rows = table[1:]
                        else:
                            data_rows = table
                        for row in data_rows:
                            all_tables.append(row)

        os.remove(temp_filename)

        df = pd.DataFrame(all_tables)
        df = df.dropna(how='all')

        # Convert columns to numeric if possible
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='ignore')

        output_filename = os.path.join(tempfile.gettempdir(), "converted.xlsx")
        df.to_excel(output_filename, index=False, header=[str(h) for h in most_common_header] if most_common_header else True)

        return send_file(output_filename, as_attachment=True)

    except Exception as e:
        os.remove(temp_filename)
        return f"Error processing file: {e}"

@app.route("/feedback", methods=["POST"])
def feedback():
    name = request.form.get("name")
    email = request.form.get("email")
    feedback_text = request.form.get("feedback")
    print(f"Feedback received from {name} ({email}): {feedback_text}")
    flash("✅ Thank you for your feedback!")
    return redirect("/")

@app.route("/pay")
def pay_redirect():
    return redirect("https://buy.stripe.com/eVq4gz6zkdHKg179Tq5wI00")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
