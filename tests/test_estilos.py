import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, ROOT / 'src' / (nome + '.py'))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


fala = carregar('titan_speech')
presets = carregar('titan_presets')


def pal(texto, ini, fim):
    return {'t': texto, 'a': ini, 'b': fim}


class RitmoCurto(unittest.TestCase):
    def test_pontuacao_forte_quebra(self):
        ws = [pal('Oi.', 0, 300), pal('Tudo', 400, 700), pal('bem?', 700, 1000)]
        self.assertEqual([[w['t'] for w in b] for b in fala.segmentar(ws)], [['Oi.'], ['Tudo', 'bem?']])

    def test_virgula_so_quebra_com_tempo_e_tamanho(self):
        curto = [pal('Sim,', 0, 200), pal('mas', 250, 400), pal('nao', 450, 600)]
        self.assertEqual(len(fala.segmentar(curto)), 1)          # menos de 1,5 s e poucas letras
        longo = [pal('Entao,', 0, 900), pal('amigos,', 950, 1700), pal('vamos', 1750, 2200)]
        blocos = fala.segmentar(longo)
        self.assertEqual([w['t'] for w in blocos[0]], ['Entao,', 'amigos,'])

    def test_estouro_de_linhas(self):
        ws = [pal(t, i * 300, i * 300 + 250) for i, t in enumerate(['abracadabra', 'supercalifra', 'gilistico', 'xablau'])]
        blocos = fala.segmentar(ws, max_chars=14, max_linhas=2)
        self.assertEqual(sum(len(b) for b in blocos), 4)
        for b in blocos:
            self.assertLessEqual(len(b), 2)

    def test_todas_as_palavras_preservadas_e_em_ordem(self):
        ws = [pal('p%d' % i, i * 200, i * 200 + 150) for i in range(40)]
        saida = [w['t'] for b in fala.segmentar(ws) for w in b]
        self.assertEqual(saida, [w['t'] for w in ws])

    def test_lacuna_curta_e_preenchida_e_tempo_minimo(self):
        blocos = [[pal('a.', 0, 500)], [pal('b.', 800, 1000)], [pal('c.', 5000, 5200)]]
        fins = fala.fins_ms(blocos)
        self.assertEqual(fins[0], 790)                  # lacuna de 300 ms preenchida
        self.assertEqual(fins[1], 800 + 1500)           # tempo mínimo de 1,5 s (há espaço)
        self.assertEqual(fins[2], 5000 + 1500)
        self.assertTrue(all(fins[i] < blocos[i + 1][0]['a'] for i in range(2)))


class Estilos(unittest.TestCase):
    def test_padrao_nao_muda_nada(self):
        self.assertEqual(presets.entradas(presets.PADRAO, True), {})
        self.assertEqual(presets.animacao(presets.PADRAO), {})
        self.assertFalse(presets.ritmo_curto(presets.PADRAO))
        self.assertEqual(presets.valido('qualquer'), presets.PADRAO)

    def test_todos_os_estilos_tem_receita(self):
        for estilo in presets.IDS[1:]:
            self.assertTrue(presets.entradas(estilo, True), estilo)
            self.assertTrue(presets.entradas(estilo, False), estilo)
            self.assertTrue(presets.ritmo_curto(estilo))

    def test_viral_e_maiusculo_com_pop(self):
        self.assertTrue(presets.caixa_alta(presets.VIRAL))
        self.assertIn('bounce', presets.animacao(presets.VIRAL)['entrada'])
        self.assertEqual(presets.entradas(presets.VIRAL, True)['Red1'], 1.0)
        self.assertEqual(presets.entradas(presets.VIRAL, True)['Blue1'], 0.0)   # amarelo no destaque

    def test_modulos_embutidos_em_dia(self):
        sys.path.insert(0, str(ROOT / 'tools'))
        import embed_modules
        texto = (ROOT / 'src' / 'Titan Titles Studio.py').read_text(encoding='utf-8')
        self.assertIn(embed_modules.bloco(), texto, 'rode python tools/embed_modules.py')
        for pasta in ('1 - Windows/Arquivos', '2 - Mac'):
            copia = (ROOT / pasta / 'Titan Titles Studio.py').read_text(encoding='utf-8')
            self.assertIn(embed_modules.bloco(), copia, pasta)

    def test_sem_caminhos_de_terceiros(self):
        for nome in ('titan_speech.py', 'titan_presets.py'):
            texto = (ROOT / 'src' / nome).read_text(encoding='utf-8')
            self.assertNotIn('Downloads', texto)
            self.assertNotIn('Legendas Master', texto)


if __name__ == '__main__':
    unittest.main()
