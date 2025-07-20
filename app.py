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

            # Save the file temporarily to read again later
            temp_pdf_path = "uploaded_temp.pdf"
            file.save(temp_pdf_path)

            # Check if it's a TD Bank Statement based on text
            with pdfplumber.open(temp_pdf_path) as pdf_check:
                first_page_text = pdf_check.pages[0].extract_text() or ""

            if "TD ALL-INCLUSIVE BANKING PLAN" in first_page_text:
                # TD-specific cleaning
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
                                    float(amount_part)  # Validate
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
                # Fallback to your existing table logic
                repeated_headers = set()
                dfs = []

                with pdfplumber.open(temp_pdf_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        table = page.extract_table()
                        if not table:
