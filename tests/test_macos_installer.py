import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

@unittest.skipUnless(sys.platform == 'darwin', 'Requires actual macOS tools')
class MacInstaller(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.home(),prefix='titan-test-')
        self.addCleanup(self.temp.cleanup)
        self.home=Path(self.temp.name)
        self.fusion=self.home/'Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion'
        self.edit=self.fusion/'Scripts/Edit'
        self.edit.mkdir(parents=True)
        self.version=(ROOT/'VERSION').read_text().strip()
    def run_engine(self,script=None,payload=None):
        return subprocess.run(['/bin/bash',str(script or ROOT/'tools/macos/install_engine.sh'),str(payload or ROOT/'2 - Mac'),str(self.home),str(os.getuid()),str(os.getgid()),self.version],capture_output=True,text=True)
    def test_install_reinstall_and_old_names(self):
        for name in ('Titan Titles Studio.py','Titan Studio Backup.py','Titan Titulo Studio.py','Titan Títulos Studio.py','Titan Update.py'):
            (self.edit/name).write_text('old')
        (self.edit/'Other Plugin.py').write_text('keep')
        (self.edit/'TitanTitlesStudio-backups').mkdir()
        (self.edit/'TitanTitlesStudio-backups/Titan Titles Studio.py').write_text('old backup')
        container=self.home/'Library/Containers/com.blackmagic-design.DaVinciResolveApp'
        container.mkdir(parents=True)
        for _ in range(2):
            result=self.run_engine();self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(sorted(p.name for p in (self.fusion/'Scripts').rglob('*.py')),['Other Plugin.py','Titan Studio.py'])
        self.assertEqual((self.edit/'Other Plugin.py').read_text(),'keep')
        self.assertEqual((self.fusion/'TitanTitlesStudio/installed-version.txt').read_text().strip(),self.version)
        self.assertEqual((self.fusion/'TitanTitlesStudio/caption-bin.drb').read_bytes(),(ROOT/'src/caption-bin.drb').read_bytes())
        self.assertTrue((self.fusion/'TitanTitlesStudio/THIRD_PARTY_NOTICES.md').is_file())
        self.assertEqual((self.edit/'Titan Studio.py').read_bytes(),(ROOT/'src/Titan Titles Studio.py').read_bytes())
        store=container/'Data/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion'
        self.assertTrue((store/'Scripts/Edit/Titan Studio.py').exists())
        self.assertTrue((store/'TitanTitlesStudio/titan_update.py').exists())
    def test_incomplete_package_does_not_change_existing(self):
        (self.edit/'Titan Studio.py').write_text('old')
        payload=self.home/'incomplete';payload.mkdir()
        result=self.run_engine(payload=payload)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual((self.edit/'Titan Studio.py').read_text(),'old')
    def test_symlink_rejected(self):
        outside=self.home/'outside';outside.mkdir()
        (self.fusion/'TitanTitlesStudio').symlink_to(outside,target_is_directory=True)
        result=self.run_engine()
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((outside/'titan_update.py').exists())
    def test_failed_write_restores_previous_version(self):
        (self.edit/'Titan Studio.py').write_text('old')
        resources=self.fusion/'TitanTitlesStudio';resources.mkdir()
        (resources/'titan_update.py').write_text('old updater')
        script=self.home/'fail.sh'
        code=(ROOT/'tools/macos/install_engine.sh').read_text().replace('/bin/mv "$stage/Titan Studio.py" "$target/Titan Studio.py"','/usr/bin/false')
        script.write_text(code)
        result=self.run_engine(script=script)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual((self.edit/'Titan Studio.py').read_text(),'old')
        self.assertEqual((resources/'titan_update.py').read_text(),'old updater')

if __name__=='__main__':unittest.main()
