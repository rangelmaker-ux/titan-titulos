import tempfile
from pathlib import Path
from unittest import TestCase,main,mock
import installer

class Installer(TestCase):
    def test_replace_and_remove_known_executable_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'package.exe';source.write_bytes(b'first version')
            target=root/'installed';exe=target/'TitanFilmCraft.exe'
            with mock.patch.object(installer,'TARGET',target),mock.patch.object(installer,'EXE',exe),mock.patch.object(installer,'shortcut') as shortcut:
                installer.install(source);self.assertEqual(exe.read_bytes(),b'first version')
                source.write_bytes(b'new version');installer.install(source)
                self.assertEqual(exe.read_bytes(),b'new version')
                other=target/'preserve.wav';other.write_bytes(b'user audio')
                installer.uninstall();self.assertFalse(exe.exists());self.assertTrue(other.exists())
                self.assertEqual(shortcut.call_args_list,[mock.call(True),mock.call(True),mock.call(False)])

if __name__=='__main__':main(verbosity=2)
