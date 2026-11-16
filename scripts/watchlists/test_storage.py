import tempfile
import gzip
import json
import unittest
from pathlib import Path
from unittest.mock import patch
import bootstrap

class StorageTests(unittest.TestCase):
    def test_windows_shard_index_is_readable_on_linux(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(bootstrap,'DATA',Path(folder)):
            obj={'authors':[{'name':'Identity retained'}]}
            bootstrap.save('homepages.json',obj)
            p=Path(folder)/'homepages.json';index=json.loads(p.read_text())
            index['record_shards']=[s.replace('/','\\') for s in index['record_shards']]
            p.write_text(json.dumps(index))
            self.assertEqual(bootstrap.load('homepages.json',{}),obj)
            bootstrap.save('homepages.json',obj)
            self.assertTrue(all('\\' not in s for s in json.loads(p.read_text())['record_shards']))

    def test_evidence_indexes_roundtrip_and_remove_obsolete_shards(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(bootstrap,'DATA',Path(folder)):
            for name,key in [('homepages.json','authors'),('run-report.json','sources'),('author-watchlist.json','authors')]:
                obj={key:[{'url':f'https://example.org/{i}','last_verified':'2026-11-02'} for i in range(2100)],'complete':False}
                legacy=Path(folder)/(name+'.gz')
                legacy.write_bytes(gzip.compress(json.dumps(obj).encode()))
                self.assertEqual(bootstrap.load(name,{}),obj)
                bootstrap.save(name,obj)
                self.assertFalse(legacy.exists())
                self.assertEqual(bootstrap.load(name,{}),obj)
                self.assertEqual(len(list((Path(folder)/Path(name).stem).glob('*.gz'))),3)
                obj[key]=obj[key][:1];bootstrap.save(name,obj)
                self.assertEqual(bootstrap.load(name,{}),obj)
                self.assertEqual(len(list((Path(folder)/Path(name).stem).glob('*.gz'))),1)

    def test_missing_shard_is_not_empty_success(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(bootstrap,'DATA',Path(folder)):
            bootstrap.save('homepages.json',{'authors':[{'name':'Person'}]})
            next((Path(folder)/'homepages').glob('*.gz')).unlink()
            with self.assertRaises(FileNotFoundError):bootstrap.load('homepages.json',{})
