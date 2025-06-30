import imaplib
import email
import os
from flask import Flask, jsonify
from email.header import decode_header

app = Flask(__name__)

EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

def clean_hadith(body):
    # Ne garder que la partie utile : on coupe à la mention "Retrouvez le hadith"
    if "Retrouvez le hadith" in body:
        body = body.split("Retrouvez le hadith")[0]

    # Supprimer les double-astérisques ** qui encadrent parfois des titres
    body = body.replace("**", "")

    # Supprimer les espaces superflus
    return body.strip()

def get_latest_email_content():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USER, EMAIL_PASS)
        imap.select("inbox")

        status, messages = imap.search(None, "ALL")
        if status != "OK":
            return None

        latest_email_id = messages[0].split()[-1]
        _, msg_data = imap.fetch(latest_email_id, "(RFC822)")

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")

                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8")

                return {
                    "subject": subject.strip(),
                    "body": clean_hadith(body)
                }

        imap.logout()

    except Exception as e:
        return {"error": str(e)}

@app.route("/email", methods=["GET"])
def get_email():
    content = get_latest_email_content()
    if not content:
        return jsonify({"error": "Aucun message trouvé."}), 404
    return jsonify(content)

if __name__ == "__main__":
    app.run(debug=True)
