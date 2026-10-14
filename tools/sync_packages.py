"""Keep the Windows/Mac source packages identical to src/."""
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[1]
for folder in ('1 - Windows/Arquivos','2 - Mac'):
    for name in ('Titan Titles Studio.py','titan_update.py','titan_locale.py','titan_sfx.py'):
        shutil.copy2(ROOT/'src'/name,ROOT/folder/name)
    for name in ('icons','sfx'):
        shutil.copytree(ROOT/'src'/name,ROOT/folder/name,dirs_exist_ok=True)
version=(ROOT/'VERSION').read_text().strip()
for relative,encoding in (('1 - Windows/Instalar_Titan.ps1','utf-8-sig'),('2 - Mac/Instalar_no_Mac.command','utf-8')):
    path=ROOT/relative
    text=re.sub(r'v\d+\.\d+\.\d+','v'+version,path.read_text(encoding=encoding))
    path.write_text(text,encoding=encoding,newline='\r\n' if relative.endswith('.ps1') else '\n')
print('Synced Titan Titles Studio v'+version)
