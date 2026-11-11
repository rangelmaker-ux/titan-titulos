"""Embute titan_speech.py e titan_presets.py dentro de 'Titan Titles Studio.py'.

O atualizador e os instaladores só conhecem uma lista fixa de arquivos; embutir
evita que uma atualização deixe o plugin sem esses módulos. Edite os arquivos
de src/ e rode este script (o sync_packages.py já chama).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULOS = ('titan_speech', 'titan_presets')
INICIO = '# >>> TITAN_MODULOS_EMBUTIDOS (gerado por tools/embed_modules.py; não edite)\n'
FIM = '# <<< TITAN_MODULOS_EMBUTIDOS\n'


def bloco():
    linhas = [INICIO, '_EMBUTIDOS = {\n']
    for nome in MODULOS:
        fonte = (ROOT / 'src' / (nome + '.py')).read_text(encoding='utf-8').replace('\r\n', '\n')
        linhas.append('    %r: %r,\n' % (nome, fonte))
    linhas.append('}\n')
    linhas.append(FIM)
    return ''.join(linhas)


def aplicar():
    caminho = ROOT / 'src' / 'Titan Titles Studio.py'
    texto = caminho.read_bytes().decode('utf-8')
    i, j = texto.index(INICIO), texto.index(FIM) + len(FIM)
    novo = texto[:i] + bloco() + texto[j:]
    if novo != texto:
        caminho.write_bytes(novo.encode('utf-8'))
    return novo != texto


if __name__ == '__main__':
    print('módulos embutidos' + (' (atualizados)' if aplicar() else ' (já em dia)'))
