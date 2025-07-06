def extract_parts(text):
    import re

    def clean_text(t):
        return t.strip()

    def normalize_linebreaks(t):
        return re.sub(r'\n{2,}', '\n\n', t)

    text = text.strip().replace('\r', '')
    lines = text.split('\n')

    # Supprimer les lignes décoratives
    lines = [line for line in lines if not re.fullmatch(r'[*\s\-_=~#]+', line.strip())]

    title = lines[0].strip() if len(lines) > 0 else ""
    basmala = lines[1].strip() if len(lines) > 1 else ""

    content_lines = lines[2:]

    # Supprimer le bas de page inutile
    truncation_keywords = [
        "Retrouvez le hadith du jour",
        "www.hadithdujour.com",
        "officielhadithdujour@gmail.com",
        "désinscription",
        "Afficher l'intégralité",
        "Message tronqué",
    ]
    content = "\n".join(content_lines)
    for kw in truncation_keywords:
        if kw in content:
            content = content.split(kw)[0]
            break

    content_lines = content.split('\n')

    # Trouver la première ligne contenant de l'arabe
    arabic_line_index = None
    arabic_re = re.compile(r'[\u0600-\u06FF]')

    for i, line in enumerate(content_lines):
        if arabic_re.search(line):
            arabic_line_index = i
            break

    if arabic_line_index is not None:
        hadith_fr = "\n".join(content_lines[:arabic_line_index]).strip()
        hadith_ar = "\n".join(content_lines[arabic_line_index:]).strip()
    else:
        hadith_fr = "\n".join(content_lines).strip()
        hadith_ar = ""

    return {
        "title": clean_text(title),
        "basmala": clean_text(basmala),
        "hadith_fr": clean_text(hadith_fr),
        "hadith_ar": clean_text(hadith_ar)
    }
