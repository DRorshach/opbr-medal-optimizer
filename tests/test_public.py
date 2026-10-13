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
    def test_character_selection_excludes_special_records(self):
        d=json.loads((ROOT/'data/bootstrap.json').read_text(encoding='utf-8'))
        ids={c['id'] for c in d['characters']}
        expected={i for i,c in self.cat.tables['charas'].items() if c.get('chara_type',0)==0}
        self.assertEqual(ids,expected)
        self.assertEqual(len(ids),362)
        self.assertEqual([c['id'] for c in d['characters'] if c['name']=='King'],[400000696])
        self.assertGreater(len([c for c in d['characters'] if c['name']=='Monkey D. Luffy']),1)
        self.assertIn(400000827,ids)
        for cid in ids:
            c=self.cat.tables['charas'][cid]
            for n in (1,2):
                self.assertNotIn(self.cat.tables['chara_skill'].get(c.get(f'skill{n}_id'),{}).get('name'),(None,'???'))
    def test_sustain_is_separate_from_hp(self):
        hp=engine.config({'preset':'hp','role':'defender'})['weights']
        self.assertEqual(hp,engine.config({'preset':'hp'})['weights'])
        self.assertEqual(hp['defense'],0)
        sustain=engine.config({'preset':'sustentacao','role':'defender'})['weights']
        self.assertGreater(sustain['defense'],0)
        self.assertGreater(sustain['skill1'],0)
        bootstrap=json.loads((ROOT/'data/bootstrap.json').read_text(encoding='utf-8'))
        self.assertEqual(bootstrap['role_presets']['defender']['sustentacao'],engine.ROLE_PRESETS['defender']['sustentacao'])
    @classmethod
    def setUpClass(cls):cls.cat=engine.Catalog()
    def test_all_character_builds_match_published_engine(self):
        paths=list((ROOT/'data/builds').glob('*.json'))+list((ROOT/'data/builds-normal').glob('*.json'))
        self.assertEqual(len(paths),len(self.cat.tables['charas'])*4)
        for path in paths:
            d=json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(len(d['sets']),5)
            for r in d['sets']:
                if path.parent.name=='builds-normal':
                    self.assertEqual(d['pool'],'normal')
                    self.assertTrue(all(self.cat.kind(self.cat.medals[i])=='normal' for i in r['ids']))
                actual=engine.evaluate(self.cat,r['ids'],r['config'])
                self.assertAlmostEqual(actual['score'],r['score'],places=5,msg=path.name)
    def test_public_bootstrap_has_no_personal_state(self):
        d=json.loads((ROOT/'data/bootstrap.json').read_text(encoding='utf-8'))
        self.assertNotIn('state',d)
        self.assertEqual(len(d['medals']),706)
        for m in d['medals']:
            if m['image']:self.assertTrue((ROOT/m['image'].lstrip('/')).is_file())
    def test_scoring_v2_categories_and_general_critical(self):
        self.assertEqual(engine.MODEL,'utility-v2')
        for name,weights in engine.PRESETS.items():
            if name!='critico':self.assertEqual(weights.get('critical',0),0,name)
        for typ,dimension in [(8,'dodge'),(9,'survival'),(200,'hp'),(201,'attack_stat'),(202,'defense_stat'),(204,'speed')]:
            self.assertEqual(engine.RULES[typ][0],dimension)
        dodge=engine.normalize({'affect_type':8,'affect_param1':1.13,'detail':'Boost the cooldown reduction speed of dodge by 13%.'},1,'ability',{})
        self.assertEqual(engine.score_effects([dodge],engine.config({'preset':'hp'}))[0],0)
    def test_no_database_or_machine_paths(self):
        self.assertFalse(list(ROOT.rglob('*.sqlite3')))
        for p in (ROOT/'data').rglob('*.json'):
            s=p.read_text(encoding='utf-8')
            self.assertNotIn('C:\\\\Users\\\\',s,p.name)
            self.assertNotIn('G:\\\\SteamLibrary',s,p.name)

if __name__=='__main__':unittest.main()
