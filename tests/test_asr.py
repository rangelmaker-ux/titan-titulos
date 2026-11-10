import ast, array, math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TREE = ast.parse((ROOT / 'src/Titan Titles Studio.py').read_text(encoding='utf-8'))
NAMES = {'_reamostrar_mono', 'parametros_whisper', '_norm_alucinacao', 'filtrar_alucinacoes'}
ASSIGNS = {'_ALUCINACOES'}


def load():
    nodes = [n for n in TREE.body
             if (isinstance(n, ast.FunctionDef) and n.name in NAMES)
             or (isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') in ASSIGNS)]
    ns = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<asr>', 'exec'), ns)
    return ns


NS = load()


def palavras(*itens):
    return [{'t': t, 'a': a, 'b': a + 300} for t, a in itens]


class Resample(unittest.TestCase):
    def tone(self, hz, rate, secs=0.5):
        return array.array('h', (int(10000 * math.sin(2 * math.pi * hz * i / rate))
                                 for i in range(int(rate * secs))))

    def rms(self, a):
        return math.sqrt(sum(v * v for v in a) / len(a))

    def test_length_and_speech_band_preserved(self):
        out = NS['_reamostrar_mono'](self.tone(1000, 48000), 48000, 16000)
        self.assertEqual(len(out), 8000)
        self.assertGreater(self.rms(out), 6000)

    def test_ultrasonic_tone_is_attenuated_not_aliased(self):
        # 20 kHz a 48k: decimar sem filtro viraria um tom audível a 4 kHz
        out = NS['_reamostrar_mono'](self.tone(20000, 48000), 48000, 16000)
        self.assertLess(self.rms(out), 3500)

    def test_non_integer_ratio_gives_16k_length(self):
        out = NS['_reamostrar_mono'](self.tone(1000, 44100), 44100, 16000)
        self.assertAlmostEqual(len(out), 8000, delta=2)


class Params(unittest.TestCase):
    def test_threads_clamped_and_vad_optional(self):
        p = NS['parametros_whisper'](64)
        self.assertEqual(p[:4], ['-t', '8', '-mc', '0'])
        self.assertNotIn('--vad', p)
        self.assertEqual(NS['parametros_whisper'](1)[1], '2')
        v = NS['parametros_whisper'](4, 'x.bin')
        self.assertEqual(v[-3:], ['--vad', '-vm', 'x.bin'])
        self.assertIn('-dtw', v)


class Hallucinations(unittest.TestCase):
    f = staticmethod(lambda w: NS['filtrar_alucinacoes'](w))

    def texts(self, w):
        return [x['t'] for x in w]

    def test_markers_removed(self):
        w = palavras(('[Música]', 0), ('olá', 500), ('♪', 900), ('(aplausos)', 1200), ('mundo', 1500))
        self.assertEqual(self.texts(self.f(w)), ['olá', 'mundo'])

    def test_isolated_cliche_removed(self):
        w = palavras(('olá', 0), ('pessoal', 400), ('Obrigado', 9000), ('por', 9300), ('assistir', 9600))
        self.assertEqual(self.texts(self.f(w)), ['olá', 'pessoal'])
        w = palavras(('Legendas', 0), ('pela', 300), ('comunidade', 600), ('Amara.org', 900))
        self.assertEqual(self.f(w), [])

    def test_real_speech_with_same_words_kept(self):
        w = palavras(('eu', 0), ('digo', 300), ('obrigado', 600), ('por', 900), ('assistir', 1200), ('hoje', 1500))
        self.assertEqual(len(self.f(w)), 6)

    def test_repetition_loop_trimmed(self):
        w = palavras(*[('não', i * 300) for i in range(12)])
        self.assertEqual(len(self.f(w)), 5)
        w = palavras(*[('não', i * 300) for i in range(3)])
        self.assertEqual(len(self.f(w)), 3)


if __name__ == '__main__':
    unittest.main()
