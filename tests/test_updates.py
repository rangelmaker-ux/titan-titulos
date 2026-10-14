import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('titan_update', ROOT/'src/titan_update.py')
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)
spec = importlib.util.spec_from_file_location('build_release', ROOT/'tools/build_release.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

class Updates(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.dist = self.base/'dist'
        b.build(self.dist)
        self.archive = self.dist/u.ASSET
        self.current = 'v'+(ROOT/'VERSION').read_text().strip()
    def test_packages_and_permissions(self):
        data = u.validate_package(self.archive, self.current)
        self.assertIn('icons/titan_word.png', data)
        with zipfile.ZipFile(self.dist/'Titan-Titles-Studio-Mac.zip') as z:
            self.assertEqual((z.getinfo('Instalar_no_Mac.command').external_attr >> 16) & 0o777, 0o755)
            self.assertNotIn(b'\r', z.read('Instalar_no_Mac.command'))
        with zipfile.ZipFile(self.dist/'Titan-Titles-Studio-Windows.zip') as z:
            self.assertIn('Instalar_Titan.ps1', z.namelist())
    def test_install_backup_preserves_other_plugins(self):
        root=self.base/'Fusion/Scripts/Edit'; root.mkdir(parents=True)
        (root/'Titan Studio.py').write_bytes(b'old script')
        (root/'other-plugin.py').write_bytes(b'keep')
        (root/'icons').mkdir(); (root/'icons/other.png').write_bytes(b'keep icon')
        backup=u.install_package(self.archive,self.current,root)
        self.assertEqual((Path(backup)/'Titan Titles Studio.py').read_bytes(), b'old script')
        self.assertEqual((root/'other-plugin.py').read_bytes(),b'keep')
        self.assertEqual((root/'icons/other.png').read_bytes(),b'keep icon')
        self.assertEqual((root.parent.parent/'TitanTitlesStudio/titan_update.py').read_bytes(),(ROOT/'src/titan_update.py').read_bytes())
    def test_failed_install_rolls_back(self):
        root=self.base/'Fusion/Scripts/Edit'; root.mkdir(parents=True)
        (root/'Titan Studio.py').write_bytes(b'old script')
        (root.parent.parent/'TitanTitlesStudio').mkdir()
        (root.parent.parent/'TitanTitlesStudio/titan_update.py').write_bytes(b'old updater')
        real_replace=u.os.replace
        calls=[0]
        def fail_once(*args):
            calls[0]+=1
            if calls[0]==3: raise OSError('simulated disk failure')
            return real_replace(*args)
        with patch.object(u.os,'replace',side_effect=fail_once):
            with self.assertRaises(OSError): u.install_package(self.archive,self.current,root)
        self.assertEqual((root/'Titan Studio.py').read_bytes(),b'old script')
        self.assertEqual((root.parent.parent/'TitanTitlesStudio/titan_update.py').read_bytes(),b'old updater')
        self.assertFalse((root.parent.parent/'TitanTitlesStudio/icons/arrow_down.png').exists())
    def test_only_one_titan_entry_after_migration(self):
        root=self.base/'Fusion/Scripts/Edit';root.mkdir(parents=True)
        (root/'Titan Titles Studio.py').write_bytes(b'legacy')
        (root/'TitanTitlesStudio').mkdir()
        (root/'TitanTitlesStudio/titan_update.py').write_bytes(b'old module')
        (root/'TitanTitlesStudio-backups').mkdir()
        (root/'TitanTitlesStudio-backups/Titan Titles Studio Backup.py').write_bytes(b'old backup')
        backup=u.install_package(self.archive,self.current,root)
        scripts=list(root.parent.rglob('*.py'))
        self.assertEqual([p.name for p in scripts],['Titan Studio.py'])
        self.assertEqual((Path(backup)/'legacy-Titan Titles Studio.py').read_bytes(),b'legacy')
        u.install_package(self.archive,self.current,root)
        self.assertEqual([p.name for p in root.parent.rglob('*.py')],['Titan Studio.py'])
    def test_tampered_package_rejected(self):
        with zipfile.ZipFile(self.archive) as z: entries={n:z.read(n) for n in z.namelist()}
        entries['Titan Titles Studio.py']=b'print("tampered")'
        b.archive(self.archive,entries)
        with self.assertRaises(ValueError):u.validate_package(self.archive,self.current)
    def test_path_traversal_rejected(self):
        with zipfile.ZipFile(self.archive) as z: entries={n:z.read(n) for n in z.namelist()}
        content=b'evil'; entries['../outside.py']=content
        manifest=json.loads(entries['manifest.json']); manifest['files']['../outside.py']=hashlib.sha256(content).hexdigest()
        entries['manifest.json']=json.dumps(manifest).encode(); b.archive(self.archive,entries)
        with self.assertRaises(ValueError):u.validate_package(self.archive,self.current)
        self.assertFalse((self.base/'outside.py').exists())
    def test_wrong_version_rejected(self):
        with self.assertRaises(ValueError):u.validate_package(self.archive,'v999.0.0')
    def test_urls(self):
        for url in ('http://github.com/x','https://evil.test/x','https://github.com/other/repo/releases/download/v1/x.zip','https://user@api.github.com/repos/'+u.REPO+'/releases/latest'):
            with self.assertRaises(ValueError):u.allowed_url(url)
        u.allowed_url(u.API)
    def test_check_offline_and_prerelease(self):
        with patch.object(u,'open_url',side_effect=OSError('offline')):self.assertIsNone(u.check('v1.0.0'))
        release={'tag_name':self.current,'draft':False,'prerelease':True,'assets':[]}
        with patch.object(u,'open_url',return_value=contextlib.closing(io.BytesIO(json.dumps(release).encode()))):
            self.assertIsNone(u.check('v1.0.0'))
    def test_check_stable_release(self):
        release={'tag_name':self.current,'draft':False,'prerelease':False,'assets':[{'name':u.ASSET,'digest':'sha256:'+'a'*64,'browser_download_url':'https://github.com/'+u.REPO+'/releases/download/'+self.current+'/'+u.ASSET}]}
        with patch.object(u,'open_url',side_effect=lambda url:contextlib.closing(io.BytesIO(json.dumps(release).encode()))):
            self.assertEqual(u.check('v1.0.0')[0],self.current)
            self.assertIsNone(u.check(self.current))

if __name__=='__main__': unittest.main()
