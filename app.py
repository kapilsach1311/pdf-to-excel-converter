from flask import Flask, render_template, request, send_file, redirect, flash
import os
import pdfplumber
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For flashing messages

UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        flash("No file uploaded.")
        return redirect("/")

    file = request.files['file']
    if file.filename == '':
        flash("No selected file.")
        return redirect("/")

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        with pdfplumber.open(filepath) as pdf:
            all_tables = []
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    df = pd.DataFrame(table)
                    df.replace('', None, inplace=True)
                    df.dropna(how='all', axis=0, inplace=True)
                    df.dropna(how='all', axis=1, inplace=True)

                    if df.shape[0] > 1:
                        df.columns = df.iloc[0]
                        df = df[1:]

                    all_tables.append(df)

        final_df = pd.concat(all_tables, ignore_index=True)
        output_filename = f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        output_path = os.path.join(DOWNLOAD_FOLDER, output_filename)
        final_df.to_excel(output_path, index=False)

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        print("Error processing file:", e)
        flash("Something went wrong. Please try another file.")
        return redirect("/")

@app.route("/feedback", methods=["POST"])
def feedback():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("feedback")
    
    with open("feedback_log.csv", "a", encoding='utf-8') as f:
        f.write(f"{datetime.now()},{name},{email},{message}\n")

    flash("✅ Thank you for your feedback!")
    return redirect("/")

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("downloads", exist_ok=True)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
