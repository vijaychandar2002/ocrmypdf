from flask import Flask, render_template, request, send_file, redirect, url_for, session
import os
import ocrmypdf
from werkzeug.utils import secure_filename
import zipfile
from threading import Thread
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed to use sessions
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

# Ensure upload and processed folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

progress = {}  # To track progress of each session

def process_pdfs(session_id, uploaded_file_paths):
    """
    Process PDFs for OCR and update the progress.
    """
    processed_files = []
    total_files = len(uploaded_file_paths)
    progress[session_id] = {'percent': 0, 'filename': ''}

    for i, file_path in enumerate(uploaded_file_paths):
        filename = os.path.basename(file_path)
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)

        # Update progress with the current file being processed
        progress[session_id] = {'percent': (i / total_files) * 100, 'filename': filename}

        # Run OCRmyPDF on the saved PDF
        ocrmypdf.ocr(file_path, output_path)
        processed_files.append(output_path)

        # Update progress after processing
        progress[session_id] = {'percent': ((i + 1) / total_files) * 100, 'filename': filename}

    # Create a zip file with the processed PDFs
    zip_filename = 'processed_pdfs.zip'
    zip_filepath = os.path.join(app.config['PROCESSED_FOLDER'], zip_filename)
    with zipfile.ZipFile(zip_filepath, 'w') as zipf:
        for processed_file in processed_files:
            zipf.write(processed_file, os.path.basename(processed_file))

    # Mark progress as complete
    progress[session_id] = {'percent': 100, 'filename': 'All files processed'}

@app.route('/')
def index():
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    return render_template('index.html', session_id=session_id)

@app.route('/upload', methods=['POST'])
def upload():
    session_id = session.get('session_id')
    uploaded_files = request.files.getlist("file[]")
    uploaded_file_paths = []

    # Save each uploaded file to the uploads directory
    for file in uploaded_files:
        if file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            uploaded_file_paths.append(file_path)

    # Start a new thread for processing files
    thread = Thread(target=process_pdfs, args=(session_id, uploaded_file_paths))
    thread.start()

    return redirect(url_for('progress_page', session_id=session_id))

@app.route('/progress/<session_id>')
def progress_page(session_id):
    """
    Display the progress page.
    """
    return render_template('progress.html', session_id=session_id)

@app.route('/status/<session_id>')
def status(session_id):
    return progress.get(session_id, {'percent': 0, 'filename': 'No file being processed'})

@app.route('/download/<session_id>')
def download(session_id):
    """
    Download the zip file after processing.
    """
    zip_filepath = os.path.join(app.config['PROCESSED_FOLDER'], 'processed_pdfs.zip')
    if os.path.exists(zip_filepath):
        return send_file(zip_filepath, as_attachment=True)
    return "No file available for download."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
