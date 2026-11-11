# -*- coding: utf-8 -*-
"""Titan Titles Studio - ritmo de legendas curtas ("Viral").

Módulo puro (sem DaVinci, sem rede, sem arquivos): recebe palavras no formato
{"t": texto, "a": início_ms, "b": fim_ms} e devolve blocos e tempos.
Só é usado quando o editor escolhe um estilo diferente de "Padrão Titan".
"""

MAX_CHARS = 14        # caracteres por linha
MIN_CHARS = 8         # mínimo para quebrar em vírgula/ponto e vírgula
MIN_DUR_S = 1.5       # tempo de tela mínimo de cada legenda
SNAP_S = 0.5          # lacunas menores que isso são preenchidas (sem piscar)
GAP_MS = 10           # folga entre uma legenda e a próxima

_FORTE = (".", "!", "?", "…")
_SUAVE = (",", ";")
_ASPAS = "\"'“”‘’)»]"


def _fim_da_frase(texto):
    return texto.rstrip().rstrip(_ASPAS)[-1:]


def _cabe(linhas, palavra, max_chars, max_linhas):
    """A palavra cabe na última linha, ou ainda há linha livre para ela?"""
    if not linhas:
        return True
    if len((linhas[-1] + " " + palavra).strip()) <= max_chars:
        return True
    return len(linhas) < max_linhas


def _adiciona(linhas, palavra, max_chars):
    if linhas and len((linhas[-1] + " " + palavra).strip()) <= max_chars:
        linhas[-1] = (linhas[-1] + " " + palavra).strip()
    else:
        linhas.append(palavra)


def segmentar(palavras, max_chars=MAX_CHARS, max_linhas=2, min_dur=MIN_DUR_S, min_chars=MIN_CHARS):
    """Divide as palavras em blocos de legenda. Devolve lista de listas (as
    mesmas palavras recebidas, sem copiar), na ordem original.

    Quebra quando: a frase termina (. ! ?); há vírgula/ponto e vírgula e o
    bloco já tem pelo menos `min_dur` segundos e `min_chars` letras; ou a
    próxima palavra estoura as linhas permitidas."""
    blocos, atual, linhas = [], [], []
    for w in palavras:
        t = str(w.get("t", "")).strip()
        if not t:
            continue
        if atual:
            texto = " ".join(linhas)
            fim = _fim_da_frase(texto)
            dur = (atual[-1]["b"] - atual[0]["a"]) / 1000.0
            forte = fim in _FORTE
            suave = fim in _SUAVE and dur >= min_dur and len(texto) >= min_chars
            if forte or suave or not _cabe(linhas, t, max_chars, max_linhas):
                blocos.append(atual)
                atual, linhas = [], []
        _adiciona(linhas, t, max_chars)
        atual.append(w)
    if atual:
        blocos.append(atual)
    return blocos


def fins_ms(blocos, min_dur=MIN_DUR_S, snap=SNAP_S, gap_ms=GAP_MS):
    """Hora de saída (ms) de cada bloco: preenche lacunas curtas até a próxima
    legenda (evita piscar) e garante o tempo mínimo de tela quando há espaço."""
    saidas = []
    for i, blk in enumerate(blocos):
        ini, fim = blk[0]["a"], blk[-1]["b"]
        prox = blocos[i + 1][0]["a"] if i + 1 < len(blocos) else None
        if prox is not None and 0 <= prox - fim < snap * 1000:
            fim = prox - gap_ms
        if fim - ini < min_dur * 1000:
            teto = (prox - gap_ms) if prox is not None else ini + min_dur * 1000
            fim = max(fim, min(ini + min_dur * 1000, teto))
        saidas.append(max(fim, ini + gap_ms))
    return saidas
