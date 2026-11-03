"""Converte os modelos Fusion (Titulos Virais Plus 16x9 e 9x16) para os modelos do Titan Títulos.

Uso: python tools/build_modelos.py <pasta com 'Titulos Virais Plus 16x9' e '... 9x16'> [saida]

O que faz em cada .setting:
  - troca o logotipo do autor original por um rótulo "Titan Títulos";
  - remove o botão que abre o site do autor original (os.execute);
  - dá a cada título um nome único: "Titulo NN 16x9" / "Titulo NN 9x16";
  - registra em manifest.json as fontes que cada título usa.
As animações (macros do Fusion) não são alteradas.
"""
import json
import os
import re
import shutil
import sys

ASPECTOS = {'16x9': 'Titulos Virais Plus 16x9', '9x16': 'Titulos Virais Plus 9x16'}
PASTA = 'Titan Títulos'


def bloco(texto, inicio):
    """Dado o índice do '{' de abertura, devolve o índice do '}' que o fecha (ignora [[...]] e "...")."""
    profundidade, i = 0, inicio
    while i < len(texto):
        c = texto[i]
        if texto.startswith('[[', i):
            i = texto.index(']]', i) + 2
            continue
        if c == '"':
            i += 1
            while texto[i] != '"':
                i += 2 if texto[i] == '\\' else 1
            i += 1
            continue
        if c == '{':
            profundidade += 1
        elif c == '}':
            profundidade -= 1
            if profundidade == 0:
                return i
        i += 1
    raise ValueError('Chaves desbalanceadas.')


def remover_bloco(texto, padrao):
    """Remove 'Nome = Tipo { ... }' (e a vírgula que o acompanha) do primeiro trecho que casar com o padrão."""
    achou = re.search(padrao, texto)
    if not achou:
        return texto, False
    fecha = bloco(texto, texto.index('{', achou.end() - 1))
    depois = fecha + 1
    if texto[depois:depois + 1] == ',':
        return texto[:achou.start()] + texto[depois + 1:], True
    antes = texto[:achou.start()].rstrip()
    if antes.endswith(','):
        antes = antes[:-1]
    return antes + "\n" + texto[depois:], True


def converter(texto, nome_macro):
    n = 0
    # botão do autor (UserControl) e o InstanceInput que o expõe no macro
    for padrao in (r"\n[ \t]*Input\d+ = InstanceInput \{(?=[^{}]*Source = \"CustomBtn\d+\")",
                   r"\n[ \t]*CustomBtn\d+ = \{",
                   r"\n[ \t]*Logo\d+ = \{"):  # o último é o logotipo (imagem embutida) do autor
        while True:
            texto, ok = remover_bloco(texto, padrao)
            if not ok:
                break
            n += 1
    texto = re.sub(r"\bTtulo\w*? = MacroOperator", nome_macro + " = MacroOperator", texto, count=1)
    texto = re.sub(r'ActiveTool = "Ttulo\w*"', 'ActiveTool = "%s"' % nome_macro, texto)
    return texto, n


def main():
    origem = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), '..', 'src', 'modelos')
    saida = os.path.abspath(saida)
    if os.path.isdir(saida):
        shutil.rmtree(saida)
    manifesto = {'pasta': PASTA, 'titulos': []}
    for aspecto, pasta in ASPECTOS.items():
        fonte = os.path.join(origem, pasta)
        destino = os.path.join(saida, aspecto)
        os.makedirs(destino)
        for arquivo in sorted(os.listdir(fonte)):
            if not arquivo.lower().endswith('.setting'):
                continue
            numero = re.search(r'(\d+)', arquivo).group(1)
            nome = 'Titulo %s %s' % (numero, aspecto)
            macro = 'TitanTitulo%s_%s' % (numero, aspecto)
            texto = open(os.path.join(fonte, arquivo), encoding='utf-8', newline='').read()
            novo, mudancas = converter(texto, macro)
            for proibido in ('editordeconteudo', 'os.execute', 'Bruno', 'Virais', 'data:image/png;base64', 'Logo1', 'CustomBtn'):
                if proibido in novo:
                    raise SystemExit('%s ainda contém "%s"' % (arquivo, proibido))
            open(os.path.join(destino, nome + '.setting'), 'w', encoding='utf-8', newline='').write(novo)
            miniatura = os.path.splitext(arquivo)[0] + '.png'
            if os.path.isfile(os.path.join(fonte, miniatura)):
                shutil.copyfile(os.path.join(fonte, miniatura), os.path.join(destino, nome + '.png'))
            fontes = sorted(set(re.findall(r'Font = Input \{ Value = "([^"]+)"', novo)))
            manifesto['titulos'].append({'nome': nome, 'aspecto': aspecto, 'numero': int(numero), 'fontes': fontes,
                                         'miniatura': os.path.isfile(os.path.join(destino, nome + '.png'))})
    with open(os.path.join(saida, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=1)
    print('titulos:', len(manifesto['titulos']))


if __name__ == '__main__':
    main()
