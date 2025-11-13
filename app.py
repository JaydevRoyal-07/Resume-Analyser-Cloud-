from flask import Flask, request, jsonify
import os, re
from pdfminer.high_level import extract_text
from docx import Document
from tika import parser

app = Flask(__name__)

def extract_text_from_file(filepath, filename):
    lower = filename.lower()
    try:
        if lower.endswith('.pdf'):
            return extract_text(filepath)
        elif lower.endswith('.docx') or lower.endswith('.doc'):
            doc = Document(filepath)
            return '\n'.join([p.text for p in doc.paragraphs])
        else:
            parsed = parser.from_file(filepath)
            return parsed.get('content') or ''
    except Exception:
        try:
            parsed = parser.from_file(filepath)
            return parsed.get('content') or ''
        except:
            return ''

EMAIL_RE = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
PHONE_RE = re.compile(r'(\+?\d{1,3}[\s-]?)?(\(?\d{2,4}\)?[\s-]?)?[\d\s-]{6,15}')
SKILLS_KEYWORDS = ['python','java','c++','c#','javascript','react','node','express','sql','postgres','mongodb','aws','azure','docker','kubernetes','machine learning','ml','nlp','tensorflow','pytorch']
EDU_KEYWORDS = ['bachelor','b.sc','btech','b.tech','master','m.sc','mtech','phd','mba','degree']

def extract_skills(text):
    found = set()
    txt = text.lower()
    for kw in SKILLS_KEYWORDS:
        if kw in txt:
            found.add(kw)
    return sorted(found)

def extract_education(text):
    edu = []
    low = text.lower()
    for k in EDU_KEYWORDS:
        if k in low:
            edu.append(k)
    return list(set(edu))

def extract_emails(text):
    return list(set(EMAIL_RE.findall(text)))

def extract_phones(text):
    phones = []
    for m in PHONE_RE.findall(text):
        phones.append(''.join(m))
    phones = [p.strip() for p in phones if len(re.sub(r'\D','',p)) >= 8]
    return list(set(phones))

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error':'no file'}), 400
    f = request.files['file']
    filename = f.filename
    tmp_path = os.path.join('/tmp', f.filename)
    f.save(tmp_path)
    text = extract_text_from_file(tmp_path, filename) or ''
    emails = extract_emails(text)
    phones = extract_phones(text)
    skills = extract_skills(text)
    education = extract_education(text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    name = None
    if lines:
        first = lines[0]
        if 1 < len(first.split()) <= 4 and any(c.isalpha() for c in first):
            name = first.strip()
    score = 0
    score += min(40, len(skills) * 10)
    if emails: score += 20
    if phones: score += 20
    if education: score += 20
    score = min(100, score)
    result = {
        'name': name,
        'emails': emails,
        'phones': phones,
        'skills': skills,
        'education': education,
        'summary': lines[:5],
        'score': score,
        'raw_text_sample': text[:1000]
    }
    try:
        os.remove(tmp_path)
    except:
        pass
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000)
