from flask import Flask, render_template, request, send_file, redirect
import pdfplumber
import pandas as pd
import os
import uuid

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return 'No file selected'

    temp_filename = f"{uuid.uuid4().hex}.pdf"
    uploaded_file.save(temp_filename)

    all_data = []
    try:
        with pdfplumber.open(temp_filename) as pdf:
    page_count = len(pdf.pages)
    if page_count > 10:
        os.remove(temp_filename)
        return render_template("pay_prompt.html", page_count=page_count)

     

            for page in pdf.pages:
                try:
                    table = page.extract_table()
                    if table:
                        # Ensure unique column names
                        columns = table[0]
                        unique_columns = []
                        seen = {}
                        for col in columns:
                            if col in seen:
                                seen[col] += 1
                                unique_columns.append(f"{col}_{seen[col]}")
                            else:
                                seen[col] = 0
                                unique_columns.append(col)

                        df = pd.DataFrame(table[1:], columns=unique_columns)

                        # Convert number-like columns to numeric
                        for col in df.columns:
                            df[col] = pd.to_numeric(df[col].str.replace(',', '').str.replace('₹', '').str.strip(), errors='ignore')

                        all_data.append(df)
                except Exception as e:
                    print(f"Error processing page: {e}")

        if not all_data:
            os.remove(temp_filename)
            return "No tables found in PDF"

        combined_df = pd.concat(all_data, ignore_index=True)
        output_filename = f"converted_{uuid.uuid4().hex}.xlsx"
        combined_df.to_excel(output_filename, index=False)

        os.remove(temp_filename)
        return send_file(output_filename, as_attachment=True)

    except Exception as e:
        os.remove(temp_filename)
        return f"Error processing file: {e}"

@app.route('/feedback', methods=['POST'])
def feedback():
    name = request.form.get('name')
    email = request.form.get('email')
    feedback_text = request.form.get('feedback')

    print(f"Feedback received from {name} ({email}): {feedback_text}")
    return render_template('index.html', feedback_thankyou=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
