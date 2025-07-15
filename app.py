from flask import Flask, render_template, request, send_file, redirect
import pdfplumber
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

STRIPE_PAYMENT_LINK = "https://buy.stripe.com/eVq4gz6zkdHKg179Tq5wI00"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if not file:
        return "No file uploaded", 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        with pdfplumber.open(filepath) as pdf:
            total_pages = len(pdf.pages)

        if total_pages > 10:
            return redirect(STRIPE_PAYMENT_LINK)

        dataframes = []
        for page in pdfplumber.open(filepath).pages:
            table = page.extract_table()
            if table:
                # Remove repeated headers
                if dataframes and table[0] == dataframes[-1].columns.tolist():
                    table = table[1:]
                df = pd.DataFrame(table[1:], columns=table[0])
                dataframes.append(df)

        if not dataframes:
            return "No tables found in PDF.", 400

        final_df = pd.concat(dataframes, ignore_index=True)

        # Try to convert numeric columns
        for col in final_df.columns:
            final_df[col] = pd.to_numeric(final_df[col].str.replace(',', ''), errors='ignore')

        output_path = os.path.join(UPLOAD_FOLDER, "converted.xlsx")
        final_df.to_excel(output_path, index=False)

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return f"Error processing file: {e}"

if __name__ == '__main__':
    app.run(debug=True, port=10000)
