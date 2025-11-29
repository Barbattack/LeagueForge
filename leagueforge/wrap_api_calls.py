#!/usr/bin/env python3
"""Script per wrappare tutte le API calls con safe_api_call e delay"""

import re

def wrap_api_calls(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern da wrappare
    patterns = [
        # get_all_values()
        (r'(\w+)\.get_all_values\(\)', r'safe_api_call(\1.get_all_values)'),
        # append_rows() - già fatto ma per sicurezza
        (r'(\w+)\.append_rows\(([^)]+)\)', r'safe_api_call(\1.append_rows, \2)'),
        # append_row()
        (r'(\w+)\.append_row\(([^)]+)\)', r'safe_api_call(\1.append_row, \2)'),
        # batch_update()
        (r'(\w+)\.batch_update\(([^)]+)\)', r'safe_api_call(\1.batch_update, \2)'),
        # update()
        (r'(\w+)\.update\(([^)]+)\)', r'safe_api_call(\1.update, \2)'),
        # update_cell()
        (r'(\w+)\.update_cell\(([^)]+)\)', r'safe_api_call(\1.update_cell, \2)'),
    ]

    # Già wrappate (per evitare doppi wrap)
    already_wrapped = set()

    # Apply patterns
    for pattern, replacement in patterns:
        # Trova tutte le occorrenze
        for match in re.finditer(pattern, content):
            full_match = match.group(0)
            if 'safe_api_call' not in full_match and full_match not in already_wrapped:
                already_wrapped.add(full_match)
                content = content.replace(full_match, re.sub(pattern, replacement, full_match))

    # Aggiungi api_delay() prima di ogni safe_api_call (se non già presente)
    lines = content.split('\n')
    new_lines = []
    for i, line in enumerate(lines):
        new_lines.append(line)
        # Se questa riga ha safe_api_call e la precedente non ha api_delay()
        if 'safe_api_call(' in line and i > 0:
            prev_line = lines[i-1].strip()
            if 'api_delay()' not in prev_line:
                # Calcola indentazione
                indent = len(line) - len(line.lstrip())
                new_lines.insert(-1, ' ' * indent + 'api_delay()')

    # Scrivi il file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print(f"✓ Wrappate tutte le API calls in {filepath}")

if __name__ == '__main__':
    wrap_api_calls('import_base.py')
