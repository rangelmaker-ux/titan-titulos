# -*- coding: utf-8 -*-
"""Titan Titles Studio - estilos de legenda (Text+).

Módulo de dados: devolve as receitas (entradas do Text+ e animação) de cada
estilo. Quem aplica no Resolve é o Titan Titles Studio.py, que confere se cada
entrada existe antes de gravar. "Padrão Titan" não muda nada do que já existe.
"""

PADRAO = "padrao"
VIRAL = "viral"
APPLE = "apple"
MARCA_TEXTO = "marca_texto"
TYPEWRITER = "typewriter"

# (id, rótulo). A ordem é a do menu.
ESTILOS = [
    (PADRAO, "Padrão Titan (atual)"),
    (VIRAL, "Viral (contorno grosso + pop)"),
    (APPLE, "Apple (limpo e suave)"),
    (MARCA_TEXTO, "Marca Texto (caixa)"),
    (TYPEWRITER, "Typewriter (máquina)"),
]
IDS = [i for i, _ in ESTILOS]

AMARELO = (1.0, 0.867, 0.0)          # #FFDD00
MARCA_AMARELO = (1.0, 0.902, 0.0)    # #FFE600
BRANCO = (1.0, 1.0, 1.0)
PRETO = (0.0, 0.0, 0.0)


def valido(estilo):
    return estilo if estilo in IDS else PADRAO


def _cor(prefixo_n, rgb):
    return {"Red%d" % prefixo_n: rgb[0], "Green%d" % prefixo_n: rgb[1], "Blue%d" % prefixo_n: rgb[2]}


def entradas(estilo, destaque=False):
    """Entradas estáticas do Text+ (nome -> valor) para o estilo e o papel."""
    estilo = valido(estilo)
    if estilo == VIRAL:
        v = {"Enabled1": 1, "Opacity1": 1.0}
        v.update(_cor(1, AMARELO if destaque else BRANCO))
        v.update({"Enabled2": 1, "Thickness2": 0.075, "Opacity2": 1.0})
        v.update(_cor(2, PRETO))
        v.update({"Enabled3": 1, "Opacity3": 0.85, "Offset3": {1: 0.045, 2: -0.045, 3: 0.0},
                  "SoftnessX3": 12.0, "SoftnessY3": 12.0, "Enabled4": 0})
        v.update(_cor(3, PRETO))
        return v
    if estilo == APPLE:
        v = {"Enabled1": 1, "Opacity1": 1.0 if destaque else 0.55, "Enabled2": 0,
             "Enabled3": 1, "Opacity3": 0.35, "Offset3": {1: 0.02, 2: -0.02, 3: 0.0},
             "SoftnessX3": 8.0, "SoftnessY3": 8.0, "Enabled4": 0}
        v.update(_cor(1, BRANCO))
        v.update(_cor(3, PRETO))
        return v
    if estilo == MARCA_TEXTO:
        v = {"Enabled2": 0, "Enabled3": 1, "Opacity3": 0.4}
        v.update(_cor(3, PRETO))
        if destaque:
            v.update({"Enabled1": 1, "Opacity1": 1.0})
            v.update(_cor(1, (0.05, 0.05, 0.05)))
            v.update({"Enabled4": 1, "Opacity4": 0.92, "Round4": 0.25, "ExtendHorizontal4": 0.04,
                      "ExtendVertical4": 0.02})
            v.update(_cor(4, MARCA_AMARELO))
        else:
            v.update({"Enabled1": 1, "Opacity1": 0.9, "Enabled4": 0})
            v.update(_cor(1, BRANCO))
        return v
    if estilo == TYPEWRITER:
        v = {"Enabled1": 1, "Opacity1": 1.0, "Enabled2": 1, "Thickness2": 0.04,
             "Enabled3": 1, "Opacity3": 0.6, "Enabled4": 0}
        v.update(_cor(1, AMARELO if destaque else BRANCO))
        v.update(_cor(2, PRETO))
        v.update(_cor(3, PRETO))
        return v
    return {}


def animacao(estilo):
    """Receita de animação aplicada a todos os blocos do estilo, usando o
    animador que o Titan já tem. Chaves: entrada (nomes do animador), direcao,
    distancia, writeon. Vazio = não mexe."""
    estilo = valido(estilo)
    if estilo == VIRAL:
        return {"entrada": {"bounce"}, "direcao": "up", "distancia": 0.025}   # pop com mola
    if estilo == APPLE:
        return {"entrada": {"slide"}, "direcao": "up", "distancia": 0.012}    # sobe 1 pouco e aparece
    if estilo == TYPEWRITER:
        return {"entrada": set(), "writeon": True}
    return {}


def caixa_alta(estilo):
    """O estilo força caixa alta? (Viral sim; os demais respeitam o seu ajuste.)"""
    return valido(estilo) == VIRAL


def ritmo_curto(estilo):
    """O estilo usa o ritmo curto (14 caracteres por linha, quebra em pontuação)?"""
    return valido(estilo) != PADRAO
