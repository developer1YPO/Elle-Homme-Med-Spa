"""Verify that form scheduling is the only HTML change vs merged PR #7."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
count = 0
frames = 0
scripts = 0
for p in sorted([*ROOT.glob('*.html'), *ROOT.glob('pages/*.html')]):
    source = p.read_text()
    old = subprocess.check_output(['git', 'show', f'61a4222:{p.relative_to(ROOT)}'], cwd=ROOT, text=True)
    normalized = source.replace('<script defer src="https://link.msgsndr.com/js/form_embed.js">', '<script src="https://link.msgsndr.com/js/form_embed.js">')
    normalized = normalized.replace('<iframe loading="lazy"', '<iframe')
    assert normalized == old, p
    for tag in re.findall(r'<iframe\b[^>]*>', source):
        if 'loading="lazy"' in tag:
            assert any(f'id="inline-{i}"' in tag for i in ('rsssEcgmWCPzGVS0JZVa', 'roREHpypb8bsGL5YdAMg')), p
            frames += 1
    assert '<script src="https://link.msgsndr.com/js/form_embed.js">' not in source, p
    scripts += source.count('<script defer src="https://link.msgsndr.com/js/form_embed.js">')
    count += 1
print(f'PASS: {count} pages; {frames} below-fold frames lazy; {scripts} form scripts deferred.')
print('All iframe URLs/attributes, script counts/order, metadata, links, content and other integrations unchanged.')
