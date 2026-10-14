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
        assert p['title'] and p['authors'] and p['journal']
        assert p['evidence_url'].startswith('https://')
        if p['last_verified']:dt.date.fromisoformat(p['last_verified'])
        else:assert p.get('reference_url') and p.get('verification_status')=='reference_only'
        if p['eligibility']:assert p['eligibility']['doi']
        if p.get('eligibility_status')=='conference_verified':
            proof=p.get('conference_eligibility',{})
            assert proof.get('conference') and proof.get('paper_title')
            assert proof.get('program_url','').startswith('https://')
            assert proof.get('year') in [2024,2025,2026]
    for j in jobs:
        assert j['source_url'].startswith('https://')
        if j['deadline']:dt.date.fromisoformat(j['deadline'])
        if j['status']=='open':assert j['last_verified'] and j.get('verification')
        assert j['scope']!='FT Europe top 50' or j['rank'] is not None
    for kind,items in [('papers',rr),('jobs',jobs)]:
        ids={i for row in items for i in row.get('reference_ids',[])}
        for source in meta.get('benchmark_sources',{}).get(kind,[]):
            assert source['matched']==source['in_scope'] and source['missing']==0, 'Reference coverage regressed'
        benchmark=load('coverage-manifest.json',{}).get(kind,{})
        for name,expected in benchmark.items():
            assert set(expected)<=ids, 'Missing reference IDs: '+name
    print(f'Validated {len(rr)} papers, {len(jobs)} vacancies and {len(schools)} schools')

if __name__=='__main__':main()
