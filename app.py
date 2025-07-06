import re

def clean_text(text):
    return text.strip()

def normalize_linebreaks(text):
    return re.sub(r'\n{2,}', '\n\n', text)

def extract_parts(text):
    text = text.strip().replace('\r', '')
    lines = text.split('\n')
    
    # Supprimer les lignes décoratives
    lines = [line for line in lines if not re.fullmatch(r'[*\s\-_=~#]+', line.strip())]

    title = lines[0].strip() if len(lines) > 0 else ""
    basmala = lines[1].strip() if len(lines) > 1 else ""

    content = "\n".join(lines[2:])
    content = normalize_linebreaks(content)

    # Supprimer le bas de page inutile
    truncation_keywords = [
        "Retrouvez le hadith du jour",
        "www.hadithdujour.com",
        "officielhadithdujour@gmail.com",
        "désinscription",
        "Afficher l'intégralité",
        "Message tronqué",
    ]
    for kw in truncation_keywords:
        if kw in content:
            content = content.split(kw)[0]

    # Trouver la première occurrence d’un caractère arabe
    match = re.search(r'[\u0600-\u06FF]', content)
    if match:
        index = match.start()
        hadith_fr = content[:index].strip()
        hadith_ar = content[index:].strip()
    else:
        hadith_fr = content.strip()
        hadith_ar = ""

    return {
        "title": clean_text(title),
        "basmala": clean_text(basmala),
        "hadith_fr": clean_text(hadith_fr),
        "hadith_ar": clean_text(hadith_ar)
    }
