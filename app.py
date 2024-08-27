from flask import Flask, render_template, request, send_file
import os
import ocrmypdf
from werkzeug.utils import secure_filename
import zipfile  # This is the correct way to import zipfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'

# Ensure upload and processed folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        # Get the list of uploaded files
        uploaded_files = request.files.getlist("file[]")
        processed_files = []

        for file in uploaded_files:
            if file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)

                # Save the uploaded PDF
                file.save(input_path)

                # Run ocrmypdf on the saved PDF
                ocrmypdf.ocr(input_path, output_path)

                processed_files.append(output_path)

        # Create a zip file with the processed PDFs
        zip_filename = 'processed_pdfs.zip'
        zip_filepath = os.path.join(app.config['PROCESSED_FOLDER'], zip_filename)
        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            for processed_file in processed_files:
                zipf.write(processed_file, os.path.basename(processed_file))

        return send_file(zip_filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
