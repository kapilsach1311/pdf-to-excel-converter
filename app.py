import os
import pdfplumber
import pandas as pd
from flask import Flask, request, send_file, render_template, redirect

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    email = request.form.get('email')

    if not file or not file.filename.endswith('.pdf'):
        return "Invalid file format. Please upload a PDF."

    temp_filename = f"/tmp/{file.filename}"
    file.save(temp_filename)

    output_filename = None

    try:
        with pdfplumber.open(temp_filename) as pdf:
            page_count = len(pdf.pages)
            if page_count > 10:
                return render_template("pay_prompt.html", page_count=page_count)

            header_counts = {}
            cleaned_rows = []

            # First pass to find most common header
            for page in pdf.pages:
                table = page.extract_table()
                if table and len(table) > 1:
                    header = tuple(table[0])
                    header_counts[header] = header_counts.get(header, 0) + 1

            most_common_header = max(header_counts, key=header_counts.get) if header_counts else None

            # Second pass to collect only rows matching header
            for page in pdf.pages:
                table = page.extract_table()
                if table and len(table) > 1:
                    for row in table[1:]:
                        if most_common_header and len(row) == len(most_common_header):
                            cleaned_rows.append(row)

            if not cleaned_rows:
                return "No clean table data found in the PDF."

            df = pd.DataFrame(cleaned_rows)

            # Format numeric columns safely
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(
                        df[col].astype(str).str.replace(',', '').str.replace('₹', '').str.strip(),
                        errors='ignore'
                    )
                except:
                    pass

            output_filename = f"/tmp/converted_{file.filename.replace('.pdf', '')}.xlsx"
            df.to_excel(output_filename, index=False, header=[str(h) for h in most_common_header] if most_common_header else True)

    except Exception as e:
        return f"Error processing file: {e}"

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    if output_filename and os.path.exists(output_filename):
        return send_file(output_filename, as_attachment=True)
    else:
        return "Conversion failed. Please try another file or contact support."

@app.route('/pay')
def pay_redirect():
    return redirect("https://buy.stripe.com/eVq4gz6zkdHKg179Tq5wI00")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
