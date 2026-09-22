# -*- coding: utf-8 -*-
"""Checks internal links in dist/ (run after build.py). Exit code 1 if something is broken."""
import os, sys, glob
from bs4 import BeautifulSoup

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
os.chdir(DIST)
redir = set(l.split()[0] for l in open('_redirects', encoding='utf-8') if len(l.split()) >= 2)
bad = {}
for f in glob.glob('**/*.html', recursive=True):
    s = BeautifulSoup(open(f, encoding='utf-8').read(), 'html.parser')
    for el in s.find_all(['a', 'link'], href=True) + s.find_all('script', src=True):
        h = el.get('href') or el.get('src')
        if not h.startswith('/') or h.startswith('//'):
            continue
        h = h.split('#')[0].split('?')[0]
        if h in redir or h.rstrip('/') in redir:
            continue
        cand = [h.lstrip('/') + 'index.html'] if h.endswith('/') else [h.lstrip('/'), h.lstrip('/') + '.html', h.lstrip('/') + '/index.html']
        if h == '/':
            cand = ['index.html']
        if not any(os.path.isfile(c) for c in cand):
            bad.setdefault(h, set()).add(f)
urls = open('sitemap.xml', encoding='utf-8').read().count('<url>')
print(f'{len(bad)} broken internal links; sitemap {urls} URLs')
for h, fs in bad.items():
    print(' ', h, '<-', sorted(fs)[:3])
sys.exit(1 if bad else 0)
