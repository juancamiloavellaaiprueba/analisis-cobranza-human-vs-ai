import re
from pathlib import Path

prohibited = [
    'causa', 'demuestra', 'superior', 'mejor', 'peor', 
    'efectivo', 'eficiencia', 'garantiza', 'domina', 
    'fracasa', 'estéril', '5 veces', 'significativo'
]

targets = [
    Path('reports/informe.html'),
    Path('reports/anexo_tecnico.html')
]

for t in targets:
    print('=== Checking:', t)
    text = t.read_text(encoding='utf-8')
    for word in prohibited:
        matches = list(re.finditer(re.escape(word), text, re.IGNORECASE))
        if matches:
            print(f'  Word: "{word}" (total: {len(matches)})')
            for m in matches[:4]:
                start = max(0, m.start() - 50)
                end = min(len(text), m.end() + 50)
                snippet = text[start:end].replace('\n', ' ').encode('ascii', 'backslashreplace').decode('ascii')
                print(f'    [{m.start()}] ...{snippet}...')
