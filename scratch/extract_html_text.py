import re

with open("Prueba técnica Creceré AI.html", "r", encoding="utf-8") as f:
    content = f.read()

content = re.sub(r'data:image/[^"\'\s]+', '', content)
content = re.sub(r'<style>.*?</style>', '', content, flags=re.DOTALL)
content = re.sub(r'<script>.*?</script>', '', content, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', '\n', content)
lines = [l.strip() for l in text.splitlines() if l.strip()]
clean_text = "\n".join(lines)

with open("scratch/prueba_original_texto.txt", "w", encoding="utf-8") as f:
    f.write(clean_text)

print("Saved cleanly. Line count:", len(lines))
