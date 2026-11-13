#!/usr/bin/env python3
"""Build the GIF manual and local MkDocs assets without changing the Markdown."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('assets', 'stylesheets', 'javascripts', 'images', 'search')


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.references = []
        self.ids = set()
        self.fragments = []
        self.tables = 0
        self.headings = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'img' and attrs.get('src'):
            self.images.append(attrs['src'])
        if tag == 'table':
            self.tables += 1
        if tag in ('h2', 'h3', 'h4', 'h5', 'h6'):
            self.headings += 1
        for key in ('src', 'href', 'poster'):
            if attrs.get(key):
                value = attrs[key]
                if value.startswith('#'):
                    if len(value) > 1:
                        self.fragments.append(unquote(value[1:]))
                elif not value.startswith(('data:', 'mailto:', 'tel:')):
                    self.references.append(value)


def require_local(reference: str, base: Path) -> Path:
    parts = urlsplit(reference)
    if parts.scheme or parts.netloc or reference.startswith('//'):
        raise ValueError(f'External dependency: {reference}')
    return base / unquote(parts.path)


def validate(output: Path) -> dict:
    text = (output / 'CEREBRO_AI_MANUAL.html').read_text(encoding='utf-8')
    parser = Resources()
    parser.feed(text)
    missing = sorted({ref for ref in parser.references if not require_local(ref, output).exists()})
    fragments = sorted(set(parser.fragments) - parser.ids)
    if missing or fragments:
        raise ValueError(f'Missing files: {missing}; missing anchors: {fragments}')
    gifs = sorted({ref for ref in parser.images if urlsplit(ref).path.lower().endswith('.gif')})
    for ref in gifs:
        path = require_local(ref, output)
        with path.open('rb') as handle:
            if handle.read(6) not in (b'GIF87a', b'GIF89a'):
                raise ValueError(f'Invalid GIF file: {ref}')
    return {
        'image_references': len(parser.images),
        'gif_references': sum(urlsplit(ref).path.lower().endswith('.gif') for ref in parser.images),
        'unique_gif_files': len(gifs),
        'tables': parser.tables,
        'section_headings': parser.headings,
        'missing_local_files': missing,
        'broken_internal_anchors': fragments,
        'external_page_dependencies': [],
    }


def lazy_images(text: str) -> str:
    def replace(match):
        tag = match.group()
        if re.search(r'\bheight\s*=', tag, re.I):
            return tag  # Inline button photographs keep their specified height.
        attributes = ' loading="lazy" decoding="async"'
        source = re.search(r'\bsrc\s*=\s*[\"\']([^\"\']+)[\"\']', tag, re.I)
        if source and urlsplit(source.group(1)).path.lower().endswith('.gif'):
            with require_local(source.group(1), ROOT).open('rb') as handle:
                header = handle.read(10)
            width, height = struct.unpack('<HH', header[6:10])
            declaration = f'--manual-gif-width: {width}px; --manual-gif-ratio: {width} / {height};'
            style = re.search(r'\bstyle\s*=\s*([\"\'])(.*?)\1', tag, re.I | re.S)
            if style:
                tag = tag[:style.end(2)] + ';' + declaration + tag[style.end(2):]
            else:
                attributes += f' style="{declaration}"'
        return tag[:-1].rstrip().rstrip('/') + attributes + '>'
    return re.sub(r'<img\b[^>]*>', replace, text, flags=re.I)


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--source', type=Path, default=ROOT / 'CEREBRO_AI_MANUAL_v0.3.md')
    args.add_argument('--output', type=Path, default=ROOT, help='Output folder; defaults to the repository root.')
    options = args.parse_args()
    source, output = options.source.resolve(), options.output.resolve()
    try:
        import mkdocs  # noqa: F401
    except ImportError:
        sys.exit('Install dependencies first: python3 -m pip install -r tools/requirements-manual-html.txt')
    original_bytes = source.read_bytes()
    original_hash = hashlib.sha256(original_bytes).hexdigest()
    visible = re.sub(r'<!--.*?-->', '', original_bytes.decode('utf-8'), flags=re.S)
    original_resources = Resources()
    original_resources.feed(visible)
    local_files = set()
    for ref in original_resources.references:
        if ref.startswith('./Source/') or ref.startswith('Source/'):
            path = require_local(ref, ROOT).resolve()
            path.relative_to(ROOT)
            if not path.is_file():
                raise FileNotFoundError(path)
            local_files.add(path)
    with tempfile.TemporaryDirectory(prefix='cerebro-manual-') as temp:
        temp = Path(temp)
        docs, site = temp / 'docs', temp / 'site'
        docs.mkdir()
        (docs / 'CEREBRO_AI_MANUAL.md').write_bytes(original_bytes)
        (docs / 'index.md').write_text(
            '# CEREBRO AI MANUAL\n\n[CEREBRO AI 매뉴얼 열기](CEREBRO_AI_MANUAL.md)\n', encoding='utf-8')
        for directory in ('stylesheets', 'javascripts', 'images'):
            shutil.copytree(ROOT / directory, docs / directory)
        for path in local_files:
            target = docs / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            # The staging tree is temporary; hard links avoid an extra media copy.
            try:
                target.hardlink_to(path)
            except OSError:
                shutil.copy2(path, target)
        config = temp / 'mkdocs.yml'
        config.write_text(
            (ROOT / 'mkdocs.manual.yml').read_text(encoding='utf-8')
            + '\ndocs_dir: ' + json.dumps(str(docs))
            + '\nsite_dir: ' + json.dumps(str(site)) + '\n', encoding='utf-8')
        subprocess.run([sys.executable, '-m', 'mkdocs', 'build', '--clean', '--config-file', str(config)], check=True)
        for page in site.glob('*.html'):
            html = lazy_images(page.read_text(encoding='utf-8'))
            if page.name in ('CEREBRO_AI_MANUAL.html', 'index.html'):
                html = re.sub(r'<title>.*?</title>', '<title>CEREBRO AI MANUAL</title>', html, count=1, flags=re.S)
            page.write_text(html, encoding='utf-8')
        # Validate the complete temporary site before publishing any generated files.
        report = validate(site)
        expected_gifs = sum(ref.lower().endswith('.gif') for ref in original_resources.images)
        if report['gif_references'] != expected_gifs:
            raise ValueError(f'GIF count changed: {expected_gifs} -> {report["gif_references"]}')
        output.mkdir(parents=True, exist_ok=True)
        for directory in DIRECTORIES:
            if (site / directory).is_dir():
                shutil.copytree(site / directory, output / directory, dirs_exist_ok=True)
        for page in site.glob('*.html'):
            shutil.copy2(page, output / page.name)
        # At the repository root, original media is already in the correct location.
        if output != ROOT:
            for path in local_files:
                target = output / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        report = {**report, 'source': source.name, 'source_sha256': original_hash,
                  'gif_policy': 'Original animated GIFs retained without conversion.',
                  'referenced_media_files': len(local_files),
                  'media_bytes': sum(path.stat().st_size for path in local_files),
                  'theme': 'mkdocs-material 9.7.6'}
        validate(output)
        (output / 'manual-build.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if hashlib.sha256(source.read_bytes()).hexdigest() != original_hash:
        raise RuntimeError('Source Markdown changed during the build.')
    print(json.dumps({'html': str(output / 'CEREBRO_AI_MANUAL.html'), **report}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
