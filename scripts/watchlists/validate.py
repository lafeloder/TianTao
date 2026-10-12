#!/usr/bin/env python3
"""Fail publication on malformed data, duplicate identities or missing evidence."""
import datetime as dt
from bootstrap import load

def main():
    rr=load('rr.json',{})['items'];jobs=load('postdocs.json',{})['items']
    schools=load('schools.json',{})['schools'];meta=load('meta.json',{})
    assert len(schools)==50 and len({s['id'] for s in schools})==50
    assert all(1<=s['rank']<=50 for s in schools)
    assert len({p['id'] for p in rr})==len(rr)
    assert len({j['id'] for j in jobs})==len(jobs)
    assert meta['approved_homepages']<=meta['author_name_groups']
    for p in rr:
        assert p['title'] and p['authors'] and p['journal'] in ['JF','JFE','RFS','RF','JFQA']
        assert p['evidence_url'].startswith('https://')
        dt.date.fromisoformat(p['last_verified'])
        if p['status']=='R&R':assert p['eligibility'] and p['eligibility']['doi']
    for j in jobs:
        assert j['source_url'].startswith('https://')
        if j['deadline']:dt.date.fromisoformat(j['deadline'])
        if j['status']=='open':assert j['deadline'] and j['source_type']=='Official website'
        assert j['scope']!='FT Europe top 50' or j['rank'] is not None
    print(f'Validated {len(rr)} papers, {len(jobs)} vacancies and {len(schools)} schools')

if __name__=='__main__':main()
