from flask import Flask, jsonify
import os
import imaplib
import email
from email.header import decode_header
import re

app = Flask(__name__)

EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

def normalize_linebreaks(text):
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r' {2,}', ' ', text)
    return text

def clean_text(text):
    text = text.replace('*', '')
    text = re.sub(r'(\n){1,5}$', '', text.strip(), flags=re.MULTILINE)
    return text

def extract_parts(text):
    text = text.strip().replace('\r', '')
    lines = text.split('\n')

    lines = [line for line in lines if not re.fullmatch(r'[*\s\-_=~#]+', line.strip())]

    title = lines[0].strip() if len(lines) > 0 else ""
    basmala = lines[2].strip() if len(lines) > 2 else ""

    content_lines = lines[3:]
    content = "\n".join(content_lines)
    content = normalize_linebreaks(content)

    truncation_keywords = [
        "Retrouvez le hadith du jour",
        "www.hadithdujour.com",
        "officielhadithdujour@gmail.com",
        "désinscription",
        "Afficher l'intégralité",
        "Message tronqué",
    ]
    for kw in truncation_keywords:
        content = content.split(kw)[0]

    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    content_lines = content.split('\n')

    arabic_start_index = None
    for i, line in enumerate(content_lines):
        if arabic_pattern.search(line):
            arabic_start_index = i
            break

    if arabic_start_index is not None:
        hadith_fr = "\n".join(content_lines[:arabic_start_index]).strip()
        hadith_ar = "\n".join(content_lines[arabic_start_index:]).strip()
    else:
        hadith_fr = content.strip()
        hadith_ar = ""

    return {
        "title": clean_text(title),
        "basmala": clean_text(basmala),
        "hadith_fr": clean_text(hadith_fr),
        "hadith_ar": clean_text(hadith_ar)
    }

def decode_body(part):
    payload = part.get_payload(decode=True)
    for encoding in ['utf-8', 'latin1', 'windows-1252']:
        try:
            return payload.decode(encoding)
        except (UnicodeDecodeError, AttributeError):
            continue
    return payload.decode('utf-8', errors='replace')

@app.route("/email", methods=["GET"])
def get_latest_email():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        if not email_ids:
            return jsonify({"error": "Aucun mail trouvé"}), 404
        latest_email_id = email_ids[-1]

        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        if msg.is_multipart():
            body = None
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = decode_body(part)
                    break
            if body is None:
                return jsonify({"error": "Aucun contenu text/plain trouvé"}), 404
        else:
            body = decode_body(msg)

        result = extract_parts(body)
        return jsonify(result)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
