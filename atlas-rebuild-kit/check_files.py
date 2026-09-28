"""Confirms every kit file arrived intact. Run from the kit folder: python3 check_files.py"""
import hashlib, pathlib, sys
here = pathlib.Path(__file__).resolve().parent
bad = 0
for line in (here / 'MANIFEST.txt').read_text().splitlines():
    digest, name = line.split('  ', 1)
    p = here / name
    if not p.exists(): print('MISSING  ', name); bad += 1
    elif hashlib.sha256(p.read_bytes()).hexdigest() != digest: print('CORRUPTED', name); bad += 1
print('all files OK' if not bad else f'{bad} problem(s) - re-copy those files'); sys.exit(1 if bad else 0)
