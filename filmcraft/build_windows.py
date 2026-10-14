"""Freeze the Windows port with no Python dependency on the customer PC."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import importlib.metadata

ROOT=Path(__file__).resolve().parents[1]
def build(output):
    from titan_filmcraft import VERSION
    work=ROOT/'work/filmcraft-build';resources=work/'resources'
    (resources/'motor').mkdir(parents=True,exist_ok=True)
    motor=Path(os.environ['LOCALAPPDATA'])/'TitulosVirais/motor'
    engine=motor/'whisper-cli.exe'
    digest=hashlib.sha256(engine.read_bytes()).hexdigest()
    if digest!='c6718660d8f19ce27e6fa87624a49bcc7a82aa2b7ac4e695cebeded20cef9ec5':
        raise ValueError('Expected audited static Whisper engine unicode-r2.')
    shutil.copy2(engine,resources/'motor/whisper-cli.exe')
    shutil.copy2(motor/'whisper-LICENSE.txt',resources/'motor/whisper-LICENSE.txt')
    licenses=resources/'licenses';licenses.mkdir(exist_ok=True)
    shutil.copy2(motor/'whisper-LICENSE.txt',licenses/'Whisper-MIT.txt')
    shutil.copy2(Path(sys.base_prefix)/'LICENSE.txt',licenses/'Python-LICENSE.txt')
    for package,filename in [('Pillow','Pillow-LICENSE.txt'),('PyInstaller','PyInstaller-COPYING.txt')]:
        distribution=importlib.metadata.distribution(package)
        original=next(p for p in distribution.files if '/licenses/' in str(p) and ('LICENSE' in str(p) or 'COPYING' in str(p)))
        shutil.copy2(distribution.locate_file(original),licenses/filename)
    for name in ('tcl8.6','tk8.6'):
        original=Path(sys.base_prefix)/'tcl'/name/'license.terms'
        if original.is_file():shutil.copy2(original,licenses/(name+'-license.txt'))
    from PIL import Image
    icon=resources/'titan.ico'
    Image.open(ROOT/'src/icons/brand_icon.png').save(icon,format='ICO',sizes=[(16,16),(32,32),(48,48),(128,128),(256,256)])
    output.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--windowed',
                    '--name','Instalar-Titan-FilmCraft-'+VERSION,'--distpath',str(output),'--workpath',str(work/'freeze'),
                    '--specpath',str(work),'--paths',str(ROOT/'filmcraft'),
                    '--icon',str(icon),'--add-data',str(licenses)+os.pathsep+'licenses',
                    '--add-data',str(ROOT/'src/icons/titan_word.png')+os.pathsep+'icons',
                    '--add-data',str(ROOT/'src/sfx')+os.pathsep+'sfx',
                    '--add-data',str(resources/'motor')+os.pathsep+'motor',
                    str(ROOT/'filmcraft/titan_filmcraft.py')],check=True)
    exe=output/('Instalar-Titan-FilmCraft-'+VERSION+'.exe')
    shutil.copy2(ROOT/'filmcraft/LEIA-ME.md',output/'Titan-FilmCraft-LEIA-ME.md')
    shutil.copy2(resources/'motor/whisper-LICENSE.txt',output/'Whisper-LICENSE.txt')
    shutil.make_archive(str(output/'Titan-FilmCraft-Licencas'),'zip',licenses)
    (output/'Titan-FilmCraft-SHA256.txt').write_text(hashlib.sha256(exe.read_bytes()).hexdigest()+'  '+exe.name+'\n',encoding='utf-8')
    return exe

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    print(build(parser.parse_args().output))
