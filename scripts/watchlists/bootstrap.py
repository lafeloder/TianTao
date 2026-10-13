#!/usr/bin/env python3
"""Build the rolling five-year author universe from public Crossref metadata.

No publisher full text is downloaded. Dates use first publication when present.
ORCIDs are identity keys; name-only records remain provisional identities.
"""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import gzip
import json
import os
from pathlib import Path
import re
import time
import unicodedata
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'content' / 'watchlists'
JOURNALS = {'JF': '0022-1082', 'JFE': '0304-405X', 'RFS': '0893-9454',
            'RF': '1572-3097', 'JFQA': '0022-1090', 'MS': '0025-1909'}

def normalize(text):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower())

def load(name, default):
    p = DATA / name
    if not p.exists() and p.with_suffix(p.suffix+'.gz').exists():
        return json.loads(gzip.decompress(p.with_suffix(p.suffix+'.gz').read_bytes()))
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default

def save(name, obj):
    DATA.mkdir(parents=True, exist_ok=True)
    p = DATA / name
    p.parent.mkdir(parents=True, exist_ok=True)
    if name in ['corpus.json','author-universe.json','ms-author-ledger.json']:
        encoded=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode()
        target=p.with_suffix(p.suffix+'.gz')
        temp=target.with_suffix('.tmp')
        temp.write_bytes(gzip.compress(encoded,mtime=0))
        temp.replace(target)
        if p.exists():p.unlink()
        return
    temp = p.with_suffix('.tmp')
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(p)

def get_json(url):
    headers = {'User-Agent': 'TianTao-ResearchWatch/1.0 (public academic metadata)', 'Accept': 'application/json'}
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
                return json.load(response)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)

def publication_date(item):
    dates = []
    for field in ['published', 'published-online', 'published-print']:
        parts = item.get(field, {}).get('date-parts', [[]])[0]
        if parts:
            try:
                dates.append(dt.date(*(parts + [1, 1])[:3]))
            except ValueError:
                pass
    return min(dates) if dates else None

def journal_records(journal, issn, start, end):
    cursor, records, seen = '*', [], set()
    while cursor:
        params = {'filter': f'from-pub-date:{start},until-pub-date:{end},type:journal-article',
                  'rows': 1000, 'cursor': cursor,
                  'select': 'DOI,title,author,published,published-online,published-print,type,container-title'}
        if os.getenv('CROSSREF_MAILTO'):
            params['mailto'] = os.environ['CROSSREF_MAILTO']
        result = get_json('https://api.crossref.org/journals/' + issn + '/works?' + urllib.parse.urlencode(params))['message']
        items = result.get('items', [])
        fresh = [x for x in items if x.get('DOI') not in seen]
        if not fresh:
            break
        for item in fresh:
            seen.add(item.get('DOI'))
            title = ' '.join(item.get('title', []))
            date = publication_date(item)
            if not title or not item.get('author') or not date or not (start <= date <= end):
                continue
            if re.match(r'^(erratum|corrigendum|correction|editorial|index|report of the editor|masthead|front matter|back matter|contents)\b', title, re.I):
                continue
            records.append({'doi': item['DOI'].lower(), 'journal': journal, 'title': title,
                            'published': date.isoformat(), 'authors': item['author']})
        cursor = result.get('next-cursor')
        if len(items) < 1000:
            break
    return journal, records

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--as-of', default=dt.date.today().isoformat())
    args = parser.parse_args()
    end = dt.date.fromisoformat(args.as_of)
    start = end.replace(year=end.year-5, day=min(end.day, 28)) if end.month == 2 else end.replace(year=end.year-5)
    previous = load('corpus.json', {'works': [], 'journals': {}})
    works, report = [], {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(journal_records, j, issn, start, end): j for j, issn in JOURNALS.items()}
        for future in concurrent.futures.as_completed(futures):
            journal = futures[future]
            try:
                _, entries = future.result()
                works.extend(entries)
                report[journal] = {'status': 'complete', 'articles': len(entries), 'checked_on': end.isoformat()}
                print(journal, len(entries), flush=True)
            except Exception as e:
                retained = [w for w in previous.get('works', []) if w['journal'] == journal and start.isoformat() <= w['published'] <= end.isoformat()]
                works.extend(retained)
                report[journal] = {'status': 'failed', 'articles': len(retained), 'error': type(e).__name__,
                                   'checked_on': previous.get('journals', {}).get(journal, {}).get('checked_on')}
                print(journal, 'failed; retained', len(retained), flush=True)
    # Fail visibly if no live journal request succeeded; never overwrite a useful corpus with an empty one.
    if all(r['status'] == 'failed' for r in report.values()):
        raise SystemExit('All Crossref journal requests failed')
    works.sort(key=lambda x: (x['journal'], x['doi']))
    author_map = {}
    for work in works:
        for a in work['authors']:
            name = ' '.join([a.get('given', ''), a.get('family', '')]).strip()
            if not name:
                continue
            orcid = a.get('ORCID', '').rstrip('/').split('/')[-1]
            affiliations = sorted(x.get('name', '') for x in a.get('affiliation', []) if x.get('name'))
            identity = orcid or normalize(name) + '|' + '|'.join(map(normalize, affiliations))
            key = hashlib.sha256(identity.encode()).hexdigest()[:16]
            entry = author_map.setdefault(key, {'id': key, 'name': name, 'orcid': orcid,
                'identity_status': 'ORCID' if orcid else 'provisional name/affiliation',
                'affiliations': affiliations, 'publications': []})
            entry['publications'].append({k: work[k] for k in ['doi', 'journal', 'title', 'published']})
    save('corpus.json', {'window_start': start.isoformat(), 'window_end': end.isoformat(),
                        'retrieved_on': end.isoformat(), 'journals': report, 'works': works})
    save('author-universe.json', {'window_start': start.isoformat(), 'window_end': end.isoformat(),
          'note': 'Name-only identities may be duplicates or namesakes; homepage approval requires publication-level identity verification.',
          'authors': sorted(author_map.values(), key=lambda a: a['name'])})
    print('Articles:', len(works), 'Provisional author identities:', len(author_map))

if __name__ == '__main__':
    main()
