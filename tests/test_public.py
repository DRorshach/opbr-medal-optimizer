import unittest,json,sys,types,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
pkg=types.ModuleType('opbr');pkg.__path__=[str(ROOT)];sys.modules['opbr']=pkg
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file)
    obj=importlib.util.module_from_spec(spec);sys.modules[name]=obj;spec.loader.exec_module(obj)
    return obj
storage=module('opbr.storage','storage-browser.py');storage.ROOT=ROOT
engine=module('opbr.engine','engine.py')

class PublicCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cat=engine.Catalog()
    def test_all_character_builds_match_published_engine(self):
        paths=list((ROOT/'data/builds').glob('*.json'))
        self.assertEqual(len(paths),len(self.cat.tables['charas'])*2)
        for path in paths:
            d=json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(len(d['sets']),3)
            for r in d['sets']:
                actual=engine.evaluate(self.cat,r['ids'],r['config'])
                self.assertAlmostEqual(actual['score'],r['score'],places=5,msg=path.name)
    def test_public_bootstrap_has_no_personal_state(self):
        d=json.loads((ROOT/'data/bootstrap.json').read_text(encoding='utf-8'))
        self.assertNotIn('state',d)
        self.assertEqual(len(d['medals']),706)
        for m in d['medals']:
            if m['image']:self.assertTrue((ROOT/m['image'].lstrip('/')).is_file())
    def test_no_database_or_machine_paths(self):
        self.assertFalse(list(ROOT.rglob('*.sqlite3')))
        for p in (ROOT/'data').rglob('*.json'):
            s=p.read_text(encoding='utf-8')
            self.assertNotIn('C:\\\\Users\\\\',s,p.name)
            self.assertNotIn('G:\\\\SteamLibrary',s,p.name)

if __name__=='__main__':unittest.main()
