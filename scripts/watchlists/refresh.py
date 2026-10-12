#!/usr/bin/env python3
"""Evidence-first weekly refresh. Uncertain discoveries go to review-queue.json.

Existing entries are rechecked; failures retain their last verified dates.
Public HTML only. Optional ORCID/Brave discovery adds unapproved homepage
candidates, never silently approves a namesake or claims exhaustive coverage.
"""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request
import urllib.error
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from bootstrap import DATA, ROOT, load, save, normalize, get_json

UA = 'TianTao-ResearchWatch/1.0'
RR = re.compile(r'\b(?:revise[\s-]*and[\s-]*resubmit|R\s*&\s*R)\b', re.I)
REJECT = re.compile(r'\breject[\s-]*and[\s-]*resubmit\b', re.I)
JOURNAL_NAMES = {'JF': 'Journal of Finance', 'JFE': 'Journal of Financial Economics',
                 'RFS': 'Review of Financial Studies', 'RF': 'Review of Finance',
                 'JFQA': 'Journal of Financial and Quantitative Analysis'}
POSTDOC = re.compile(r'\bpost[\s-]?(?:doc(?:toral)?|doctorate)\b|research (?:fellow|associate)', re.I)
FIELDS = {'Banking': r'bank(?:ing|s)?|financial intermediation|credit|mortgage',
          'Corporate finance': r'corporate|firm financ|capital structure|merger|acquisition',
          'Labor': r'labou?r|employment|wage|inequality|migration',
          'General interest': r'economics|macroeconom|microeconom|econometric|political economy'}
MONTHS = {name.lower(): i for i, name in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}
MONTHS.update({k[:3]:v for k,v in list(MONTHS.items())})

def clean(text):
    return re.sub(r'\s+', ' ', text.replace('\xad','').replace('\u200b','')).strip()

def parse_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    for tag in soup(['script','style','nav','footer','header','noscript']):
        tag.decompose()
    return soup

def plain(body):
    return clean(parse_html(body).get_text(' ', strip=True))

def fetch(url, timeout=20):
    # A forbidden/failed robots request does not justify guessing permission.
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname:
        raise ValueError('Only public HTTPS sources are supported')
    robots_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, '/robots.txt', '', ''))
    try:
        with urllib.request.urlopen(urllib.request.Request(robots_url, headers={'User-Agent': UA}), timeout=10) as r:
            rules = RobotFileParser()
            rules.parse(r.read(500_000).decode('utf8', 'replace').splitlines())
            if not rules.can_fetch(UA, url):
                raise PermissionError('robots disallows this source')
    except urllib.error.HTTPError as e:
        if e.code not in (404,410):
            raise
    req = urllib.request.Request(url, headers={'User-Agent':UA, 'Accept':'text/html,application/pdf'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(8_000_001)
        if len(raw) > 8_000_000:
            raise ValueError('Source too large')
        if 'pdf' in r.headers.get('Content-Type','') or raw[:4] == b'%PDF':
            from pypdf import PdfReader
            return '\n'.join(p.extract_text() or '' for p in PdfReader(io.BytesIO(raw)).pages)
        return raw.decode(r.headers.get_content_charset() or 'utf8', 'replace')

def journal_in(text):
    matches=[]
    for key,name in JOURNAL_NAMES.items():
        match=re.search(r'\b(?:the\s+)?'+re.escape(name)+r'\b',text,re.I)
        if match:matches.append((match.start(),-len(name),key))
    return min(matches)[2] if matches else None

def rr_blocks(body, url):
    """Only a title and status within a bounded paper block become a candidate."""
    soup = parse_html(body)
    blocks = []
    for tag in soup.find_all(['li','article','h2','h3','h4']):
        if tag.name in ('li','article'):
            txt = clean(tag.get_text(' ',strip=True))
            if len(txt) > 1600:
                continue
        else:
            pieces = [tag.get_text(' ',strip=True)]
            for sib in tag.next_siblings:
                if getattr(sib, 'name', None) in ('h1','h2','h3','h4'):
                    break
                pieces.append(sib.get_text(' ',strip=True) if hasattr(sib,'get_text') else str(sib))
                if len(' '.join(pieces)) > 1600:
                    break
            txt = clean(' '.join(pieces))[:1600]
        if not RR.search(txt) or REJECT.search(txt):
            continue
        journal = journal_in(txt)
        if not journal:
            continue
        anchor = tag.find('a', href=True)
        heading = tag if tag.name.startswith('h') else tag.find(['h2','h3','h4'])
        title = clean((anchor or heading).get_text(' ',strip=True)) if (heading or anchor) else ''
        title = re.sub(r'^\d+[.)]?\s*','',title)
        if not title or not (12 <= len(title) <= 240) or RR.search(title) or title.lower() in ['working papers','publications','research papers']:
            continue
        link = urllib.parse.urljoin(url,anchor['href']) if anchor else ''
        if not link.startswith('https://'):
            link = ''
        blocks.append({'title':title,'journal':journal,'paper_url':link,'evidence_url':url,
                       'evidence_excerpt':RR.search(txt).group(0) + ', ' + JOURNAL_NAMES[journal]})
    return list({normalize(x['title'])+x['journal']:x for x in blocks}.values())

def find_paper_block(body, title, titles):
    # Bound the excerpt at the next known paper; journal/status on a neighbouring
    # paper must never be attributed to this one.
    text = plain(body)
    target = re.search(re.escape(clean(title)).replace(r'\ ',r'\s+'), text, re.I)
    if not target:
        return ''
    tail = text[target.end():target.end()+800]
    stop = len(tail)
    for other in titles:
        if normalize(other) == normalize(title):
            continue
        m = re.search(re.escape(clean(other)), tail, re.I)
        if m:
            stop = min(stop,m.start())
    return tail[:stop]

def extract_deadline(text):
    # Dates need an application-deadline label: never mistake start dates for one.
    label = re.search(r'(?:application deadline|closing date|deadline(?: for applications)?|apply (?:now )?(?:by|until)|applications? (?:must be (?:received|submitted)|can be submitted) (?:by|until))\s*:?\s*(.{0,100})', clean(text), re.I)
    if not label:
        return ''
    part = label.group(1)
    numeric = re.search(r'\b(\d{1,2})[./](\d{1,2})[./](20\d{2})\b',part)
    if numeric:
        d,m,y=map(int,numeric.groups())
        try: return dt.date(y,m,d).isoformat()
        except ValueError: return ''
    word = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s*,?\s*(20\d{2})\b',part)
    if word:
        d,m,y=word.groups()
        try: return dt.date(int(y),MONTHS[m.lower()],int(d)).isoformat()
        except (ValueError,KeyError): return ''
    word = re.search(r'\b([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(20\d{2})\b',part)
    if word:
        m,d,y=word.groups()
        try: return dt.date(int(y),MONTHS[m.lower()],int(d)).isoformat()
        except (ValueError,KeyError): return ''
    return ''

def job_status(job, text, today):
    if job.get('deadline') and job['deadline'] < today:
        return 'closed'
    # Explicit closure only, not general careers text mentioning closed vacancies.
    if re.search(r'(?:this (?:position|vacancy|call) (?:is|has been) (?:now )?closed|no longer accepting applications|position has been filled)',text,re.I):
        return 'closed'
    if not POSTDOC.search(text):
        return 'needs recheck'
    if job.get('source_type') == 'LinkedIn':
        return 'needs official confirmation'
    return 'open' if job.get('deadline') else 'deadline unknown'

def safe_get(url):
    try:
        return url, fetch(url), ''
    except Exception as e:
        return url, '', type(e).__name__

def discover_homepages(universe, already, limit, state):
    candidates=[]
    eligible=[a for a in universe if a.get('orcid') and a['orcid'] not in state.get('orcid_done',[])]
    done=state.setdefault('orcid_done',[])
    for author in eligible[:limit]:
        try:
            record=get_json('https://pub.orcid.org/v3.0/'+author['orcid']+'/researcher-urls')
            done.append(author['orcid'])
            for row in record.get('researcher-url',[]):
                url=row.get('url',{}).get('value','')
                if url.startswith('https://') and not re.search(r'(scholar.google|scopus|linkedin|twitter|x.com/|researchgate|ssrn)',url) and url not in already:
                    candidates.append({'kind':'homepage','name':author['name'],'url':url,'orcid':author['orcid'],
                                       'publication_doi':author['publications'][0]['doi'],'review':'Verify that this homepage belongs to the author of the indexed publication.'})
        except Exception:
            # Do not mark API failures done; retry on a later run.
            pass
    # Optional search accelerates discovery for authors without ORCID. No secret
    # is required to use the known-source crawler or Crossref bibliography.
    key=os.getenv('BRAVE_SEARCH_API_KEY')
    if key:
        name_done=state.setdefault('search_done',[])
        authors=[a for a in universe if normalize(a['name']) not in name_done]
        for a in authors[:min(limit,30)]:
            try:
                q=a['name']+' finance research personal website '+(' '.join(a['affiliations'])[:100])
                url='https://api.search.brave.com/res/v1/web/search?'+urllib.parse.urlencode({'q':q,'count':3})
                req=urllib.request.Request(url,headers={'X-Subscription-Token':key,'Accept':'application/json'})
                with urllib.request.urlopen(req,timeout=20) as r:
                    results=json.load(r).get('web',{}).get('results',[])
                name_done.append(normalize(a['name']))
                for hit in results:
                    if hit['url'].startswith('https://') and hit['url'] not in already:
                        candidates.append({'kind':'homepage','name':a['name'],'url':hit['url'],
                                           'publication_doi':a['publications'][0]['doi'],'review':'Publication-level identity approval required.'})
            except Exception:
                pass
    return candidates

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--as-of',default=dt.date.today().isoformat())
    parser.add_argument('--discover-limit',type=int,default=30)
    parser.add_argument('--skip-feeds',action='store_true')
    parser.add_argument('--skip-discovery',action='store_true')
    args=parser.parse_args();today=args.as_of
    corpus=load('corpus.json',{'works':[],'journals':{}})
    universe=load('author-universe.json',{'authors':[]})['authors']
    rr=load('rr.json',{'items':[]});jobs=load('postdocs.json',{'items':[]})
    homes=load('homepages.json',{'authors':[]})['authors'];schools=load('schools.json',{'schools':[]})
    state=load('discovery-state.json',{})
    queue=load('review-queue.json',{'items':[]})['items']
    urls={a['url'] for a in homes if a.get('approved')} | {j['source_url'] for j in jobs['items']}
    if not args.skip_feeds:
        urls|={s['career_url'] for s in schools['schools']}
    results={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for url,body,error in pool.map(safe_get,sorted(urls)):
            results[url]=(body,error)
    report={'attempted_on':today,'sources':[]}
    for url,(body,error) in results.items():
        report['sources'].append({'url':url,'result':'failed' if error else 'fetched','error':error})
    verified_names=set()
    for author in homes:
        matches=[a for a in universe if normalize(a['name'])==normalize(author['name'])]
        pubs=[p for a in matches for p in a['publications']]
        if not author.get('approved') or not pubs:
            continue
        author['eligibility']=min(pubs,key=lambda p:p['published'])
        body,error=results.get(author['url'],('','not attempted'))
        author['last_attempted']=today;author['scan_status']='failed' if error else 'scanned'
        if not error:
            author['last_scanned']=today;verified_names.add(normalize(author['name']))
            existing={normalize(p['title'])+p['journal'] for p in rr['items']}
            for candidate in rr_blocks(body,author['url']):
                if normalize(candidate['title'])+candidate['journal'] not in existing:
                    queue.append(dict(candidate,kind='paper',source_author=author['name'],discovered_on=today,
                                      review='Confirm title, authors, strict revise-and-resubmit wording and no newer publication/acceptance.'))
        titles=[p['title'] for p in rr['items'] if p['evidence_url']==author['url']]
        for paper in rr['items']:
            if paper['evidence_url']!=author['url']:
                continue
            if paper['status'] in ['Accepted','Published'] or paper['journal'] not in JOURNAL_NAMES:
                # Extended-journal reports and acceptance evidence are reconciled
                # by the reference/research layer, not the five-journal matcher.
                continue
            paper['eligibility']={**author['eligibility'],'author':author['name']}
            if error:
                paper['last_attempted']=today
                continue
            block=find_paper_block(body,paper['title'],titles)
            if RR.search(block) and journal_in(block)==paper['journal'] and not REJECT.search(block):
                paper['last_verified']=today;paper['status']='R&R'
                paper['evidence_excerpt']=RR.search(block).group(0)+', '+JOURNAL_NAMES[paper['journal']]
                # Resolve paper links from the exact title anchor, never guess URLs.
                soup=parse_html(body)
                for a in soup.find_all('a',href=True):
                    if normalize(a.get_text(' ',strip=True))==normalize(paper['title']):
                        link=urllib.parse.urljoin(author['url'],a['href'])
                        if link.startswith('https://'):paper['paper_url']=link
                        break
            else:
                paper['verification_status']='needs_recheck'
                paper['verification']='Previously reported status; latest primary parsing incomplete'
    for job in jobs['items']:
        if 'econjobmarket.org' in job['source_url'] or 'openpostdoc.org' in job['source_url']:
            # A listing-page date belongs to a specific card, never to all jobs.
            # These records are updated by the structured provider adapter.
            continue
        body,error=results.get(job['source_url'],('','not attempted'))
        job['last_attempted']=today
        if job.get('deadline') and job['deadline']<today:
            job['status']='closed'
        elif not error:
            text=plain(body)
            # The title must occur in the page to exclude redirected generic hubs.
            identity_text=re.sub(r'\b[fmdx](?:\s*/\s*[fmdx]){1,2}\b','',text,flags=re.I)
            if normalize(job['title']) not in normalize(identity_text):
                job['status']='needs recheck'
                continue
            deadline=extract_deadline(text)
            if deadline:job['deadline']=deadline
            job['status']=job_status(job,text,today);job['last_verified']=today
    for school in schools['schools']:
        if args.skip_feeds:
            continue
        body,error=results.get(school['career_url'],('','not attempted'))
        school['feed_status']='failed' if error else 'fetched (limited HTML scan)'
        school['last_attempted']=today
        if error:continue
        school['last_fetched']=today
        for a in parse_html(body).find_all('a',href=True):
            title=clean(a.get_text(' ',strip=True))
            if POSTDOC.search(title):
                url=urllib.parse.urljoin(school['career_url'],a['href'])
                if url.startswith('https://') and url not in {j['source_url'] for j in jobs['items']}:
                    queue.append({'kind':'vacancy','title':title,'institution':school['name'],
                                  'url':url,'rank':school['rank'],'discovered_on':today,
                                  'review':'Verify field, employer, Europe location, deadline, postdoctoral qualification and application status.'})
    if not args.skip_discovery:
        queue.extend(discover_homepages(universe,{a['url'] for a in homes},args.discover_limit,state))
    # Keep stable historical identities; retain failed-source evidence dates.
    queue=list({x['kind']+'|'+x.get('url',x.get('evidence_url',''))+'|'+normalize(x.get('title',x.get('name',''))):x for x in queue}.values())
    save('rr.json',rr);save('postdocs.json',jobs);save('homepages.json',{'authors':homes})
    save('schools.json',schools);save('discovery-state.json',state)
    save('review-queue.json',{'updated_on':today,'items':queue});save('run-report.json',report)
    names={normalize(a['name']) for a in universe}
    meta={**load('meta.json',{}),'last_run':today,'publication_window_start':corpus.get('window_start',''),
          'publication_window_end':corpus.get('window_end',''),'articles':len(corpus['works']),
          'author_name_groups':len(names),'author_identity_records':len(universe),
          'approved_homepages':sum(bool(a.get('approved') and a.get('eligibility')) for a in homes),
          'homepages_scanned_this_run':len(verified_names),'journals':corpus['journals'],
          'schools':len(schools['schools']),
          'feeds_fetched':sum(s['feed_status'].startswith('fetched') for s in schools['schools']),
          'review_queue':len(queue),'schedule':'Weekly on Mondays (GitHub Actions; activation requires repository deployment)',
          'coverage_note':'Homepage coverage is partial. Name/affiliation identities are provisional. A fetched career feed is not an exhaustive vacancy search.',
          'linkedin_note':'Public LinkedIn evidence only. Automated LinkedIn crawling may be blocked; no signed-in or complete LinkedIn coverage is claimed.'}
    save('meta.json',meta)
    public=ROOT/'public'/'watchlists';public.mkdir(parents=True,exist_ok=True)
    for name in ['rr','postdocs','meta','schools']:
        (public/(name+'.json')).write_text((DATA/(name+'.json')).read_text())
    for name in ['rr','postdocs']:
        save('history/'+today+'-'+name+'.json',load(name+'.json',{}))
    print(json.dumps({k:meta[k] for k in ['articles','author_name_groups','approved_homepages','homepages_scanned_this_run','feeds_fetched','review_queue']}))

if __name__=='__main__':main()
