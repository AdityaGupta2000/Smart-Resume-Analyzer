from flask import Flask, render_template, request, make_response
from backend import extract_text_from_file, analyze_resume_with_agent
from fpdf import FPDF
import html
import re

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        resume_file = request.files.get('resume')
        jd_file = request.files.get('jd')

        if resume_file and jd_file:
            resume_text = extract_text_from_file(resume_file)
            jd_text = extract_text_from_file(jd_file)
            result = analyze_resume_with_agent(resume_text, jd_text)

    return render_template('index.html', result=result)

@app.route('/download', methods=['POST'])
def download_pdf():
    content = request.form.get('content', '')

    # Clean HTML/text safely
    clean_text = html.unescape(content)
    clean_text = re.sub(r'<[^>]+>', '', clean_text)  # Remove any HTML tags

    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for line in clean_text.splitlines():
        if line.strip():  # Avoid empty lines
            pdf.multi_cell(0, 10, line.strip())

    # Send file as response
    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=analysis_result.pdf'
    return response

if __name__ == '__main__':
    app.run(debug=True)
