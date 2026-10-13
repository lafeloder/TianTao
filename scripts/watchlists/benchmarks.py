#!/usr/bin/env python3
"""Full public reference pagination with cached, labelled fallback snapshots.

Reference reports are never presented as independently verified author decisions.
Only factual metadata is retained; long job descriptions are discarded.
"""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import re
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
from bootstrap import ROOT, DATA, load, save, normalize
from public_benchmarks import screen_openpostdoc, screen_ejm, parse_ejm_html

TODAY=dt.date.today().isoformat()
RR_URL='https://chenyangfinance.github.io/paper-status/'
OP_URL='https://www.openpostdoc.org/board'
EJM_URL='https://econjobmarket.org/'
TRACKED_JOURNALS={'JF','JFE','RFS','RF','JFQA','MS'}
EUROPE={'Austria','Belgium','Bulgaria','Croatia','Cyprus','Czech Republic','Czechia','Denmark','Estonia','Finland','France','Germany','Greece','Hungary','Iceland','Ireland','Italy','Latvia','Lithuania','Luxembourg','Malta','Netherlands','Norway','Poland','Portugal','Romania','Slovakia','Slovenia','Spain','Sweden','Switzerland','United Kingdom','UK','Turkey','Türkiye'}

def download(url):
    req=urllib.request.Request(url,headers={'User-Agent':'TianTao-ResearchWatch/2.0 (public academic references)'})
    with urllib.request.urlopen(req,timeout=35) as r:return r.read().decode('utf8','replace')

def journal_code(text):
    aliases=[('Journal of Financial and Quantitative Analysis','JFQA'),('Journal of Finances and Quantitative Analysis','JFQA'),('Journal of Financial Economics','JFE'),('Review of Financial Studies','RFS'),('Review of Finance','RF'),('Journal of Finance','JF'),('Review of Economic Studies','ReStud'),('Quarterly Journal of Economics','QJE'),('Journal of Political Economy: Microeconomics','JPE Micro'),('Journal of Political Economy','JPE'),('Management Science','MS'),('Econometrica','ECTA'),('Journal of Accounting Research','JAR'),('Journal of the European Economic Association','JEEA')]
    if text in TRACKED_JOURNALS:return text
    for label,code in aliases:
        if label.lower() in (text or '').lower():return code
    return text or 'Undisclosed'

def parse_rr(html):
    match=re.search(r'const\s+data\s*=\s*(\[.*?\]);\s*\n?\s*const\s+esc',html,re.S)
    if not match:raise ValueError('Paper reference format changed')
    rows=json.loads(match.group(1))
    stamp=re.search(r'Updated\s+(\d{4}-\d{2}-\d{2})',html)
    return {'checked_on':TODAY,'source_updated':stamp.group(1) if stamp else '',
            'rows':[{k:r.get(k) for k in ['scholar','title','coauthors','journal','status','url']} for r in rows]}

def rr_key(row):
    return 'chenyang:'+hashlib.sha256((normalize(row['title'])+'|'+normalize(row['scholar'])).encode()).hexdigest()[:16]

def parse_openpostdoc(html):
    chunks=[]
    for x in re.findall(r'self\.__next_f\.push\((.*?)\)</script>',html):
        block=json.loads(x)
        if isinstance(block,list) and len(block)>1 and isinstance(block[1],str):chunks.append(block[1])
    stream=''.join(chunks);marker='"positions":';index=stream.find(marker)
    if index<0:raise ValueError('OpenPostdoc public page format changed')
    remaining=stream[index+len(marker):].lstrip()
    positions,end=json.JSONDecoder().raw_decode(remaining)
    tail=remaining[end:]
    metadata={k:int(v) for k,v in re.findall(r'"(total|otherCount|page|pageCount|pageSize)":\s*([0-9]+)',tail)}
    return positions,metadata

def op_in_scope(row):
    return screen_openpostdoc(row)[0]

def fetch_openpostdoc():
    all_rows=[];reported=0;pages=0
    for tab in ['', '&tab=expired']:
        first,meta=parse_openpostdoc(download(OP_URL+'?size=100'+tab))
        all_rows.extend(first);reported+=meta['total'];pages+=meta['pageCount']
        urls=[OP_URL+'?size=100'+tab+'&page='+str(p) for p in range(2,meta['pageCount']+1)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for html in pool.map(download,urls):all_rows.extend(parse_openpostdoc(html)[0])
    unique={r['id']:r for r in all_rows}
    if len(unique)<reported:raise ValueError('Incomplete or shifting OpenPostdoc pagination; retain complete cached snapshot')
    factual=['id','title','institutionName','country','city','region','primaryField','deadlineDate','startDate','applyUrl','sourceUrl','statusKind','scrapedAt']
    return {'checked_on':TODAY,'total_scanned':len(unique),'pages':pages,
            'note':'All active and archived pages across all fields were scanned. Only European economics, finance and explicitly related postdoctoral records are included; mechanically focused jobs mislabeled Economics are excluded.',
            'rows':[{k:r.get(k) for k in factual} for r in unique.values() if op_in_scope(r)]}

def ejm_page(html,kind,page):
    decoded=parse_ejm_html(html,EJM_URL+kind+'?page='+str(page))
    rows=[]
    labels=['Location of job','Degree required','Job start date','Job duration','Salary','Application deadline','Target date for applications','Current search status']
    for source in decoded['positions']:
        rows.append({'id':source['id'],'title':source['title'],'columns':source['headerColumns'],
          'facts':{k:source[k] for k in labels if k in source},'url':source['sourceUrl'],
          'listing_url':source['statusSourceUrl'],'links':source['links'],
          'deadline':source.get('deadline'),'recruitmentStatus':source.get('recruitmentStatus')})
    return rows,decoded['pageCount']

def ejm_in_scope(row):
    source={**row.get('facts',{}),'title':row['title'],
            'positionTypesAndFields':row.get('columns',['','',''])[2] if len(row.get('columns',[]))>2 else ''}
    return screen_ejm(source)[0]

def fetch_ejm():
    unique={};page_count=0
    for kind in ['statuses','positions']:
        first,total=ejm_page(download(EJM_URL+kind+'?page=1'),kind,1)
        if total>30:raise ValueError('Unexpected EJM pagination')
        for row in first:unique[row['id']]=row
        page_count+=total
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            htmls=list(pool.map(download,[EJM_URL+kind+'?page='+str(p) for p in range(2,total+1)]))
        for p,html in enumerate(htmls,2):
            for row in ejm_page(html,kind,p)[0]:
                # Status view carries recruiter status, so retain it when both exist.
                unique.setdefault(row['id'],row)
    return {'checked_on':TODAY,'total_scanned':len(unique),'pages':page_count,
            'note':'All public status and position pages were scanned. Public EJM omits some login-only/free advertisements.',
            'rows':[r for r in unique.values() if ejm_in_scope(r)]}

def normalize_paper(row,snapshot):
    code=journal_code(row.get('journal'));status=row.get('status') or 'needs recheck'
    return {'id':rr_key(row),'title':row['title'],'authors':[row['scholar']]+(row.get('coauthors') or []),
       'journal':code,'status':status,'evidence_url':row['url'],'primary_source_url':row['url'],'paper_url':'',
       'source_author':row['scholar'],'first_seen':TODAY,'last_verified':'','source_updated':'',
       'topics':[],'evidence_excerpt':status+', '+(row.get('journal') or 'target journal undisclosed'),
       'eligibility':None,'verification':'Reference-listed; primary status check pending',
       'verification_status':'reference_only','reference_url':RR_URL,'reference_date':snapshot.get('source_updated',''),
       'reference_checked_on':snapshot['checked_on'],'reference_ids':[rr_key(row)],
       'source_scope':'top5' if code in TRACKED_JOURNALS else 'extended','authors_note':'Names are listed as reported by the reference; author order is not asserted.'}

def job_from_op(row,snapshot):
    deadline=row.get('deadlineDate') or '';closed=row.get('statusKind')=='closed' or bool(deadline and deadline<TODAY)
    return {'id':'openpostdoc-'+row['id'],'title':row['title'],'institution':row.get('institutionName') or 'Institution unconfirmed',
      'country':row.get('country') or '', 'city':row.get('city') or '', 'rank':None,'scope':'Additional European institution',
      'topics':['General interest'],'fit':row.get('primaryField') or 'Economics / finance',
      'deadline':deadline,'status':'closed' if closed else 'needs official confirmation',
      'duration':'Not stated','start':row.get('startDate') or 'Not stated','salary':'Not stated',
      'source_url':OP_URL.replace('/board','/position/')+row['id'],'apply_url':row.get('applyUrl') or row.get('sourceUrl') or OP_URL,
      'source_type':'OpenPostdoc','last_verified':'','first_seen':TODAY,
      'verification':'Reference-listed; employer verification pending',
      'notes':'Dates and application status need confirmation on the employer posting.',
      'reference_ids':['openpostdoc:'+row['id']],
      'source_reports':[{'name':'OpenPostdoc','url':OP_URL.replace('/board','/position/')+row['id'],'checked_on':snapshot['checked_on'],'reported_status':row.get('statusKind','')}]}

def job_from_ejm(row,snapshot):
    cols=row['columns'];facts=row['facts'];head=cols[0] if cols else ''
    dates=re.findall(r'\b\d{1,2} [A-Za-z]{3} \d{4}\b',cols[3] if len(cols)>3 else '')
    deadline=row.get('deadline') or (dt.datetime.strptime(dates[-2],'%d %b %Y').date().isoformat() if len(dates)>=3 else '')
    closed_words=['Reviewing applications','Scheduling interviews','Arranging flyouts','Making offers','Position filled','Search cancelled','Search completed','Interviews completed','Not accepting applications']
    status='closed' if (deadline and deadline<TODAY) or any(word in head for word in closed_words) else 'open' if 'Accepting applications' in head else 'needs official confirmation'
    country=next((c for c in sorted(EUROPE,key=len,reverse=True) if re.search(r'\b'+re.escape(c)+r'\b',facts.get('Location of job',''),re.I)),'')
    return {'id':'ejm-'+row['id'],'title':row['title'],'institution':cols[1] if len(cols)>1 else 'Institution unconfirmed',
      'country':country,'city':'','rank':None,'scope':'Additional European institution','topics':['General interest'],
      'fit':cols[2] if len(cols)>2 else 'Economics','deadline':deadline,'status':status,'duration':facts.get('Job duration') or 'Not stated',
      'start':facts.get('Job start date') or 'Not stated','salary':facts.get('Salary') or 'Not stated',
      'source_url':row.get('listing_url') or row['url'],'apply_url':row['url'],'source_type':'Econ Job Market employer advert',
      'last_verified':snapshot['checked_on'],'first_seen':TODAY,'verification':'Employer-published EJM advertisement',
      'search_status':head.split('Flexible start date.')[-1].strip()[:120],
      'notes':'Recruiter search status is separate from whether new applications are accepted.',
      'reference_ids':['ejm:'+row['id']],
      'source_reports':[{'name':'Econ Job Market','url':row.get('listing_url') or row['url'],'checked_on':snapshot['checked_on']}]}

def merge(items,new_items,kind):
    # Two employer adverts can share a title, institution and deadline (Oxford
    # 188851 / 188853). Preserve them unless a provider ID or advert URL agrees.
    result=list(items)
    def same_advert(old,new):
        if old.get('id') and old.get('id')==new.get('id'):return True
        if set(old.get('reference_ids',[])) & set(new.get('reference_ids',[])):return True
        if kind=='papers':return normalize(old['title'])==normalize(new['title'])
        first=old.get('apply_url','');second=new.get('apply_url','')
        if not first or not second:return False
        def canonical(url):
            parsed=urllib.parse.urlsplit(url)
            return (parsed.netloc.lower(),parsed.path.rstrip('/'),tuple(sorted(urllib.parse.parse_qsl(parsed.query))))
        return canonical(first)==canonical(second) and bool(urllib.parse.urlsplit(first).path.strip('/'))
    for new in new_items:
        # Cross-source aliases already researched take precedence over title drift.
        old=next((r for r in result if same_advert(r,new)),None)
        if old:
            old['reference_ids']=sorted(set(old.get('reference_ids',[])+new.get('reference_ids',[])))
            if kind=='papers':
                for field in ['reference_url','reference_date','reference_checked_on']:old[field]=new.get(field,old.get(field,''))
                if old.get('journal')==new.get('journal') and new.get('source_scope')=='top5':
                    old['source_scope']='top5'
                    if old.get('scope')=='extended':old['scope']='top5'
            else:
                old['source_reports']=list({r['name']+'|'+r['url']:r for r in old.get('source_reports',[])+new.get('source_reports',[])}.values())
                if new['source_type']=='OpenPostdoc' and new.get('status')=='closed':old['status']='closed'
                if new['source_type']=='Econ Job Market employer advert':
                    old['deadline']=new['deadline'] or old.get('deadline','')
                    if new['status']!='needs official confirmation':old['status']=new['status']
                    old['last_verified']=new['last_verified']
            continue
        result.append(new)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--offline',action='store_true');args=parser.parse_args()
    sources=[('chenyang',RR_URL,lambda:parse_rr(download(RR_URL))),('openpostdoc',OP_URL,fetch_openpostdoc),('ejm',EJM_URL+'statuses?page=5',fetch_ejm)]
    papers=load('rr.json',{})['items'];jobs=load('postdocs.json',{})['items'];coverage={'papers':[],'jobs':[]}
    for name,url,fetcher in sources:
        cached=load('references/'+name+'.json',{})
        status='cached complete snapshot'
        if not args.offline:
            try:
                snapshot=fetcher()
                if not snapshot.get('rows'):raise ValueError('Empty source response')
                save('references/'+name+'.json',snapshot);cached=snapshot;status='complete public pagination'
            except Exception as e:
                print(name,'fallback to saved snapshot:',type(e).__name__,flush=True)
        if not cached.get('rows'):raise RuntimeError(name+' has no complete reference snapshot')
        if name=='chenyang':
            rows=[normalize_paper(r,cached) for r in cached['rows']];papers=merge(papers,rows,'papers');dest='papers'
        else:
            rows=[job_from_op(r,cached) if name=='openpostdoc' else job_from_ejm(r,cached) for r in cached['rows']]
            jobs=merge(jobs,rows,'jobs');dest='jobs'
        target=papers if dest=='papers' else jobs;ids={i for r in target for i in r.get('reference_ids',[])}
        expected={i for r in rows for i in r['reference_ids']};missing=expected-ids
        coverage[dest].append({'name':{'chenyang':'Chen Yang paper status','openpostdoc':'OpenPostdoc','ejm':'Econ Job Market'}[name],
          'url':url,'total_scanned':cached.get('total_scanned',len(cached['rows'])),'in_scope':len(expected),
          'matched':len(expected-missing),'missing':len(missing),'checked_on':cached['checked_on'],'status':status,
          'note':cached.get('note','')})
    for job in jobs:
        if job.get('deadline') and job['deadline']<TODAY:job['status']='closed'
    meta=load('meta.json',{});meta['benchmark_sources']=coverage
    meta['job_counts']={'total':len(jobs),'historical':sum(r['status']=='closed' for r in jobs),
      'active':sum(r['status']=='open' for r in jobs),'uncertain':sum(r['status'] not in ['closed','open'] for r in jobs)}
    save('rr.json',{'items':papers});save('postdocs.json',{'items':jobs});save('meta.json',meta)
    save('history/'+TODAY+'-rr.json',{'items':papers})
    save('history/'+TODAY+'-postdocs.json',{'items':jobs})
    for name in ['rr','postdocs','meta']:(ROOT/'public'/'watchlists'/(name+'.json')).write_text((DATA/(name+'.json')).read_text())
    print(json.dumps({'papers':len(papers),'jobs':len(jobs),'coverage':coverage},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
