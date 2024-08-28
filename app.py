from flask import Flask, render_template, request, send_file, redirect, url_for, session
import os
import ocrmypdf
from werkzeug.utils import secure_filename
import zipfile
from threading import Thread
import uuid
import PyPDF2
import tempfile

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
    processed_files = []
    total_files = len(uploaded_file_paths)
    progress[session_id] = {'percent': 0, 'filename': '', 'ocr_progress': 0}

    for i, file_path in enumerate(uploaded_file_paths):
        filename = os.path.basename(file_path)
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        temp_folder = tempfile.mkdtemp()

        # Get the number of pages
        reader = PyPDF2.PdfReader(file_path)
        total_pages = len(reader.pages)

        for page_num in range(total_pages):  # Page numbers are 0-indexed
            # Create a temporary single-page PDF
            writer = PyPDF2.PdfWriter()
            writer.add_page(reader.pages[page_num])
            single_page_path = os.path.join(temp_folder, f"page_{page_num + 1}.pdf")
            
            with open(single_page_path, 'wb') as temp_pdf:
                writer.write(temp_pdf)

            # Process single-page PDF
            ocrmypdf.ocr(single_page_path, single_page_path.replace('.pdf', '_ocr.pdf'))

            # Track progress for the current page
            ocr_progress = ((page_num + 1) / total_pages) * 100
            progress[session_id]['ocr_progress'] = ocr_progress
            progress[session_id]['filename'] = filename

        # Combine all processed pages into one PDF
        with open(output_path, 'wb') as output_pdf:
            writer = PyPDF2.PdfWriter()
            for page_num in range(total_pages):
                processed_page_path = os.path.join(temp_folder, f"page_{page_num + 1}_ocr.pdf")
                with open(processed_page_path, 'rb') as processed_pdf:
                    reader = PyPDF2.PdfReader(processed_pdf)
                    writer.add_page(reader.pages[0])
            writer.write(output_pdf)

        processed_files.append(output_path)

        # Update the overall progress after processing the file
        progress[session_id] = {
            'percent': ((i + 1) / total_files) * 100,
            'filename': filename,
            'ocr_progress': 100
        }

    # Create a zip file with the processed PDFs
    zip_filename = 'processed_pdfs.zip'
    zip_filepath = os.path.join(app.config['PROCESSED_FOLDER'], zip_filename)
    with zipfile.ZipFile(zip_filepath, 'w') as zipf:
        for processed_file in processed_files:
            zipf.write(processed_file, os.path.basename(processed_file))

    # Mark progress as complete
    progress[session_id] = {
        'percent': 100,
        'filename': 'All files processed',
        'ocr_progress': 100
    }

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
