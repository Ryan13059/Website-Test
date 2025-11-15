#!/usr/bin/env python3
# Lightweight smoke-check script for my-website HTML files.
# Checks: DOCTYPE, <html lang>, viewport meta, <title>, <img> alt, <figure>/<figcaption>, "Under Construction"

import os
import re
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parents[1]  # one level up from tools/
HTML_GLOB = "*.html"

def read_text(path):
    return path.read_text(encoding='utf-8', errors='ignore')

def check_file(path):
    text = read_text(path)
    lower = text.lower()
    results = {
        'path': str(path.relative_to(SITE_DIR)),
        'doctype': bool(re.search(r"<!doctype\s+html", lower)),
        'html_lang': bool(re.search(r"<html[^>]*\slang=\"[^\"]+\"|<html[^>]*\slang='[^']+'", text, re.IGNORECASE)),
        'viewport': bool(re.search(r"<meta[^>]+name=[\"']viewport[\"']", lower)),
        'title': bool(re.search(r"<title>.*?</title>", lower, re.DOTALL)),
        'imgs': [],
        'figures': 0,
        'figcaptions': 0,
        'under_construction': 'under construction' in lower,
    }

    # Find <img ...>
    for m in re.finditer(r"<img\s+([^>]+)>", text, re.IGNORECASE):
        attrs = m.group(1)
        alt_m = re.search(r"alt\s*=\s*\"([^\"]*)\"|alt\s*=\s*'([^']*)'", attrs, re.IGNORECASE)
        src_m = re.search(r"src\s*=\s*\"([^\"]*)\"|src\s*=\s*'([^']*)'", attrs, re.IGNORECASE)
        src = src_m.group(1) if src_m else ''
        alt = ''
        if alt_m:
            alt = alt_m.group(1) or alt_m.group(2) or ''
        results['imgs'].append({'src': src, 'alt': alt, 'has_alt': bool(alt.strip())})

    # figures and figcaptions
    results['figures'] = len(re.findall(r"<figure", lower))
    results['figcaptions'] = len(re.findall(r"<figcaption", lower))

    return results


def run_checks():
    html_files = sorted(SITE_DIR.glob(HTML_GLOB))
    if not html_files:
        print(f"No HTML files found in {SITE_DIR}")
        return 1

    all_results = []
    summary = {
        'files': 0,
        'missing_doctype': [],
        'missing_lang': [],
        'missing_viewport': [],
        'missing_title': [],
        'images_missing_alt': [],
        'figures_missing_figcaptions': [],
        'under_construction': []
    }

    for path in html_files:
        res = check_file(path)
        all_results.append(res)
        summary['files'] += 1
        if not res['doctype']:
            summary['missing_doctype'].append(res['path'])
        if not res['html_lang']:
            summary['missing_lang'].append(res['path'])
        if not res['viewport']:
            summary['missing_viewport'].append(res['path'])
        if not res['title']:
            summary['missing_title'].append(res['path'])
        # images
        for img in res['imgs']:
            if not img['has_alt']:
                summary['images_missing_alt'].append({'file': res['path'], 'src': img['src']})
        # figures
        if res['figures'] > res['figcaptions']:
            summary['figures_missing_figcaptions'].append(res['path'])
        if res['under_construction']:
            summary['under_construction'].append(res['path'])

    # Output human-friendly report
    print('\nSite smoke-test report for:', SITE_DIR)
    print('Files scanned:', summary['files'])
    print('\nChecks (present / issues):')

    def show_list(name, lst):
        if not lst:
            print(f" - {name}: OK")
        else:
            print(f" - {name}: {len(lst)} issue(s)")
            for item in lst[:20]:
                print(f"    • {item}")

    show_list('Missing <!DOCTYPE html>', summary['missing_doctype'])
    show_list('<html lang="..."> missing', summary['missing_lang'])
    show_list('Missing viewport meta', summary['missing_viewport'])
    show_list('Missing <title>', summary['missing_title'])

    if not summary['images_missing_alt']:
        print(' - Images with missing alt: OK')
    else:
        print(f" - Images with missing alt: {len(summary['images_missing_alt'])}")
        for img in summary['images_missing_alt'][:50]:
            print(f"    • {img['file']} -> src={img['src']}")

    show_list('Figures missing figcaptions', summary['figures_missing_figcaptions'])
    show_list('\"Under Construction\" occurrences', summary['under_construction'])

    print('\nDetailed per-file breakdown (counts):')
    for r in all_results:
        print(f" - {r['path']}: doctype={'yes' if r['doctype'] else 'no'}, lang={'yes' if r['html_lang'] else 'no'}, viewport={'yes' if r['viewport'] else 'no'}, title={'yes' if r['title'] else 'no'}, imgs={len(r['imgs'])}, figs={r['figures']}, figcaps={r['figcaptions']}, under_construction={'yes' if r['under_construction'] else 'no'})")

    print('\nSummary:')
    issues = sum([len(summary['missing_doctype']), len(summary['missing_lang']), len(summary['missing_viewport']), len(summary['missing_title']), len(summary['images_missing_alt']), len(summary['figures_missing_figcaptions']), len(summary['under_construction'])])
    if issues == 0:
        print('No issues found by the smoke-check. Good job!')
    else:
        print(f'Total issues found (rough count): {issues}. See above for details.')

    return 0

if __name__ == '__main__':
    raise SystemExit(run_checks())
