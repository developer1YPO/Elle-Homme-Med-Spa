"""Static loading checks; optionally compare preservation against a Git revision.
Run: python3 tests/performance_audit.py --baseline <revision>
"""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def missing_resources(name, source):
    missing = set()
    for tag, attrs in Page(source).tags:
        urls = [attrs[k] for k in ('src', 'href') if attrs.get(k)]
        for key in ('srcset', 'imagesrcset'):
            urls.extend(part.strip().split()[0] for part in attrs.get(key, '').split(',') if part.strip())
        for url in urls:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith('/_vercel/'):
                continue
            target = ROOT / unquote(parsed.path.lstrip('/')) if parsed.path.startswith('/') else ROOT / name.parent / unquote(parsed.path)
            if not target.exists() and not target.with_suffix('.html').exists() and not (target / 'index.html').exists():
                missing.add((str(name), url))
    return missing


def preserved_source(source):
    # Only normalize explicitly authorized loading changes. Everything else must match.
    source = re.sub(r'<script\b[^>]*src="https://ajax.googleapis.com/ajax/libs/webfont/[^>]*></script>', '', source)
    source = re.sub(r'<script\b[^>]*>WebFont.load\(.*?</script>', '', source, flags=re.S)
    source = re.sub(r'<style>@import url\(\'https://fonts.googleapis.com/[^<]*</style>', '', source)
    source = re.sub(r'<link\b[^>]*href="https://fonts.googleapis.com/css2\?[^>]*>', '', source)
    source = re.sub(r'<link\b[^>]*rel="preload"[^>]*>', '', source)
    source = re.sub(r'<img\b[^>]*class="header83_background-image"[^>]*>', '', source)

    def normalize_image(match):
        tag = match.group()
        if re.search(r'class="header(?:37|36|65|69)_(?:background-)?image"', tag):
            tag = re.sub(r'\s(?:width|height|loading|fetchpriority)="[^"]*"', '', tag)
        return tag

    source = re.sub(r'<img\b[^>]*>', normalize_image, source)
    return re.sub(r'>\s+<', '><', source).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', help='Git revision before the optimization')
    args = parser.parse_args()
    pages = sorted([*ROOT.glob('*.html'), *ROOT.glob('pages/*.html')])
    missing = set()
    previous_missing = set()
    for path in pages:
        name = path.relative_to(ROOT)
        source = path.read_text()
        assert 'WebFont' not in source and '@import' not in source, name
        fonts = [attrs for tag, attrs in Page(source).tags if tag == 'link' and 'fonts.googleapis.com/css2?' in attrs.get('href', '')]
        assert len(fonts) == 1 and 'display=swap' in fonts[0]['href'], name
        assert source.count('/_vercel/speed-insights/script.js') == 1, name
        priority = [attrs for tag, attrs in Page(source).tags if tag == 'img' and attrs.get('fetchpriority') == 'high']
        assert len(priority) <= 1, name
        for image in priority:
            assert image.get('loading') == 'eager', name
            if not image.get('src', '').endswith('.svg'):
                assert int(image['width']) > 0 and int(image['height']) > 0, name
        missing |= missing_resources(name, source)
        if args.baseline:
            old = subprocess.check_output(['git', 'show', f'{args.baseline}:{name}'], cwd=ROOT, text=True)
            assert preserved_source(old) == preserved_source(source), f'Unexpected content/integration change: {name}'
            previous_missing |= missing_resources(name, old)
    homepage = Page((ROOT / 'index.html').read_text()).tags
    preload = next(a for t, a in homepage if t == 'link' and a.get('rel') == 'preload')
    hero = next(a for t, a in homepage if t == 'img' and a.get('class') == 'header83_background-image')
    assert preload['imagesrcset'] == hero['srcset'] and preload['imagesizes'] == hero['sizes']
    assert preload['href'] == hero['src']
    assert 'font-display: swap;' in (ROOT / 'css/components.css').read_text()
    if args.baseline:
        assert not missing - previous_missing, f'New missing resources: {missing - previous_missing}'
    else:
        assert not missing, f'Missing resources: {missing}'
    print(f'PASS: {len(pages)} HTML pages; font loading, hero priority/preload, Speed Insights, and local resources checked.')
    if args.baseline:
        print('PASS: content, metadata, links, forms, integration scripts and attributes preserved against baseline.')
    if missing:
        print('Existing missing resources (unchanged):')
        for item in sorted(missing):
            print('  ', *item)


if __name__ == '__main__':
    main()
