"""Export the unchanged saved roster and title-matched revision records."""
import datetime as dt
import json
from pathlib import Path
import re
import sys
from collections import defaultdict
from bootstrap import load,normalize

def prepare():
    watch=load('author-watchlist.json',{})['authors'];homes=load('homepages.json',{})['authors']
    byname=defaultdict(list);papers=defaultdict(list);publications=defaultdict(dict)
    for person in load('author-universe.json',{})['authors']:
        for pub in person['publications']:publications[normalize(person['name'])][pub['doi']]=pub
    if sum(normalize(a['name'])=='menggao' for a in watch)==1:
        watch=[a for row in watch for a in ([row,{**row,'id':'workbook-menggao-uibe','homepage_url':'https://menggaosite.github.io/','identity_note':'UIBE; ORCID 0000-0003-0374-8607. Distinct from the UConn researcher.'}] if normalize(row['name'])=='menggao' else [row])]
    for home in homes:
        for key in set(home.get('name_keys',[])+[normalize(home['name'])]):byname[key].append(home)
    for paper in load('rr.json',{})['items']:
        if paper['journal'] not in {'JF','JFE','RFS','RF','JFQA','MS'} or paper['status'] not in {'R&R','Reject & Resubmit'}:continue
        for key in set(map(normalize,paper['authors']+[paper.get('source_author','')])):papers[key].append(paper)
    rows=[]
    for author in watch:
        keys=set(author.get('name_keys',[])+[normalize(author['name'])]);url=author.get('homepage_url','')
        hs=[h for k in keys for h in byname[k] if h.get('url','').rstrip('/')==url.rstrip('/')]
        attempted=max((h.get('last_attempted','') for h in hs),default='')
        readable=max((h.get('last_scanned','') for h in hs),default='')
        status='Website unresolved; R&R not checked' if not url else ('Source read '+readable if readable else 'Readable research source not confirmed')
        if normalize(author['name'])=='menggao' and 'sites.google.com/view/menggao/' in url:
            readable='2026-10-26';status='Primary research page read 2026-10-26; no explicit R&R disclosed on reviewed page'
        if attempted and attempted>readable:status='Source unavailable '+attempted+'; last read '+(readable or 'not recorded')
        selected={p['id']:p for key in keys for p in papers[key]}
        pubs={doi:pub for k in keys for doi,pub in publications[k].items()}
        if normalize(author['name'])=='menggao':
            uibe='menggaosite.github.io' in url
            own={'10.1017/s0022109023000492'} if uibe else {'10.1017/s0022109026103044','10.1093/rfs/hhae038'}
            pubs={doi:p for doi,p in pubs.items() if doi in own}
            selected={i:p for i,p in selected.items() if ('menggaosite.github.io' in p.get('evidence_url','') if uibe else 'sites.google.com/view/menggao/' in p.get('evidence_url',''))}
        ps=[]
        for p in sorted(selected.values(),key=lambda p:p['title'].casefold()):
            ssrn=p.get('ssrn_url','')
            if not ssrn and 'ssrn.com/' in p.get('paper_url',''):ssrn=p['paper_url']
            ps.append({'title':p['title'],'journal':p['journal'],'status':p['status'],'ssrn_url':ssrn,'last_verified':p.get('last_verified','')})
        elig=next((h['eligibility'] for h in hs if h.get('eligibility')),None)
        if normalize(author['name'])=='menggao' and pubs and not elig:elig=next(iter(pubs.values()))
        rows.append({'name':author['name'],'homepage_url':url,'papers':ps,'website_status':'Linked personal / individual institution page' if url else 'Unresolved',
            'rr_check':status,'last_read':readable,'publication_doi':('https://doi.org/'+elig['doi']) if elig else '',
            'publication_journals':', '.join(sorted({p['journal'] for p in pubs.values()})), 'publication_count':len(pubs) if pubs else None,
            'identity_note':author.get('identity_note') or ('UConn; ORCID 0000-0001-6805-2323. Distinct from the UIBE researcher.' if normalize(author['name'])=='menggao' else 'Saved name aliases; provisional identities and profile-only matches require care.')})
    meta=load('meta.json',{})
    return {'as_of':dt.date.today().isoformat(),'publication_window':meta['publication_window_start']+' to '+meta['publication_window_end'],'scope':'Fixed 10,762-name roster. Finance five, Management Science and retained conference authors. The two confirmed Meng Gao researchers occupy separate worksheet rows.',
        'rows':rows,'linked':sum(bool(r['homepage_url']) for r in rows),'paper_associations':sum(len(r['papers']) for r in rows)}

if __name__=='__main__':
    result=prepare();Path(sys.argv[1]).write_text(json.dumps(result,ensure_ascii=False))
    print(json.dumps({'authors':len(result['rows']),'linked':result['linked'],'paper_associations':result['paper_associations']}))
