def extract_parts(text):
    text = text.strip().replace('\r', '')
    lines = text.split('\n')

    # Supprime lignes décoratives
    lines = [line for line in lines if not re.fullmatch(r'[*\s\-_=~#]+', line.strip())]

    title = lines[0].strip() if len(lines) > 0 else ""
    basmala = lines[1].strip() if len(lines) > 1 else ""

    content_lines = lines[2:]
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
