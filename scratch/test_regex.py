import re

text = "[PT] Olá! Vamos aprender alemão. [DE] Hallo! Wie geht es dir? [PT] Responde em alemão:"
parts = re.split(r'(\[[A-Z]{2,3}\])', text)
print(parts)

chunks = []
current_lang = "pt"
for part in parts:
    part = part.strip()
    if not part: continue
    if re.match(r'^\[[A-Z]{2,3}\]$', part):
        current_lang = part[1:-1].lower()
    else:
        chunks.append((current_lang, part))

print(chunks)
