import json

with open('/root/.openmausbot/routines.json', 'r') as f:
    d = json.load(f)

for r in d.get('routines', []):
    if r.get('id') == 'd7442499-ec81-4573-b684-1275063a13dd':
        prompt = r.get('prompt')
        with open('/tmp/cycle_prompt.txt', 'w', encoding='utf-8') as pf:
            pf.write(prompt)
        print("Prompt guardado en /tmp/cycle_prompt.txt con longitud:", len(prompt))
        print("Primeras 3 líneas:")
        print('\n'.join(prompt.split('\n')[:3]))
        break
