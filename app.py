import os
import uuid
from flask import Flask, request, jsonify, send_file, render_template, after_this_request
from werkzeug.utils import secure_filename
from pdf2docx import Converter

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

UPLOAD_FOLDER = '/tmp/uploads'
OUTPUT_FOLDER = '/tmp/outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'error': '파일이 없습니다.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '파일을 선택해 주세요.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'PDF 파일만 업로드 가능합니다.'}), 400

    job_id = str(uuid.uuid4())
    original_name = secure_filename(file.filename)
    base_name = original_name.rsplit('.', 1)[0]

    pdf_path = os.path.join(UPLOAD_FOLDER, f'{job_id}.pdf')
    docx_path = os.path.join(OUTPUT_FOLDER, f'{job_id}.docx')

    file.save(pdf_path)

    try:
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
    except Exception as e:
        os.remove(pdf_path)
        return jsonify({'error': f'변환 중 오류가 발생했습니다: {str(e)}'}), 500

    os.remove(pdf_path)

    @after_this_request
    def cleanup(response):
        try:
            os.remove(docx_path)
        except Exception:
            pass
        return response

    download_name = f'{base_name}.docx'
    return send_file(
        docx_path,
        as_attachment=True,
        download_name=download_name,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
