from flask import Flask, jsonify
import os
import imaplib
import email
from email.header import decode_header
import re

app = Flask(__name__)

EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

def extract_parts(text):
    # Nettoyage de base
    text = text.strip().replace('\r', '')
    lines = text.split('\n')

    # Retire les lignes décoratives (comme "*************")
    lines = [line for line in lines if not re.fullmatch(r'[*\s\-_=~#]+', line.strip())]

    # Reprendre le titre et la basmala après nettoyage
    title = lines[0].strip() if len(lines) > 0 else ""
    basmala = lines[1].strip() if len(lines) > 1 else ""

    # Reste du contenu
    content = "\n".join(lines[2:])

    # Supprimer ce qui vient après du contenu inutile
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

    # Identifier le hadith en arabe
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    lines_cleaned = content.split('\n')

    arabic_start_index = None
    for i, line in enumerate(lines_cleaned):
        if arabic_pattern.search(line):
            arabic_start_index = i
            break

    if arabic_start_index is not None:
        hadith_fr = "\n".join(lines_cleaned[:arabic_start_index]).strip()
        hadith_ar = "\n".join(lines_cleaned[arabic_start_index:]).strip()
    else:
        hadith_fr = content.strip()
        hadith_ar = ""

    return {
        "title": title,
        "basmala": basmala,
        "hadith_fr": hadith_fr,
        "hadith_ar": hadith_ar
    }

@app.route("/email", methods=["GET"])
def get_latest_email():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        latest_email_id = email_ids[-1]

        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()

        result = extract_parts(body)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Pour Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
