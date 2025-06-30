from flask import Flask, jsonify
import imaplib
import email
from email.header import decode_header
import os

app = Flask(__name__)

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_SERVER = "imap.gmail.com"

def get_latest_email():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")

    # Obtenir le dernier email
    status, data = mail.search(None, 'ALL')
    mail_ids = data[0].split()
    latest_id = mail_ids[-1]

    status, data = mail.fetch(latest_id, '(RFC822)')
    raw_email = data[0][1]
    msg = email.message_from_bytes(raw_email)

    # Décodage sujet
    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding or "utf-8", errors="ignore")

    from_ = msg.get("From")
    to_ = msg.get("To")
    date_ = msg.get("Date")

    # Lecture du corps
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get("Content-Disposition"):
                body = part.get_payload(decode=True).decode(errors="ignore")
                break
    else:
        body = msg.get_payload(decode=True).decode(errors="ignore")

    return {
        "from": from_,
        "to": to_,
        "subject": subject,
        "date": date_,
        "body": body.strip()
    }

@app.route("/email", methods=["GET"])
def email_route():
    try:
        return jsonify(get_latest_email())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
