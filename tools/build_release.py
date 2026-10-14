"""Build distributable ZIPs with correct macOS permissions; standard library only."""
import argparse
import ast
import base64
import hashlib
import json
from pathlib import Path
import re
import zipfile
import zlib

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
        for name in ('Titan Titles Studio.py', 'titan_update.py', 'titan_locale.py', 'titan_sfx.py'):
            if (ROOT/folder/name).read_bytes() != (ROOT/'src'/name).read_bytes():
                raise ValueError('Package copies differ: ' + folder + '/' + name)
    files = {'Titan Titles Studio.py': code, 'titan_update.py': (ROOT/'src/titan_update.py').read_bytes()}
    for name in ('titan_locale.py','titan_sfx.py'):
        files[name]=(ROOT/'src'/name).read_bytes()
        ast.parse(files[name].decode('utf-8'))
    for folder in ('icons','sfx'):
        for path in sorted((ROOT/'src'/folder).iterdir()):
            if path.is_file():files[folder+'/' + path.name] = path.read_bytes()
    # v3.2.x accepts only its original filenames. Embed new resources in the
    # updater for a compatible first upgrade; v3.3 expands them transactionally.
    resources={n:{'sha256':hashlib.sha256(content).hexdigest(),'data':base64.b64encode(content).decode()}
               for n,content in files.items() if n in ('titan_locale.py','titan_sfx.py') or n.startswith('sfx/')}
    packed=base64.b64encode(zlib.compress(json.dumps(resources,separators=(',',':')).encode(),9)).decode()
    bootstrap='''
def prepare_resources(directory, main_path=None):
    source=Path(__file__)
    updater=source.read_bytes()
    data=read_resource_bundle(updater)
    directory=Path(directory).resolve()
    legacy_root = directory.parent if directory.parent.name == 'Edit' and directory.parent.parent.name == 'Scripts' else directory if directory.name == 'Edit' and directory.parent.name == 'Scripts' else None
    target=legacy_root.parent.parent/'TitanTitlesStudio' if legacy_root else directory
    target.mkdir(parents=True,exist_ok=True)
    for name,content in data.items():
        path=target/name
        if path.is_symlink():raise ValueError('Recurso redirecionado.')
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists() or path.read_bytes()!=content:path.write_bytes(content)
    if legacy_root:
        backup_parent=legacy_root.parent.parent/'TitanTitlesStudio-backups'
        backup=backup_parent/('migration-'+str(time.time_ns()))
        backup.mkdir(parents=True)
        (target/'titan_update.py').write_bytes(updater)
        for name in _TITAN_ICONS:
            old=directory/name
            if old.is_file():
                destination=target/name
                destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes(old.read_bytes())
        script=Path(main_path) if main_path else legacy_root/'Titan Titles Studio.py'
        if script.parent.resolve()==legacy_root and script.is_file():
            canonical=legacy_root/'Titan Studio.py'
            if canonical.exists():shutil.copy2(canonical,backup/'before-Titan Studio.py')
            canonical.write_bytes(script.read_bytes())
        retire_legacy(legacy_root,backup)
    return str(target)
'''
    update_files={n:content for n,content in files.items() if n not in resources}
    update_files['titan_update.py']=(files['titan_update.py'].decode()+'\n_TITAN_BUNDLE = '+repr(packed)+'\n_TITAN_ICONS = '+repr([n for n in files if n.startswith('icons/')])+'\n'+bootstrap).encode()
    manifest = {'product': 'Titan Titles Studio', 'version': 'v' + version,
                'files': {n: hashlib.sha256(b).hexdigest() for n,b in update_files.items()}}
    archive(destination/'Titan-Titles-Studio-Update.zip', {**update_files, 'manifest.json': json.dumps(manifest, indent=2).encode()})
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
