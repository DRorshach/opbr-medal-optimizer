from pathlib import Path
import json
ROOT=Path('/app')
def load_tables():
    d=json.loads((ROOT/'data/tables.json').read_text())
    return {k:{int(i):v for i,v in rows.items()} for k,rows in d.items()},[]
