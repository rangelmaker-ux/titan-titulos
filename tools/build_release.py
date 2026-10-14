"""Build distributable ZIPs with correct macOS permissions; standard library only."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def archive(path, entries):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as out:
        for name, content in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = ((0o100755 if name.endswith('.command') else 0o100644) << 16)
            info.compress_type = zipfile.ZIP_DEFLATED
            out.writestr(info, content)

def build(destination):
    destination.mkdir(parents=True, exist_ok=True)
    version = ROOT.joinpath('VERSION').read_text().strip()
    code = ROOT.joinpath('src/Titan Titles Studio.py').read_bytes()
    if ('APP_VERSION = "v' + version + '"').encode() not in code:
        raise ValueError('VERSION and APP_VERSION must match.')
    ast.parse(code.decode('utf-8'))
    for folder in ('1 - Windows/Arquivos', '2 - Mac'):
        for name in ('Titan Titles Studio.py', 'titan_update.py'):
            if (ROOT/folder/name).read_bytes() != (ROOT/'src'/name).read_bytes():
                raise ValueError('Package copies differ: ' + folder + '/' + name)
    files = {'Titan Titles Studio.py': code, 'titan_update.py': (ROOT/'src/titan_update.py').read_bytes()}
    for path in sorted((ROOT/'src/icons').iterdir()):
        if path.is_file():
            files['icons/' + path.name] = path.read_bytes()
    manifest = {'product': 'Titan Titles Studio', 'version': 'v' + version,
                'files': {n: hashlib.sha256(b).hexdigest() for n,b in files.items()}}
    archive(destination/'Titan-Titles-Studio-Update.zip', {**files, 'manifest.json': json.dumps(manifest, indent=2).encode()})
    for platform, folder in (('Windows','1 - Windows'), ('Mac','2 - Mac')):
        entries = {str(p.relative_to(ROOT/folder)).replace('\\','/'): p.read_bytes()
                   for p in (ROOT/folder).rglob('*') if p.is_file()}
        entries['LEIA-ME.md'] = (ROOT/'INSTALL.md').read_bytes()
        entries['Boas-vindas.html'] = (ROOT/'welcome.html').read_bytes()
        archive(destination/('Titan-Titles-Studio-' + platform + '.zip'), entries)
    sums = '\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name for p in sorted(destination.glob('*.zip')))
    (destination/'SHA256SUMS.txt').write_text(sums+'\n',encoding='utf-8')
    return version

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'dist')
    args=parser.parse_args()
    print('Built Titan Titles Studio v'+build(args.output))
