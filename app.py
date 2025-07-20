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
