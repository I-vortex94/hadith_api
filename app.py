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
    # Supprime les sauts de ligne simples (pas doubles), typiques des coupures de ligne automatiques
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r' {2,}', ' ', text)  # nettoyage des doubles espaces
    return text

def extract_parts(text):
    # Nettoyage de base
    text = text.strip().replace('\r', '')
    lines = text.split('\n')

    # Supprimer les lignes décoratives
    lines = [line for line in lines if not re.fullmatch(r'[*\s\-_=~#]+', line.strip())]

    # Extraire titre et basmala AVANT normalisation
    title = lines[0].strip() if len(lines) > 0 else ""
    basmala = lines[2].strip() if len(lines) > 2 else ""

    # Reconstituer le reste du contenu
    content_lines = lines[2:]
    content = "\n".join(content_lines)

    # Nettoyer les retours à la ligne automatiques uniquement sur le reste
    content = normalize_linebreaks(content)

    # Supprimer les lignes parasites
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

    # Détection de l'arabe
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
