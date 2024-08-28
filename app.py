from flask import Flask, render_template, request, send_file, redirect, url_for, session, jsonify
import os
import ocrmypdf
from werkzeug.utils import secure_filename
import zipfile
from threading import Thread
import uuid
import PyPDF2
import tempfile

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

progress = {}  # To track progress of each session
stop_signals = {}  # To handle stop signals for each session


def process_pdfs(session_id, uploaded_file_paths):
    processed_files = []
    total_files = len(uploaded_file_paths)
    progress[session_id] = {
        'percent': 0,
        'filename': '',
        'ocr_progress': 0,
        'current_file_index': 0,
        'total_files': total_files,
        'pages_done': 0,
        'total_pages': 0
    }
    
    stop_signals[session_id] = False  # Initialize stop signal for this session

    for i, file_path in enumerate(uploaded_file_paths):
        if stop_signals[session_id]:
            break  # Stop processing if stop signal is received

        filename = os.path.basename(file_path)
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        temp_folder = tempfile.mkdtemp()

        reader = PyPDF2.PdfReader(file_path)
        total_pages = len(reader.pages)

        progress[session_id]['filename'] = filename
        progress[session_id]['total_pages'] = total_pages
        progress[session_id]['current_file_index'] = i
        progress[session_id]['pages_done'] = 0

        for page_num in range(total_pages):  
            if stop_signals[session_id]:
                break  # Stop processing if stop signal is received

            writer = PyPDF2.PdfWriter()
            writer.add_page(reader.pages[page_num])
            single_page_path = os.path.join(temp_folder, f"page_{page_num + 1}.pdf")
            
            with open(single_page_path, 'wb') as temp_pdf:
                writer.write(temp_pdf)

            ocrmypdf.ocr(single_page_path, single_page_path.replace('.pdf', '_ocr.pdf'))

            ocr_progress = ((page_num + 1) / total_pages) * 100
            progress[session_id]['ocr_progress'] = ocr_progress
            progress[session_id]['pages_done'] = page_num + 1

        if not stop_signals[session_id]:
            with open(output_path, 'wb') as output_pdf:
                writer = PyPDF2.PdfWriter()
                for page_num in range(total_pages):
                    processed_page_path = os.path.join(temp_folder, f"page_{page_num + 1}_ocr.pdf")
                    with open(processed_page_path, 'rb') as processed_pdf:
                        reader = PyPDF2.PdfReader(processed_pdf)
                        writer.add_page(reader.pages[0])
                writer.write(output_pdf)

            processed_files.append(output_path)

            progress[session_id] = {
                'percent': ((i + 1) / total_files) * 100,
                'filename': filename,
                'ocr_progress': 100,
                'current_file_index': i,
                'total_files': total_files,
                'pages_done': total_pages,
                'total_pages': total_pages
            }

    zip_filename = 'processed_pdfs.zip'
    zip_filepath = os.path.join(app.config['PROCESSED_FOLDER'], zip_filename)
    with zipfile.ZipFile(zip_filepath, 'w') as zipf:
        for processed_file in processed_files:
            zipf.write(processed_file, os.path.basename(processed_file))

    progress[session_id]['percent'] = 100

@app.route('/')
def index():
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    return render_template('index.html', session_id=session_id)

@app.route('/upload', methods=['POST'])
def upload():
    session_id = session.get('session_id')
    uploaded_files = request.files.getlist("file[]")
    uploaded_file_paths = []

    for file in uploaded_files:
        if file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            uploaded_file_paths.append(file_path)

    thread = Thread(target=process_pdfs, args=(session_id, uploaded_file_paths))
    thread.start()

    return redirect(url_for('progress_page', session_id=session_id))

@app.route('/progress/<session_id>')
def progress_page(session_id):
    return render_template('progress.html', session_id=session_id)

@app.route('/status/<session_id>')
def status(session_id):
    return jsonify(progress.get(session_id, {'percent': 0, 'filename': 'No file being processed'}))

@app.route('/stop/<session_id>', methods=['POST'])
def stop(session_id):
    stop_signals[session_id] = True  # Set stop signal
    return jsonify({'status': 'stopped'})

@app.route('/download/<session_id>')
def download(session_id):
    zip_filepath = os.path.join(app.config['PROCESSED_FOLDER'], 'processed_pdfs.zip')

    # Check if the processing was stopped before any PDF was completed
    if progress.get(session_id, {}).get('percent', 0) == 0:
        return "No files were processed. Please try again."

    if os.path.exists(zip_filepath):
        return send_file(zip_filepath, as_attachment=True)
    
    return "No file available for download."


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
