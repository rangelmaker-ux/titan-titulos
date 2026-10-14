
"""
Títulos Virais — DaVinci Resolve (Python + UIManager)
====================================================
Layouts + animações para Text+ empilhados na timeline (estilo app Captions).

Como usar:
  1. Empilhe 2–4 Text+ (um por palavra/linha) em faixas de vídeo diferentes,
     cobrindo o mesmo trecho da timeline.
  2. Posicione o playhead em cima deles.
  3. Workspace > Scripts > Edit > Titulos Virais
  4. Clique num layout → as linhas se organizam. Selecione uma/várias linhas
     na lista e clique nas animações (ou em nenhuma = aplica em todas).

Funciona no Resolve FREE e Studio (roda dentro do Resolve, via menu Scripts).
"""
import types as _jw_types
_jw_mod = _jw_types.ModuleType('tv_janela_windows')
exec('"""Recuperação pontual de janelas nativas; nunca altera DPI do processo host."""\nimport os\nimport sys\n\n\ndef ajustar_retangulo(rect, area):\n    x, y, w, h = rect\n    left, top, right, bottom = area\n    w, h = min(w, right-left), min(h, bottom-top)\n    return [max(left, min(x, right-w)), max(top, min(y, bottom-h)), w, h]\n\n\ndef recuperar(titulo, diagnostico=None):\n    if sys.platform != \'win32\':\n        return []\n    def evento(**dados):\n        if diagnostico:\n            diagnostico.evento(\'janela.windows\', **dados)\n    try:\n        import ctypes as c\n        from ctypes import wintypes as w\n        u = c.WinDLL(\'user32\', use_last_error=True)\n        callback = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)\n        class Monitor(c.Structure):\n            _fields_ = [(\'cbSize\', w.DWORD), (\'rcMonitor\', w.RECT), (\'rcWork\', w.RECT), (\'dwFlags\', w.DWORD)]\n        signatures = {\n            \'EnumWindows\': ([callback,w.LPARAM],w.BOOL),\n            \'GetWindowThreadProcessId\': ([w.HWND,c.POINTER(w.DWORD)],w.DWORD),\n            \'GetWindowTextW\': ([w.HWND,w.LPWSTR,c.c_int],c.c_int),\n            \'GetWindowRect\': ([w.HWND,c.POINTER(w.RECT)],w.BOOL),\n            \'MonitorFromWindow\': ([w.HWND,w.DWORD],w.HANDLE),\n            \'GetMonitorInfoW\': ([w.HANDLE,c.POINTER(Monitor)],w.BOOL),\n            \'SetWindowPos\': ([w.HWND,w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.UINT],w.BOOL),\n            \'ShowWindow\': ([w.HWND,c.c_int],w.BOOL),\n            \'IsIconic\': ([w.HWND],w.BOOL), \'IsWindowVisible\': ([w.HWND],w.BOOL),\n            \'SetForegroundWindow\': ([w.HWND],w.BOOL),\n        }\n        for name,(args,result) in signatures.items():\n            fn=getattr(u,name);fn.argtypes=args;fn.restype=result\n        encontrados=[]\n        @callback\n        def enum(hwnd,_):\n            pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,c.byref(pid))\n            # UIManager may host the native window in Resolve instead of fuscript.\n            # Exact title only: never reposition arbitrary Resolve/editor windows.\n            text=c.create_unicode_buffer(1024);u.GetWindowTextW(hwnd,text,len(text))\n            if text.value == titulo and (u.IsWindowVisible(hwnd) or u.IsIconic(hwnd)):\n                encontrados.append((hwnd,pid.value))\n            return True\n        if not u.EnumWindows(enum,0): raise c.WinError(c.get_last_error())\n        resultados=[]\n        for hwnd,pid_janela in encontrados:\n            minimizada=bool(u.IsIconic(hwnd))\n            u.ShowWindow(hwnd,9 if minimizada else 5)\n            r=w.RECT()\n            if not u.GetWindowRect(hwnd,c.byref(r)):raise c.WinError(c.get_last_error())\n            m=Monitor();m.cbSize=c.sizeof(m)\n            if not u.GetMonitorInfoW(u.MonitorFromWindow(hwnd,2),c.byref(m)):raise c.WinError(c.get_last_error())\n            antes=[r.left,r.top,r.right-r.left,r.bottom-r.top]\n            area=[m.rcWork.left,m.rcWork.top,m.rcWork.right,m.rcWork.bottom]\n            alvo=ajustar_retangulo(antes,area)\n            # SWP_NOZORDER|SWP_NOACTIVATE: posicionar sem modificar política do host.\n            movida=False\n            if alvo != antes:\n                if not u.SetWindowPos(hwnd,None,*alvo,0x0014):raise c.WinError(c.get_last_error())\n                movida=True\n            frente=bool(u.SetForegroundWindow(hwnd))\n            if not u.GetWindowRect(hwnd,c.byref(r)):raise c.WinError(c.get_last_error())\n            depois=[r.left,r.top,r.right-r.left,r.bottom-r.top]\n            resultado=dict(hwnd=int(hwnd),pid_janela=pid_janela,pid_script=os.getpid(),antes=antes,depois=depois,area_util=area,\n                           reposicionada=movida,minimizada=minimizada,\n                           visivel=bool(u.IsWindowVisible(hwnd)),primeiro_plano=frente,\n                           dentro_da_area=(ajustar_retangulo(depois,area)==depois))\n            evento(**resultado);resultados.append(resultado)\n        if not encontrados:evento(encontrada=False,pid=os.getpid(),titulo=titulo)\n        return resultados\n    except Exception:\n        if diagnostico:diagnostico.falha(\'janela.windows.recuperar\')\n        return []\n', _jw_mod.__dict__)
_recuperar_janela = _jw_mod.recuperar
import types as _diag_types
_diag_mod = _diag_types.ModuleType('tv_diagnostico')
exec('"""Diagnóstico local automático. Nunca recebe payloads, credenciais ou transcrições."""\nimport atexit\nimport datetime\nimport functools\nimport json\nimport logging\nimport logging.handlers\nimport os\nimport platform\nimport subprocess\nimport re\nimport sys\nimport tempfile\nimport threading\nimport time\nimport traceback\nimport uuid\n\n_INSTANCIAS = {}\n_PRINCIPAL = None\n_SEGREDO = re.compile(r\'(?i)([\\"\\\']?(?:password|senha|token|authorization|cookie|secret|hottok|api[_-]?key|codigo|código|otp|challenge|ticket)[\\"\\\']?\\s*[:=]\\s*)(?:[\\"\\\'][^\\"\\\']*[\\"\\\']|[^\\s,;]+)\')\n\n\ndef limpar(valor):\n    texto = str(valor)[:8192]\n    texto = texto.replace(os.path.expanduser(\'~\'), \'~\')\n    if \'@\' in texto:\n        texto = re.sub(r\'[\\w.+-]+@[\\w.-]+\\.[A-Za-z]{2,}\', \'[email]\', texto)\n    texto = re.sub(r\'(?i)\\b(?:Bearer|Basic)\\s+[A-Za-z0-9+/_.=-]+\', \'[authorization]\', texto)\n    texto = re.sub(r\'\\beyJ[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+(?:\\.[A-Za-z0-9_-]+)?\', \'[token]\', texto)\n    texto = re.sub(r\'(https?://[^\\s?\\"\\\']+)\\?[^\\s\\"\\\']*\', r\'\\1?[query removida]\', texto)\n    texto = _SEGREDO.sub(r\'\\1[removido]\', texto)\n    return texto[:4096]\n\n\ndef pasta_logs():\n    if sys.platform == \'darwin\':\n        return os.path.expanduser(\'~/Library/Logs/TitulosVirais\')\n    if os.name == \'nt\':\n        return os.path.join(os.environ.get(\'LOCALAPPDATA\', os.path.expanduser(\'~\')), \'TitulosVirais\', \'Logs\')\n    return os.path.expanduser(\'~/.local/state/TitulosVirais/Logs\')\n\n\nclass Diagnostico:\n    def __init__(self, produto, versao, base=None):\n        self.produto, self.versao = produto, versao\n        self.sessao = uuid.uuid4().hex[:12]\n        self.logger = None\n        self._hooks_instalados = False\n        self.arquivo = None\n        for raiz in [base or pasta_logs(), os.path.join(tempfile.gettempdir(), \'TitulosVirais-Logs-\'+str(getattr(os, \'getuid\', lambda: os.environ.get(\'USERNAME\', \'usuario\'))()))]:\n            try:\n                pasta = os.path.join(raiz, re.sub(r\'[^a-zA-Z0-9_-]\', \'_\', produto))\n                os.makedirs(pasta, mode=0o700, exist_ok=True)\n                if os.path.islink(pasta):\n                    continue\n                # Só remove arquivos antigos do próprio produto; nunca projeto/cache.\n                for nome in os.listdir(pasta):\n                    p = os.path.join(pasta, nome)\n                    if nome.startswith(\'diagnostico-\') and \'.jsonl\' in nome and not os.path.islink(p):\n                        try:\n                            if time.time()-os.path.getmtime(p)>7*86400: os.unlink(p)\n                        except OSError: pass\n                stamp = datetime.datetime.now().strftime(\'%Y%m%d-%H%M%S\')\n                self.arquivo = os.path.join(pasta, \'diagnostico-%s-%s.jsonl\' % (stamp, self.sessao))\n                fd = os.open(self.arquivo, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)\n                os.close(fd)\n                handler = logging.handlers.RotatingFileHandler(self.arquivo, maxBytes=1024*1024, backupCount=3, encoding=\'utf-8\', delay=False)\n                handler.setFormatter(logging.Formatter(\'%(message)s\'))\n                self.logger = logging.Logger(\'diagnostico.\'+self.sessao)\n                self.logger.addHandler(handler)\n                self.logger.propagate = False\n                break\n            except Exception:\n                self.logger = None\n        self.evento(\'inicio\', python=platform.python_version(), sistema=platform.platform(), arquitetura=platform.machine(), pid=os.getpid(), executavel=os.path.basename(sys.executable))\n        atexit.register(self.evento, \'saida_normal\')\n\n    def evento(self, etapa, **contexto):\n        try:\n            if self.logger is None: return\n            proibidos = (\'senha\',\'password\',\'token\',\'secret\',\'codigo\',\'código\',\'otp\',\'email\',\'transcri\',\'payload\',\'headers\',\'body\',\'texto\',\'palavras\')\n            dados = {str(k): limpar(v) if not isinstance(v, (int,float,bool,type(None))) else v\n                     for k,v in contexto.items() if not any(s in str(k).lower() for s in proibidos)}\n            reservados = {\'hora\', \'produto\', \'versao\', \'sessao\', \'thread\', \'etapa\'}\n            dados = {(\'contexto_\'+k if k in reservados else k): v for k, v in dados.items()}\n            registro = dict(hora=datetime.datetime.now(datetime.timezone.utc).isoformat(), produto=self.produto,\n                            versao=self.versao, sessao=self.sessao, thread=threading.current_thread().name,\n                            etapa=limpar(etapa), **dados)\n            self.logger.info(json.dumps(registro, ensure_ascii=False))\n            for h in self.logger.handlers: h.flush()\n        except Exception:\n            pass  # diagnosticar nunca pode impedir o produto de funcionar\n\n    def abrir_pasta(self):\n        """Abre a pasta do arquivo desta sessão, inclusive quando usa fallback."""\n        try:\n            if not self.logger or not self.arquivo:\n                raise OSError(\'Não foi possível criar o arquivo de diagnóstico nesta sessão.\')\n            pasta = os.path.dirname(os.path.abspath(self.arquivo))\n            self.evento(\'logs.abrir.solicitado\', arquivo=self.arquivo)\n            for handler in self.logger.handlers:\n                handler.flush()\n            if not os.path.isfile(self.arquivo) or os.path.getsize(self.arquivo) == 0:\n                raise OSError(\'O arquivo de diagnóstico não foi gravado: \'+self.arquivo)\n            if sys.platform == \'darwin\':\n                subprocess.run([\'/usr/bin/open\', pasta], check=True, timeout=15,\n                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)\n            elif os.name == \'nt\':\n                os.startfile(pasta)\n            else:\n                subprocess.run([\'xdg-open\', pasta], check=True, timeout=15,\n                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)\n            self.evento(\'logs.abrir.solicitacao_aceita\', arquivo=self.arquivo)\n            return pasta\n        except Exception as erro:\n            self.falha(\'logs.abrir\', erro, arquivo=self.arquivo)\n            raise\n\n    def falha(self, etapa, erro=None, **contexto):\n        try:\n            erro = erro or sys.exc_info()[1]\n            if erro is None: return\n            frames = [{\'arquivo\': os.path.basename(f.filename), \'linha\': f.lineno, \'funcao\': f.name}\n                      for f in traceback.extract_tb(erro.__traceback__)[-24:]]\n            # CalledProcessError.__str__ contém comando completo (pode conter dados).\n            mensagem = str(erro) if type(erro).__name__ not in (\'CalledProcessError\',\'TimeoutExpired\') else \'Falha de subprocesso\'\n            detalhes = dict(tipo=type(erro).__name__, mensagem=limpar(mensagem), traceback=json.dumps(frames),\n                            errno=getattr(erro,\'errno\',None), winerror=getattr(erro,\'winerror\',None),\n                            status_http=getattr(erro,\'code\',None), retorno=getattr(erro,\'returncode\',None), **contexto)\n            if type(erro).__name__ in (\'CalledProcessError\', \'TimeoutExpired\'):\n                comando = getattr(erro, \'cmd\', None)\n                # Somente o executável: argumentos podem conter dados do aluno.\n                if isinstance(comando, (list, tuple)) and comando:\n                    detalhes[\'executavel\'] = os.path.basename(str(comando[0]))\n                detalhes[\'timeout_s\'] = getattr(erro, \'timeout\', None)\n                detalhes[\'mensagem\'] = (\'Tempo limite excedido ao executar o motor\' if\n                    type(erro).__name__ == \'TimeoutExpired\' else\n                    \'Processo terminou com retorno %s\' % getattr(erro, \'returncode\', None))\n            self.evento(etapa+\'.erro\', **detalhes)\n            causa = erro.__cause__ or (erro.__context__ if not erro.__suppress_context__ else None)\n            if causa and causa is not erro:\n                self.evento(etapa+\'.causa\', tipo=type(causa).__name__, mensagem=limpar(causa))\n        except Exception: pass\n\n    def operacao(self, etapa):\n        def decorator(fn):\n            @functools.wraps(fn)\n            def executar(*args, **kwargs):\n                inicio = time.monotonic()\n                self.evento(etapa+\'.inicio\')\n                try:\n                    result = fn(*args, **kwargs)\n                    self.evento(etapa+\'.fim\', duracao_ms=round((time.monotonic()-inicio)*1000))\n                    return result\n                except Exception as erro:\n                    self.falha(etapa, erro, duracao_ms=round((time.monotonic()-inicio)*1000))\n                    raise\n            return executar\n        return decorator\n\n    def hooks(self):\n        if self._hooks_instalados:\n            return\n        self._hooks_instalados = True\n        anterior = sys.excepthook\n        def hook(tipo, erro, tb):\n            self.falha(\'nao_tratado\', erro)\n            anterior(tipo, erro, tb)\n        sys.excepthook = hook\n        if hasattr(threading, \'excepthook\'):\n            anterior_thread = threading.excepthook\n            def thread_hook(args):\n                self.falha(\'thread_nao_tratada\', args.exc_value)\n                anterior_thread(args)\n            threading.excepthook = thread_hook\n\n\ndef iniciar(produto, versao, hooks=False):\n    global _PRINCIPAL\n    if _PRINCIPAL is not None and not hooks:\n        return _PRINCIPAL\n    chave = (produto, versao)\n    if chave not in _INSTANCIAS:\n        diag = Diagnostico(produto, versao)\n        _INSTANCIAS[chave] = diag\n    if hooks:\n        _PRINCIPAL = _INSTANCIAS[chave]\n        _PRINCIPAL.hooks()\n    return _INSTANCIAS[chave]\n', _diag_mod.__dict__)
iniciar = _diag_mod.iniciar
_tv_diag = iniciar('davinci', '3.3.5', hooks=False)

import io
import json
import os
import sys
import math
import random
import subprocess


def _sem_janela():
    """kwargs para subprocess NÃO abrir a janela preta de console no Windows.
    O usuário via esse terminal e achava que era bug. Em mac/linux não faz nada."""
    if not sys.platform.startswith("win"):
        return {}
    flags = 0
    try:
        flags |= subprocess.CREATE_NO_WINDOW          
    except Exception:
        _tv_diag.falha('Titulos Virais._sem_janela')
        flags |= 0x08000000
    si = None
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW  
        si.wShowWindow = 0                             
    except Exception:
        _tv_diag.falha('Titulos Virais._sem_janela')
        si = None
    kw = {"creationflags": flags}
    if si is not None:
        kw["startupinfo"] = si
    return kw





try:
    resolve  
except NameError:
    _tv_diag.falha('Titulos Virais.import')
    import DaVinciResolveScript as dvr
    resolve = dvr.scriptapp("Resolve")

try:
    bmd
except NameError:
    _tv_diag.falha('Titulos Virais.import')
    try:
        import fusionscript as bmd
    except ImportError:
        _tv_diag.falha('Titulos Virais.import')
        import DaVinciResolveScript as _dvr
        bmd = _dvr.bmd

fusion = resolve.Fusion()
ui = fusion.UIManager
disp = bmd.UIDispatcher(ui)

IDIOMA = "pt"          
APP_ALVO = "davinci"   
APP_NAME = "Titan Titles Studio"

"""Planeja cortes e modelos juntos, preservando a sequência e os tempos da fala."""

def _pl_dupla(indices, textos):
    if len(indices) < 2:
        return [indices] if indices else []
    corte = min(range(1, len(indices)), key=lambda k: (
        abs(sum(len(textos[i]) for i in indices[:k]) - sum(len(textos[i]) for i in indices[k:])),
        abs(2 * k - len(indices))))
    return [indices[:corte], indices[corte:]]


def plano_modelo(textos, layout, pontuar):
    n = len(textos)
    if not n:
        return None
    if layout == "center":
        cortes = sorted(set([0, max(1, n // 3), max(2, (2 * n) // 3), n]))
        grupos = [list(range(a, min(b, n))) for a, b in zip(cortes, cortes[1:]) if a < n and b > a]
        return {"grupos": grupos, "hi": None, "completo": n >= 3, "custo": 180 if n >= 3 else 8000, "excecao": False}
    pos = "fim" if layout.endswith("_up") else "ini" if layout.endswith("_dn") else "meio"
    permitidos = [n - 1] if pos == "fim" else [0] if pos == "ini" else list(range(n))
    candidatos = [(pontuar([textos[i]]), i) for i in permitidos if pontuar([textos[i]]) > 0]
    excecao = False
    if not candidatos:
        return {"grupos": [list(range(n))], "hi": None, "completo": False, "custo": 6000 * n, "excecao": False}
    score, hero = max(candidatos, key=lambda item: (item[0], -item[1]))
    antes, depois = list(range(hero)), list(range(hero + 1, n))
    cima = _pl_dupla(antes, textos) if layout == "duo_up" else ([antes] if antes else [])
    baixo = _pl_dupla(depois, textos) if layout == "duo_dn" else ([depois] if depois else [])
    grupos = cima + [[hero]] + baixo
    esperado = 3 if layout in ("badge", "cbadge", "duo_up", "duo_dn") else 2
    completo = len(grupos) == esperado
    assert [i for grupo in grupos for i in grupo] == list(range(n))
    return {"grupos": grupos, "hi": len(cima), "completo": completo,
            "custo": (0 if completo else 8000) + (50 - score) * 2 + max(0, max(pontuar([t]) for t in textos) - score) * 100, "excecao": excecao}


def planejar_blocos(palavras, layouts, pontuar, max_palavras=6, max_duracao=4000):
    """Tokens {t,a,b[,corte]} → blocos contíguos com layout, sem tempos estimados.

    Pontuação/corte de vídeo/silêncio longo são fronteiras duras. A programação
    dinâmica prefere desenhos completos e classes normais; blocos incompletos
    ou exceção gramatical custam muito mais. Cobre todas as palavras. Outro modelo é exceção para impedir lacunas.
    """
    if not layouts:
        raise ValueError("Nenhum layout permitido")
    frases, atual = [], []
    for w in palavras:
        if atual:
            anterior = atual[-1]
            fim = str(anterior['t']).rstrip().rstrip('\"\u201d\u2019)\u00bb')
            if (fim[-1:] in ('.', ',', ';', ':', '!', '?', '…') or
                    anterior.get('corte') != w.get('corte') or w['a'] - anterior['b'] > max_duracao):
                frases.append(atual); atual = []
        atual.append(w)
    if atual:
        frases.append(atual)
    saida = []
    modelos = list(dict.fromkeys(list(layouts) + ["badge", "cbadge", "badge_up", "badge_dn", "cbadge_up", "cbadge_dn", "duo_up", "duo_dn"]))
    for frase in frases:
        n = len(frase)
        dp = [(0, None) for _ in range(n + 1)]
        for i in range(n - 1, -1, -1):
            
            best = (float("inf"), None)
            for j in range(i + 1, min(n, i + max_palavras) + 1):
                if frase[j - 1]['b'] - frase[i]['a'] > max_duracao and j > i + 1:
                    break
                for lay in modelos:
                    arr = plano_modelo([w['t'] for w in frase[i:j]], lay, pontuar)
                    if not arr['completo'] and lay != 'badge':
                        continue
                    excecao = lay not in layouts or not arr['completo']
                    
                    
                    cost = arr['custo'] + 250 + dp[j][0] + (100000 * (j-i) if excecao else 0)
                    if cost < best[0]:
                        best = (cost, (j, lay, arr))
            dp[i] = best
        i = 0
        while i < n:
            j, lay, arr = dp[i][1]
            saida.append({'palavras': frase[i:j], 'layout': lay, 'arranjo': arr,
                          'excecao_layout': lay not in layouts or not arr['completo']})
            i = j
    assert [w for p in saida for w in p['palavras']] == list(palavras), 'Cobertura incompleta da transcrição'
    return saida

import types as _tv_types
_tv_texto = _tv_types.ModuleType('tv_texto')
exec('# -*- coding: utf-8 -*-\n"""Caixa de legendas PT/ES, sem rede, modelo linguístico ou dependências.\n\nO léxico abaixo foi escrito para este projeto, não copiado de um corpus ou\ndicionário externo. Só palavras comuns reconhecidas perdem a capitalização;\nnomes, marcas, siglas e caixa mista conservam a grafia recebida do Whisper.\n\nÉ uma normalização conservadora, NÃO reconhecimento perfeito de entidades.\nPalavras desconhecidas podem continuar com maiúscula. Uma palavra comum usada\ncomo nome precisa de contexto ou da lista de ambiguidades para ser protegida.\nOcorrências em minúsculas ajudam apenas com palavra desconhecida no INTERIOR\nde um bloco, nunca com nome desconhecido que inicia bloco/frase. Não inventa\nacentos, capitalização de nomes nem correções ortográficas.\n"""\n\nfrom collections import Counter\nimport unicodedata\n\n\ndef _chave(texto):\n    return unicodedata.normalize("NFC", texto).casefold()\n\n\ndef _palavras(texto):\n    return frozenset(_chave(p) for p in texto.split())\n\n\n# Formas explícitas: não aplicar sufixos genéricos a sobrenomes ou marcas.\nCOMUNS = {\n    "pt": _palavras("""\n        final finais início inícios começo começos vivo vive vivem vivemos viver\n        a à às o os as um uma uns umas de do da dos das em no na nos nas num numa\n        nuns numas ao aos pelo pela pelos pelas por para pra pro pras pros com sem\n        sob sobre entre até após antes desde contra durante perante através\n        e ou mas porém contudo todavia entretanto nem senão porque pois portanto\n        logo então assim embora apesar enquanto quando onde aonde como conforme\n        caso se que quê quem qual quais quanto quanta quantos quantas cujo cuja\n        cujos cujas este esta estes estas esse essa esses essas aquele aquela\n        aqueles aquelas aquilo isto isso eu tu você vocês ele ela eles elas nós\n        vós me mim comigo te ti contigo lhe lhes conosco convosco si consigo\n        meu minha meus minhas teu tua teus tuas seu sua seus suas nosso nossa\n        nossos nossas vosso vossa alguém ninguém algo nada tudo cada outro outra\n        outros outras qualquer quaisquer algum alguma alguns algumas nenhum\n        nenhuma todos todas todo toda mesmo mesma mesmos mesmas próprio própria\n        próprios próprias muito muita muitos muitas pouco pouca poucos poucas\n        bastante bastantes demais mais menos tanto tanta tantos tantas tão\n        sim não também só somente apenas ainda já nunca sempre às vezes talvez\n        quase aqui aí ali lá cá hoje ontem amanhã agora depois cedo tarde antes\n        novamente novamente realmente provavelmente certamente normalmente\n        geralmente finalmente exatamente simplesmente principalmente totalmente\n        completamente rapidamente lentamente facilmente dificilmente\n        infelizmente felizmente imediatamente atualmente praticamente\n        primeiro primeira primeiros primeiras segundo segunda segundos segundas\n        terceiro terceira últimos últimas último última próximo próxima próximos\n        próximas melhor melhores pior piores maior maiores menor menores\n        sou és é somos são era eras éramos eram fui foste foi fomos foram serei\n        será serão seria seriam seja sejam sendo sido ser estar estou está estamos\n        estão estava estavam estive esteve estivemos estiveram estará estarão\n        estaria estariam esteja estejam estando estado tá tô tava ter tenho tem\n        temos têm tinha tinham tive teve tivemos tiveram terá terão teria teriam\n        tenha tenham tendo tido haver há havia haviam houve haverá fazer faço faz\n        fazemos fazem fazia faziam fiz fez fizemos fizeram fará farão faria fariam\n        faça façam fazendo feito feita feitos feitas poder posso pode podemos\n        podem podia podiam pude pôde puderam poderá poderão poderia poderiam\n        possa possam podendo querer quero quer queremos querem queria queriam\n        quis quiseram quererá queira queiram querendo saber sei sabe sabemos\n        sabem sabia sabiam soube souberam saberá saiba saibam sabendo conhecido\n        conhecer conheço conhece conhecemos conhecem conhecia conheci conheceu\n        chamar chamo chama chamamos chamam chamei chamou chamando chamado chamada\n        dizer digo diz dizemos dizem dizia disse disseram dirá dirão dizerem diga\n        digam dizendo dito dita falar falo fala falamos falam falava falei falou\n        falaram falando falado ver vejo vê vemos veem via vi viu vimos viram verá\n        vejam veja vendo visto vista ouvir ouço ouve ouvimos ouvem ouvi ouviu\n        ouviram ouvindo escutar escuta escutei escutando olhar olha olhe olhando\n        ir vou vai vamos vão ia iam fui foi fomos foram indo ido voltar volto\n        volta voltamos voltam voltei voltou voltaram voltando vir venho vem vêm\n        vinha vim veio vieram vindo chegar chego chega chegamos chegam cheguei\n        chegou chegaram chegando sair saio sai saímos saem saí saiu saíram saindo\n        ficar fico fica ficamos ficam ficava fiquei ficou ficaram ficando deixar\n        deixo deixa deixamos deixam deixei deixou deixaram deixando trazer trago\n        traz trazemos trazem trouxe trouxeram trazendo levar levo leva levamos\n        levam levei levou levaram levando colocar coloco coloca colocamos colocam\n        coloquei colocou colocando tirar tiro tira tiramos tiram tirei tirou\n        tirando dar dou dá damos dão dava dei deu deram dando dado receber recebo\n        recebe recebemos recebem recebi recebeu recebendo pegar pego pega pegamos\n        pegam peguei pegou pegando passar passo passa passamos passam passei\n        passou passaram passando começar começo começa começamos começam comecei\n        começou começaram começando acabar acabo acaba acabamos acabam acabei\n        acabou acabaram acabando terminar termino termina terminamos terminam\n        terminei terminou terminando continuar continuo continua continuamos\n        continuam continuei continuou continuando parar paro para paramos param\n        parei parou pararam parando precisar preciso precisa precisamos precisam\n        precisava precisei precisou precisando dever devo deve devemos devem\n        devia deveria deveriam aprender aprendo aprende aprendemos aprendem\n        aprendi aprendeu aprendendo ensinar ensino ensina ensinamos ensinam\n        ensinei ensinou ensinando entender entendo entende entendemos entendem\n        entendia entendi entendeu entenderam entendendo perceber percebo percebe\n        percebemos percebem percebi percebeu percebendo pensar penso pensa\n        pensamos pensam pensei pensou pensaram pensando acreditar acredito\n        acredita acreditamos acreditam acreditei acreditou acreditando lembrar\n        lembro lembra lembramos lembram lembrei lembrou lembrando esquecer\n        esqueço esquece esquecemos esquecem esqueci esqueceu esquecendo gostar\n        gosto gosta gostamos gostam gostei gostou gostaram gostando sentir sinto\n        sente sentimos sentem senti sentiu sentiram sentindo conseguir consigo\n        consegue conseguimos conseguem consegui conseguiu conseguindo tentar\n        tento tenta tentamos tentam tentei tentou tentaram tentando ajudar ajudo\n        ajuda ajudamos ajudam ajudei ajudou ajudando trabalhar trabalho trabalha\n        trabalhamos trabalham trabalhei trabalhou trabalhando usar uso usa usamos\n        usam usava usei usou usaram usando utilizado utilizada utilizar utiliza\n        criar crio cria criamos criam criei criou criaram criando criado criada\n        escrever escrevo escreve escrevemos escrevem escrevi escreveu escreveram\n        escrevendo escrito escrita escritos escritas ler leio lê lemos leem li\n        leu leram lendo lido lida gravar gravo grava gravamos gravam gravei gravou\n        gravando editar edito edita editamos editam editei editou editando\n        publicar publico publica publicamos publicam publiquei publicou publicando\n        abrir abro abre abrimos abrem abri abriu abriram abrindo aberto aberta\n        fechar fecho fecha fechamos fecham fechei fechou fechando fechado fechada\n        selecionar seleciono seleciona selecione selecionado selecionada\n        escolher escolho escolhe escolhemos escolhem escolhi escolheu escolhendo\n        salvar salvo salva salvamos salvam salvei salvou salvando baixar baixo\n        baixa baixamos baixam baixei baixou baixando instalar instalo instala\n        instalamos instalam instalei instalou instalando instalado instalada\n        atualizar atualiza atualizado atualizada corrigir corrijo corrige corrigi\n        corrigiu corrigindo corrigido corrigida funcionar funciona funcionam\n        funcionou funcionando melhorar melhoro melhora melhoramos melhoram\n        melhorei melhorou melhorando mudar mudo muda mudamos mudam mudei mudou\n        mudaram mudando transformar transforma transformando transformado\n        transformada interromper interrompo interrompe interrompi interrompeu\n        interrompendo interrompido interrompida interrompidos interrompidas\n        explicar explico explica explicamos explicam expliquei explicou explicando\n        mostrar mostro mostra mostramos mostram mostrei mostrou mostrando\n        procurar procuro procura procuramos procuram procurei procurou procurando\n        encontrar encontro encontra encontramos encontram encontrei encontrou\n        encontrando perder perco perde perdemos perdem perdi perdeu perdendo\n        ganhar ganho ganha ganhamos ganham ganhei ganhou ganhando comprar compro\n        compra compramos compram comprei comprou comprando vender vendo vende\n        vendemos vendem vendi vendeu vendendo pagar pago paga pagamos pagam paguei\n        pagou pagando valer vale valem valeu valendo existir existe existem\n        existia existir existirão acontece acontecer aconteceu acontecendo\n        verdade problema problemas solução soluções dúvida dúvidas pergunta\n        perguntas resposta respostas exemplo exemplos momento momentos tempo\n        tempos dia dias semana semanas mês meses ano anos hora horas minuto\n        minutos segundo segundos pessoa pessoas gente vida vidas mundo coisa\n        coisas forma formas maneira maneiras jeito jeitos parte partes vez vezes\n        ponto pontos lado lados lugar lugares situação situações caso casos\n        resultado resultados objetivo objetivos oportunidade oportunidades\n        experiência experiências história histórias informação informações\n        conhecimento conhecimentos ideia ideias pensamento pensamentos atenção\n        interesse vontade necessidade necessidades dificuldade dificuldades\n        possibilidade possibilidades diferença diferenças qualidade quantidade\n        capacidade habilidade habilidades criatividade produtividade velocidade\n        importância motivo motivos razão razões sentido significado foco esforço\n        energia processo processos método métodos estratégia estratégias sistema\n        sistemas ferramenta ferramentas recurso recursos etapa etapas ação ações\n        decisão decisões escolha escolhas mudança mudanças desenvolvimento\n        crescimento aprendizagem aprendizado organização planejamento comunicação\n        educação saúde alimentação exercício exercícios comportamento conteúdo\n        conteúdos vídeo vídeos áudio áudios imagem imagens foto fotos texto\n        textos palavra palavras frase frases legenda legendas linha linhas\n        principal principais secundário secundária secundários secundárias herói\n        apoio apoios tamanho tamanhos largura altura posição posições margem\n        margens fonte fontes cor cores modelo modelos animação animações prévia\n        horizontal vertical proporção proporções projeto projetos programa\n        programas aplicativo aplicativos computador computadores arquivo arquivos\n        pasta pastas versão versões instalação atualização tela telas janela\n        janelas botão botões opção opções ajuste ajustes controle controles\n        português espanhol inglês idioma idiomas cliente clientes compra compras\n        empresa empresas equipe equipes dinheiro preço preços valor valores\n        produto produtos serviço serviços mercado negócio negócios trabalho\n        trabalhos carreira profissão família amigo amigos amiga amigas filho\n        filhos filha filhas pai mãe casa escola faculdade universidade curso\n        cursos aula aulas professor professora aluno alunos livro livros página\n        páginas mensagem mensagens nome nomes número números cidade país países\n        bom boa bons boas ruim ruins bonito bonita bonitos bonitas grande grandes\n        pequeno pequena pequenos pequenas novo nova novos novas velho velha\n        certo certa certos certas errado errada errados erradas pronto pronta\n        prontos prontas fácil fáceis difícil difíceis simples importante\n        importantes interessante interessantes possível impossíveis impossível\n        necessário necessária necessários necessárias diferente diferentes igual\n        iguais parecido parecida forte fortes fraco fraca rápido rápida rápidos\n        rápidas lento lenta alto alta altos altas baixo baixa baixos baixas\n        longe perto junto juntos juntas separado separada completo completa\n        completado feito fácil feliz felizes triste tristes tranquilo tranquila\n        seguro segura criativo criativa criativos criativas dinâmico dinâmica\n        automático automática atualizado atualizada real reais verdadeiro\n        verdadeira natural naturais pessoal profissional útil úteis gratuito\n        gratuita livre livres especial especiais positivo positiva negativo\n        negativa ativo ativa aberto aberta fechado fechada local locais normal\n        normais básico básica básico avançado avançada incrível incrível\n        incrível perfeito perfeita obrigado obrigada parabéns desculpa desculpe\n        olá oi obrigado obrigada beleza certo pronto enfim inclusive afinal\n        sozinho sozinha sozinhos sozinhas roteiro roteiros ótimo ótima ótimos ótimas\n    """),\n    "es": _palavras("""\n        final finales inicio inicios comienzo comienzos vivo vive viven vivimos vivir\n        a al ante bajo con contra de del desde durante en entre hacia hasta\n        mediante para por según sin sobre tras el la los las un una unos unas\n        y e o u ni pero sino aunque porque pues entonces así mientras cuando\n        donde adonde como conforme si que qué quien quién quienes quiénes cual\n        cuál cuales cuáles cuanto cuánto cuanta cuánta cuantos cuántos cuantas\n        cuántas cuyo cuya cuyos cuyas yo tú él ella usted nosotros nosotras\n        vosotros vosotras ellos ellas ustedes me mí conmigo te ti contigo se sí\n        consigo lo le les nos os mi mis tu tus su sus mío mía míos mías tuyo tuya\n        tuyos tuyas suyo suya suyos suyas nuestro nuestra nuestros nuestras\n        vuestro vuestra vuestros vuestras este esta estos estas ese esa esos esas\n        aquel aquella aquellos aquellas aquello esto eso todo toda todos todas\n        algo alguien nada nadie cada otro otra otros otras alguno alguna algunos\n        algunas ninguno ninguna cualquier cualquiera cualesquiera mismo misma\n        mismos mismas propio propia propios propias mucho mucha muchos muchas\n        poco poca pocos pocas tanto tanta tantos tantas bastante bastantes\n        demasiado demasiada más menos muy tan también tampoco solo sola solos solas sólo\n        solamente apenas aún aun todavía ya nunca siempre jamás quizá quizás\n        casi aquí ahí allí acá allá hoy ayer mañana ahora después antes luego\n        pronto temprano tarde nuevamente otra realmente probablemente ciertamente\n        normalmente generalmente finalmente exactamente simplemente principalmente\n        totalmente completamente rápidamente lentamente fácilmente difícilmente\n        inmediatamente actualmente prácticamente especialmente lamentablemente\n        primero primera primeros primeras segundo segunda segundos segundas\n        tercero tercera último última últimos últimas próximo próxima próximos\n        próximas mejor mejores peor peores mayor mayores menor menores\n        soy eres es somos sois son era eras éramos eran fui fuiste fue fuimos\n        fueron seré será serán sería serían sea sean siendo sido ser estar estoy\n        estás está estamos están estaba estaban estuve estuvo estuvimos estuvieron\n        estará estarán estaría estén esté estando estado tener tengo tienes tiene\n        tenemos tienen tenía tenían tuve tuvo tuvimos tuvieron tendrá tendrán\n        tendría tenga tengan teniendo tenido haber he has ha hemos han había\n        habían hubo habrá habrán haya hayan hacer hago haces hace hacemos hacen\n        hacía hacían hice hizo hicimos hicieron hará harán haría hagan haga\n        haciendo hecho hecha hechos hechas poder puedo puedes puede podemos pueden\n        podía podían pude pudo pudimos pudieron podrá podrán podría podrían pueda\n        puedan pudiendo querer quiero quieres quiere queremos quieren quería\n        querían quise quiso quisieron quiera quieran queriendo saber sé sabes sabe\n        sabemos saben sabía sabían supe supo supieron sabrá sepan sepa sabiendo\n        conocer conozco conoce conocemos conocen conocía conocí conoció conociendo\n        decir digo dices dice decimos dicen decía dije dijo dijimos dijeron dirá\n        dirán diría diga digan diciendo dicho dicha hablar hablo hablas habla\n        hablamos hablan hablaba hablé habló hablaron hablando ver veo ves ve vemos\n        ven veía vi vio vimos vieron verá verán vean vea viendo visto vista\n        escuchar escucho escucha escuchamos escuchan escuché escuchó escuchando\n        oír oigo oye oímos oyen oí oyó oyeron oyendo mirar miro mira miramos miran\n        miré miró mirando ir voy vas va vamos vais van iba iban fui fue fuimos\n        fueron yendo ido volver vuelvo vuelve volvemos vuelven volví volvió\n        volviendo venir vengo viene venimos vienen venía vine vino vinieron\n        viniendo llegar llego llega llegamos llegan llegué llegó llegaron llegando\n        salir salgo sale salimos salen salí salió salieron saliendo quedar quedo\n        queda quedamos quedan quedaba quedé quedó quedaron quedando dejar dejo\n        deja dejamos dejan dejé dejó dejaron dejando traer traigo trae traemos\n        traen traje trajo trajeron trayendo llevar llevo lleva llevamos llevan\n        llevé llevó llevaron llevando poner pongo pone ponemos ponen puse puso\n        pusieron poniendo puesto puesta quitar quito quita quitamos quitan quité\n        quitó quitando dar doy das da damos dan daba di dio dieron dando dado\n        recibir recibo recibe recibimos reciben recibí recibió recibiendo tomar\n        tomo toma tomamos toman tomé tomó tomando pasar paso pasa pasamos pasan\n        pasé pasó pasaron pasando empezar empiezo empieza empezamos empiezan\n        empecé empezó empezaron empezando comenzar comienzo comienza comenzamos\n        comienzan comencé comenzó comenzando acabar acabo acaba acabamos acaban\n        acabé acabó acabaron acabando terminar termino termina terminamos terminan\n        terminé terminó terminando continuar continúo continúa continuamos\n        continúan continué continuó continuando parar paro para paramos paran\n        paré paró pararon parando necesitar necesito necesita necesitamos\n        necesitan necesitaba necesité necesitó necesitando deber debo debe\n        debemos deben debía debería deberían aprender aprendo aprende aprendemos\n        aprenden aprendí aprendió aprendiendo enseñar enseño enseña enseñamos\n        enseñan enseñé enseñó enseñando entender entiendo entiende entendemos\n        entienden entendía entendí entendió entendieron entendiendo comprender\n        comprendo comprende comprendí comprendió comprendiendo pensar pienso\n        piensa pensamos piensan pensé pensó pensaron pensando creer creo cree\n        creemos creen creí creyó creyendo recordar recuerdo recuerda recordamos\n        recuerdan recordé recordó recordando olvidar olvido olvida olvidamos\n        olvidan olvidé olvidó olvidando gustar gusto gusta gustan gustó gustando\n        sentir siento siente sentimos sienten sentí sintió sintieron sintiendo\n        conseguir consigo consigue conseguimos consiguen conseguí consiguió\n        consiguiendo lograr logro logra logramos logran logré logró logrando\n        intentar intento intenta intentamos intentan intenté intentó intentando\n        ayudar ayudo ayuda ayudamos ayudan ayudé ayudó ayudando trabajar trabajo\n        trabaja trabajamos trabajan trabajé trabajó trabajando usar uso usa usamos\n        usan usaba usé usó usaron usando utilizar utilizo utiliza utilizamos\n        utilizan utilicé utilizó utilizando crear creo crea creamos crean creé\n        creó crearon creando creado creada escribir escribo escribe escribimos\n        escriben escribí escribió escribieron escribiendo escrito escrita\n        escritos escritas leer leo lee leemos leen leí leyó leyeron leyendo leído\n        leída grabar grabo graba grabamos graban grabé grabó grabando editar edito\n        edita editamos editan edité editó editando publicar publico publica\n        publicamos publican publiqué publicó publicando abrir abro abre abrimos\n        abren abrí abrió abrieron abriendo abierto abierta cerrar cierro cierra\n        cerramos cierran cerré cerró cerrando cerrado cerrada seleccionar\n        selecciono selecciona seleccione seleccionado seleccionada elegir elijo\n        elige elegimos eligen elegí eligió eligiendo guardar guardo guarda\n        guardamos guardan guardé guardó guardando descargar descargo descarga\n        descargamos descargan descargué descargó descargando instalar instalo\n        instala instalamos instalan instalé instaló instalando instalado instalada\n        actualizar actualiza actualizado actualizada corregir corrijo corrige\n        corregí corrigió corrigiendo corregido corregida funcionar funciona\n        funcionan funcionó funcionando mejorar mejoro mejora mejoramos mejoran\n        mejoré mejoró mejorando cambiar cambio cambia cambiamos cambian cambié\n        cambió cambiaron cambiando transformar transforma transformando\n        transformado transformada interrumpir interrumpo interrumpe interrumpí\n        interrumpió interrumpiendo interrumpido interrumpida interrumpidos\n        interrumpidas explicar explico explica explicamos explican expliqué\n        explicó explicando mostrar muestro muestra mostramos muestran mostré\n        mostró mostrando buscar busco busca buscamos buscan busqué buscó buscando\n        encontrar encuentro encuentra encontramos encuentran encontré encontró\n        encontrando perder pierdo pierde perdemos pierden perdí perdió perdiendo\n        ganar gano gana ganamos ganan gané ganó ganando comprar compro compra\n        compramos compran compré compró comprando vender vendo vende vendemos\n        venden vendí vendió vendiendo pagar pago paga pagamos pagan pagué pagó\n        pagando valer vale valen valió valiendo existir existe existen existía\n        existirán suceder sucede sucedió sucediendo ocurrir ocurre ocurrió\n        verdad problema problemas solución soluciones duda dudas pregunta\n        preguntas respuesta respuestas ejemplo ejemplos momento momentos tiempo\n        tiempos día días semana semanas mes meses año años hora horas minuto\n        minutos segundo segundos persona personas gente vida vidas mundo cosa\n        cosas forma formas manera maneras modo modos parte partes vez veces\n        punto puntos lado lados lugar lugares situación situaciones caso casos\n        resultado resultados objetivo objetivos oportunidad oportunidades\n        experiencia experiencias historia historias información informaciones\n        conocimiento conocimientos idea ideas pensamiento pensamientos atención\n        interés voluntad necesidad necesidades dificultad dificultades\n        posibilidad posibilidades diferencia diferencias calidad cantidad\n        capacidad habilidad habilidades creatividad productividad velocidad\n        importancia motivo motivos razón razones sentido significado enfoque\n        esfuerzo energía proceso procesos método métodos estrategia estrategias\n        sistema sistemas herramienta herramientas recurso recursos etapa etapas\n        acción acciones decisión decisiones elección elecciones cambio cambios\n        desarrollo crecimiento aprendizaje organización planificación comunicación\n        educación salud alimentación ejercicio ejercicios comportamiento contenido\n        contenidos vídeo vídeos video videos audio audios imagen imágenes foto\n        fotos texto textos palabra palabras frase frases subtítulo subtítulos\n        leyenda leyendas línea líneas principal principales secundario secundaria\n        secundarios secundarias héroe apoyo apoyos tamaño tamaños anchura altura\n        posición posiciones margen márgenes fuente fuentes color colores modelo\n        modelos animación animaciones vista previa horizontal vertical proporción\n        proporciones proyecto proyectos programa programas aplicación aplicaciones\n        computadora computadoras ordenador ordenadores archivo archivos carpeta\n        carpetas versión versiones instalación actualización pantalla pantallas\n        ventana ventanas botón botones opción opciones ajuste ajustes control\n        controles portugués español inglés idioma idiomas cliente clientes compra\n        compras empresa empresas equipo equipos dinero precio precios valor\n        valores producto productos servicio servicios mercado negocio negocios\n        trabajo trabajos carrera profesión familia amigo amigos amiga amigas hijo\n        hijos hija hijas padre madre casa escuela facultad universidad curso\n        cursos clase clases profesor profesora alumno alumnos libro libros página\n        páginas mensaje mensajes nombre nombres número números ciudad país países\n        bueno buena buenos buenas mal malo mala malos malas bonito bonita\n        bonitos bonitas grande grandes pequeño pequeña pequeños pequeñas nuevo\n        nueva nuevos nuevas viejo vieja cierto cierta ciertos ciertas correcto\n        correcta incorrecto incorrecta listo lista listos listas fácil fáciles\n        difícil difíciles simple simples sencillo sencilla importante importantes\n        interesante interesantes posible posibles imposible imposibles necesario\n        necesaria necesarios necesarias diferente diferentes igual iguales\n        parecido parecida fuerte fuertes débil débiles rápido rápida rápidos\n        rápidas lento lenta alto alta altos altas bajo baja bajos bajas lejos\n        cerca junto juntos juntas separado separada completo completa feliz\n        felices triste tristes tranquilo tranquila seguro segura creativo\n        creativa creativos creativas dinámico dinámica automático automática\n        actualizado actualizada real reales verdadero verdadera natural naturales\n        personal profesional útil útiles gratuito gratuita libre libres especial\n        especiales positivo positiva negativo negativa activo activa local\n        locales normal normales básico básica avanzado avanzada increíble\n        increíbles perfecto perfecta gracias disculpa disculpe hola vale bien\n        claro adelante además incluso tampoco tampoco finalmente guion guión guiones\n        llamar llamo llama llamamos llaman llamé llamó llamando llamado llamada\n    """),\n}\nPALAVRAS_COMUNS = COMUNS["pt"] | COMUNS["es"]\n\n\n# Homônimos deliberadamente conservadores: "Luz" pode ser pessoa ou substantivo.\n# Preservar a grafia do usuário é preferível a destruir um nome desconhecido.\nNOMES = _palavras("""\n    João Joao Maria Bruno Ana José Jose Pedro Paulo Paula Carlos Carla Marcos\n    Marco Lucas Luiza Luísa Luis Luís Luiz Laura Leonardo Gabriel Gabriela Miguel\n    Rafael Rafaela Daniel Daniela David Davi Fernando Fernanda Felipe Mariana\n    Marina Beatriz Camila Juliana Julia Júlia André Andre Andressa Eduardo Eduarda\n    Antônio Antonio Antônia Antonia Francisco Francisca Guilherme Gustavo\n    Henrique Helena Isabel Isabela Isabella Sofia Sophia Alice Arthur Artur\n    Bernardo Enzo Lorenzo Valentina Vicente Victor Vitor Vitória Vitoria Vanessa\n    Renata Renato Ricardo Roberto Roberta Rodrigo Sérgio Sergio Silvia Sílvia\n    Thiago Tiago Vera Rosa Clara Luz Mar Sol Flor Graça Graca Glória Gloria\n    Esperança Esperanza Paz Cielo Alma Aurora Amparo Dolores Mercedes Pilar\n    Carmen Consuelo Concepción Encarnación Milagros Soledad Trinidad Salvador\n    Santos Santiago Juan Juana Jorge Javier Xavi Ximena Jimena Diego Alejandro\n    Alejandra Andrés Andres Ángel Angel Ángela Angela Jesús Jesus Cristina Lucía\n    Lucia Manuel Manuela Pablo Rosario Rocío Rocio Teresa Tomás Tomas Ramón\n    Ramon Raúl Raul Enrique Esteban Ignacio Nicolás Nicolas Valeria Iker Aitor Tomé\n    Brasil Portugal Espanha España México Mexico Argentina Chile Colombia\n    Colômbia Venezuela Uruguay Uruguai Paraguay Paraguai Peru Bolívia Bolivia\n    Ecuador Equador Cuba Panamá Panama Honduras Guatemala Nicaragua Canadá\n    Canada França Francia Alemania Alemanha Itália Italia Japão Japón China\n    Índia India África Africa Europa Lisboa Madrid Barcelona Londres London\n    Paris Roma Brasília Brasilia Curitiba Recife Fortaleza Manaus Belém Belem\n    Natal Florianópolis Florianopolis Vitória Vitoria Porto Rio Bahia Paraná\n    Parana Ceará Ceara Pernambuco Alagoas Sergipe Goiás Goias Tocantins Amazonas\n    CapCut Windows Premiere DaVinci Resolve Adobe Microsoft Apple macOS Linux\n    Android iOS Python YouTube Instagram Facebook WhatsApp TikTok Hotmart Google\n    OpenAI ChatGPT Canva Figma Photoshop Illustrator Spotify Netflix Amazon\n    Samsung Sony Canon Nikon Intel AMD Nvidia Inter Poppins Garamond Arial\n""")\n\nSIGLAS = frozenset("TV PC IA AI API URL HTTP HTTPS USB PDF CPU GPU RAM CRM CEO "\n                   "CPF CNPJ RG MEI PJ CLT UX UI HTML CSS DNA ONU OMS UE EUA "\n                   "BR PT ES RJ SP TI".split())\nPARTICULAS = _palavras("de da do das dos e del la las los y van von di du")\nNOMES_COMPOSTOS = tuple(tuple(_chave(p) for p in frase.split()) for frase in (\n    "São Paulo", "São José", "São Luís", "São Luiz", "São João", "São Pedro",\n    "Santo André", "Santo Antônio", "Santa Catarina", "Santa Maria", "Santa Rita",\n    "Rio de Janeiro", "Rio Grande do Sul", "Rio Grande do Norte", "Belo Horizonte",\n    "Porto Alegre", "Minas Gerais", "Espírito Santo", "Mato Grosso", "Mato Grosso do Sul",\n    "Distrito Federal", "Estados Unidos", "Reino Unido", "Banco do Brasil",\n    "San José", "San Juan", "San Pedro", "San Francisco", "San Sebastián",\n    "Santa Fe", "Santa Cruz", "Buenos Aires", "Ciudad de México", "Nueva York",\n    "Los Ángeles", "Las Vegas", "Costa Rica", "República Dominicana", "País Vasco",\n))\n\nCONTEXTO_NOME = tuple(tuple(_chave(p) for p in frase.split()) for frase in (\n    "me chamo", "se chama", "meu nome é", "nome", "me llamo", "se llama",\n    "mi nombre es", "nombre", "doutor", "doutora", "senhor", "senhora",\n    "doctor", "doctora", "señor", "señora", "dr", "dra", "sr", "sra",\n    "professor", "professora", "profesor", "profesora", "prof", "profa",\n    "empresa", "marca", "canal", "cidade", "ciudad", "bairro", "barrio",\n    "rua", "calle", "avenida", "universidade", "universidad", "escola",\n    "escuela", "instituto", "hospital", "restaurante", "hotel",\n))\nPREFIXOS_LOCAL = _palavras("são santo santa san")\nABREVIACOES_NOME = _palavras("dr dra sr sra prof profa")\nFREIOS_NOME = _palavras("""\n    eu você vocês ele ela eles elas nós tu quando onde como hoje ontem amanhã\n    agora então depois antes porque porém mas fui foi sou é são está estão era\n    eram tenho tem têm teve tinha vai vão vou disse fala falou escreve escreveu\n    yo tú él ella ellos ellas usted ustedes nosotros cuando donde cómo hoy ayer\n    mañana ahora entonces después antes porque pero fui fue soy es son está\n    están era eran tengo tiene tienen tuvo tenía voy va van dijo habla habló\n    escribe escribió\n""")\n\n\ndef _separar_token(token):\n    """Recorta somente pontuação externa; mantém hífens, URLs e handles intactos."""\n    if not isinstance(token, str):\n        raise TypeError("Os tokens de legenda precisam ser strings")\n    letras = [i for i, c in enumerate(token) if c.isalpha()]\n    if not letras:\n        return None\n    a, b = letras[0], letras[-1] + 1\n    while b < len(token) and unicodedata.category(token[b]).startswith("M"):\n        b += 1\n    miolo = token[a:b]\n    if any(not (c.isalpha() or unicodedata.category(c).startswith("M")) for c in miolo):\n        return None\n    if any(c.isalnum() or c in "@#_" for c in token[:a] + token[b:]):\n        return None\n    return a, b, miolo, _chave(miolo)\n\n\ndef _capitalizado(info):\n    return info is not None and info[2][0].isupper()\n\n\ndef _fim(token):\n    return token.rstrip().rstrip(\'"\\\'”’»)]}\').endswith(tuple(".,;:!?…"))\n\n\ndef _protegidos(tokens, infos, primeiros):\n    protegidos = {i for i, info in enumerate(infos) if info and (\n        info[3] in NOMES or info[2] in SIGLAS\n        or (any(c.isupper() for c in info[2][1:])\n            and any(c.islower() for c in info[2])))}\n\n    def trecho_nome(inicio, apenas_nomes=False):\n        """Conserva um nome capitalizado e suas partículas, com tamanho limitado."""\n        j, ultimo_nome = inicio, None\n        while j < len(tokens) and j < inicio + 8:\n            info = infos[j]\n            if info is None or (j > inicio and (\n                    j in primeiros or _fim(tokens[j - 1]))):\n                break\n            if _capitalizado(info) and info[3] not in FREIOS_NOME:\n                # "Bruno Gravou" não torna "Gravou" parte do nome. Uma\n                # apresentação explícita ("me chamo Seguro") é evidência maior.\n                if (apenas_nomes and info[3] in PALAVRAS_COMUNS\n                        and info[3] not in NOMES):\n                    break\n                ultimo_nome = j\n                j += 1\n            elif ultimo_nome is not None and info[3] in PARTICULAS:\n                j += 1\n            else:\n                break\n        if ultimo_nome is not None:\n            protegidos.update(range(inicio, ultimo_nome + 1))\n\n    chaves = [info[3] if info else None for info in infos]\n    for i, info in enumerate(infos):\n        if info is None:\n            continue\n        for frase in NOMES_COMPOSTOS:\n            if tuple(chaves[i:i + len(frase)]) == frase and not any(\n                    _fim(t) for t in tokens[i:i + len(frase) - 1]):\n                protegidos.update(range(i, i + len(frase)))\n        if i in protegidos and _capitalizado(info):\n            trecho_nome(i, apenas_nomes=True)\n        for pista in CONTEXTO_NOME:\n            if tuple(chaves[i:i + len(pista)]) != pista:\n                continue\n            if any(_fim(t) for t in tokens[i:i + len(pista) - 1]):\n                continue\n            ultimo = tokens[i + len(pista) - 1].rstrip()\n            if (_fim(ultimo) and not ultimo.endswith(":")\n                    and not (pista[-1] in ABREVIACOES_NOME and ultimo.endswith("."))):\n                continue\n            j = i + len(pista)\n            while j < len(infos) and infos[j] and infos[j][3] in PARTICULAS:\n                j += 1\n            if j < len(infos) and _capitalizado(infos[j]):\n                trecho_nome(j)\n        if info[3] in PREFIXOS_LOCAL and i + 1 < len(infos) and not _fim(tokens[i]):\n            proximo = infos[i + 1]\n            if _capitalizado(proximo) and (proximo[3] in NOMES\n                                          or proximo[3] not in PALAVRAS_COMUNS):\n                protegidos.add(i)\n                trecho_nome(i + 1, apenas_nomes=True)\n    return protegidos\n\n\ndef normalizar_palavras(palavras, idioma="pt"):\n    """Normaliza a transcrição antes dos layouts, conservando tempos/metadados."""\n    palavras = list(palavras)\n    tokens = normalizar_blocos([([w["t"] for w in palavras], 0, 0)], idioma)[0][0]\n    return [dict(w, t=t) for w, t in zip(palavras, tokens)]\n\n\ndef normalizar_blocos(blocos, idioma="pt"):\n    """Nova lista de blocos; muda apenas a caixa dos tokens comuns PT/ES.\n\n    Aceita o contrato do transcritor: [(palavras, início_us, duração_us), ...].\n    Conserva blocos/tokens como lista ou tupla, campos extras e valores de tempo.\n    Não altera a entrada. Idiomas não suportados passam intactos em novas listas.\n    A opção de CAIXA ALTA do app deve ser aplicada DEPOIS desta função.\n    """\n    blocos = list(blocos)\n    tokens, primeiros, mapa = [], set(), []\n    for bloco in blocos:\n        if not isinstance(bloco, (list, tuple)) or not bloco or not isinstance(bloco[0], (list, tuple)):\n            raise TypeError("Bloco precisa conter uma lista/tupla de tokens no primeiro campo")\n        primeiros.add(len(tokens))\n        mapa.append((len(tokens), len(bloco[0])))\n        tokens.extend(bloco[0])\n    infos = [_separar_token(t) for t in tokens]\n    codigo = str(idioma or "").lower().replace("_", "-").split("-", 1)[0]\n    comuns = COMUNS.get(codigo, frozenset())\n    protegidos = _protegidos(tokens, infos, primeiros) if comuns else set(range(len(tokens)))\n    minusculas = Counter(info[3] for i, info in enumerate(infos)\n                         if info and i not in protegidos and info[2].islower())\n    novos = []\n    for i, (token, info) in enumerate(zip(tokens, infos)):\n        if info is None or i in protegidos:\n            novos.append(token)\n            continue\n        a, b, miolo, chave = info\n        inicio = i in primeiros or i == 0 or _fim(tokens[i - 1]) or any(c in token[:a] for c in "¿¡")\n        evidencia_local = (not inicio and miolo.istitle() and len(chave) >= 4\n                           and minusculas[chave] >= 2)\n        if chave in comuns or evidencia_local:\n            token = token[:a] + miolo.lower() + token[b:]\n        novos.append(token)\n    saida = []\n    for bloco, (inicio, tamanho) in zip(blocos, mapa):\n        palavras = novos[inicio:inicio + tamanho]\n        if isinstance(bloco[0], tuple):\n            palavras = tuple(palavras)\n        copia = [palavras] + list(bloco[1:])\n        saida.append(tuple(copia) if isinstance(bloco, tuple) else copia)\n    return saida\n', _tv_texto.__dict__)
normalizar_palavras = _tv_texto.normalizar_palavras

APP_VERSION = "v3.3.6"
WIN_ID = "TitanTitles_Win_v1"
OLD_WIN_IDS = ("LD_Win", "TV_Win_v2", "TV_Win_v3",
               "TV_Win_1", "TV_Win_2", "TV_Win_3", "TV_Win_4",
               "TV_Win_5", "TV_Win_6", "TV_Win_7", "TV_Win_8")
LOGIN_ID = "TV_Login"     
ACCENT = "#38bdf8"   




def _script_dir():
    for cand in (globals().get("__file__"), sys.argv[0] if sys.argv else None):
        if cand and os.path.exists(cand):
            return os.path.dirname(os.path.abspath(cand))
    
    homes = []
    if sys.platform == "darwin":
        homes.append(os.path.expanduser("~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts"))
        homes.append("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts")
    elif sys.platform.startswith("win"):
        homes.append(os.path.join(os.environ.get("APPDATA", ""), "Blackmagic Design", "DaVinci Resolve", "Support", "Fusion", "Scripts"))
        homes.append(os.path.join(os.environ.get("PROGRAMDATA", ""), "Blackmagic Design", "DaVinci Resolve", "Fusion", "Scripts"))
    else:
        homes.append(os.path.expanduser("~/.local/share/DaVinciResolve/Fusion/Scripts"))
        homes.append("/opt/resolve/Fusion/Scripts")
    for h in homes:
        for sub in ("Edit", "Comp", "Utility"):
            p = os.path.join(h, sub)
            if os.path.isfile(os.path.join(p, "Titan Studio.py")) or os.path.isfile(os.path.join(p, "Titan Titles Studio.py")):
                return p
    return os.getcwd()

SCRIPT_DIR = _script_dir()
INSTALL_ROOT = SCRIPT_DIR
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.dirname(INSTALL_ROOT)), "TitanTitlesStudio")
if not os.path.isfile(os.path.join(RESOURCE_DIR, "titan_update.py")):
    legacy_resources = os.path.join(INSTALL_ROOT, "TitanTitlesStudio")
    RESOURCE_DIR = legacy_resources if os.path.isfile(os.path.join(legacy_resources, "titan_update.py")) else INSTALL_ROOT
ICON_DIR = os.path.join(RESOURCE_DIR, "icons")
import importlib.util as _import_util
_update_spec = _import_util.spec_from_file_location("titan_update", os.path.join(RESOURCE_DIR, "titan_update.py"))
_update_module = _import_util.module_from_spec(_update_spec)
_update_spec.loader.exec_module(_update_module)
Atualizador = _update_module.Atualizador
if hasattr(_update_module, "prepare_resources"):
    RESOURCE_DIR = _update_module.prepare_resources(RESOURCE_DIR, globals().get("__file__"))
    ICON_DIR = os.path.join(RESOURCE_DIR, "icons")

# MIT notice for the embedded AutoSubs caption bin: MIT License
#
# Copyright (c) 2023 Tom Moroney
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# The updater embeds this small MIT-licensed Resolve bin so existing installs
# receive it in the script update without requiring a separate resource format.
_CAPTION_BIN_B64 = """
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
"""
_CAPTION_BIN_SHA256 = "f49760cc4d7f59fd7fb7988f80700eb29d65c929e1112bf38c902d2982560dc4"
def _ensure_caption_bin():
    import base64 as _base64, hashlib as _hashlib, zlib as _zlib
    target=os.path.join(RESOURCE_DIR,"caption-bin.drb")
    try:
        if os.path.isfile(target) and _hashlib.sha256(open(target,"rb").read()).hexdigest()==_CAPTION_BIN_SHA256:
            return target
        data=_zlib.decompress(_base64.b64decode(_CAPTION_BIN_B64))
        if _hashlib.sha256(data).hexdigest()!=_CAPTION_BIN_SHA256:
            raise ValueError("hash mismatch")
        os.makedirs(RESOURCE_DIR,exist_ok=True)
        temporary=target+".tmp-"+str(os.getpid())
        with open(temporary,"wb") as output: output.write(data)
        os.replace(temporary,target)
        return target
    except Exception as error:
        try: log("Não foi possível preparar o template Basic Template:",error)
        except Exception: pass
        return ""

_CAPTION_BIN_PATH=_ensure_caption_bin()
def _load_titan_module(name):
    spec = _import_util.spec_from_file_location(name, os.path.join(RESOURCE_DIR, name + ".py"))
    module = _import_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
_locale = _load_titan_module("titan_locale")
_sound_module = _load_titan_module("titan_sfx")
try:
    UI_LANGUAGE = _locale.configure(fusion.GetData("TitanTitlesStudio.uiLanguage") or "pt-BR")
except Exception:
    UI_LANGUAGE = _locale.configure("pt-BR")
ui = _locale.UIProxy(ui)
tr = _locale.translate




ICON_URL = ICON_DIR.replace("\\", "/")


def icon(name):
    p = os.path.join(ICON_DIR, name + ".png")
    if os.path.exists(p):
        return ui.Icon({"File": p})
    return None


def log(*a):
    print("[%s] " % APP_NAME + " ".join(str(x) for x in a))





def get_timeline():
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject()
    if not proj:
        return None, None
    return proj, proj.GetCurrentTimeline()


def tc_to_frame(tc, fps):
    parts = tc.replace(";", ":").split(":")
    if len(parts) != 4:
        return 0
    h, m, s, f = [int(x) for x in parts]
    nominal = int(round(fps))
    frame = (h * 3600 + m * 60 + s) * nominal + f
    if ";" in tc and nominal in (30, 60) and abs(fps - nominal * 1000 / 1001) < 0.01:
        minutes = h * 60 + m
        frame -= (2 if nominal == 30 else 4) * (minutes - minutes // 10)
    return frame


def playhead_frame(tl):
    fps = float(tl.GetSetting("timelineFrameRate") or 24)
    timecode = tl.GetCurrentTimecode()
    return tc_to_frame(timecode, fps) if timecode else None


def timeline_aspect(tl):
    try:
        w = float(tl.GetSetting("timelineResolutionWidth"))
        h = float(tl.GetSetting("timelineResolutionHeight"))
        return h / w if w else 1.0   
    except Exception:
        _tv_diag.falha('Titulos Virais.timeline_aspect')
        return 1.0


def find_textplus_under_playhead(tl, all_titles=False):
    """Retorna lista de dicts {item, track, comp, tool, text, start, end} ordenada por início."""
    frame = playhead_frame(tl)
    out = []
    if frame is None and not all_titles:
        return out
    try:
        ntracks = int(tl.GetTrackCount("video"))
    except Exception:
        _tv_diag.falha('Titulos Virais.find_textplus_under_playhead')
        ntracks = 0
    for t in range(1, ntracks + 1):
        items = tl.GetItemListInTrack("video", t) or []
        if hasattr(items, "values"):
            items = items.values()
        for it in items:
            try:
                st, en = int(it.GetStart()), int(it.GetEnd())
            except Exception:
                _tv_diag.falha('Titulos Virais.find_textplus_under_playhead')
                continue
            if not all_titles and not (st <= frame < en):
                continue
            try:
                if it.GetFusionCompCount() < 1:
                    continue
                comp = it.GetFusionCompByIndex(1)
            except Exception:
                _tv_diag.falha('Titulos Virais.find_textplus_under_playhead')
                continue
            if not comp:
                continue
            try:
                tool = comp.FindToolByID("TextPlus")
                if not tool:
                    tools = comp.GetToolList(False, "TextPlus") or {}
                    tools = list(tools.values()) if hasattr(tools, "values") else list(tools)
                    tool = tools[0] if tools else None
                if not tool:
                    continue
                txt = tool.GetInput("StyledText") or ""
                out.append({
                    "item": it, "track": t, "comp": comp, "tool": tool,
                    "text": str(txt).strip(), "start": st, "end": en,
                    "uid": _uid(it, t, st),
                })
            except Exception:
                _tv_diag.falha("Titan.detectar_textplus")
                continue
    out.sort(key=lambda e: (e["start"], e["track"]))
    return out


def _uid(item, track, start):
    try:
        u = item.GetUniqueId()
        if u:
            return str(u)
    except Exception:
        _tv_diag.falha('Titulos Virais._uid')
        pass
    return "V%d_%d" % (track, start)


def to_xy(v):
    """Center pode vir como dict {1:x,2:y}, lista ou tupla."""
    if v is None:
        return (0.5, 0.5)
    if isinstance(v, dict):
        keys = sorted(v.keys(), key=lambda k: float(k))
        return (float(v[keys[0]]), float(v[keys[1]]))
    try:
        return (float(v[0]), float(v[1]))
    except Exception:
        _tv_diag.falha('Titulos Virais.to_xy')
        return (0.5, 0.5)


def comp_range(comp):
    a = comp.GetAttrs()
    s = int(a.get("COMPN_RenderStart", 0))
    e = int(a.get("COMPN_RenderEnd", s))
    if e < s:
        e = s
    return s, e


def visible_range(entry):
    """Frames do comp realmente visíveis na timeline (respeita o trim do
    clipe). Keys fora dessa janela existem mas nunca aparecem — era o bug
    de 'só mostra a animação se fizer trim pra esquerda'."""
    it = entry.get("item")
    if it is not None:
        try:
            lo = int(it.GetLeftOffset() or 0)
            dur = int(it.GetEnd()) - int(it.GetStart())
            if dur > 0:
                
                
                try:
                    src_fps = float(it.GetMediaPoolItem().GetClipProperty("FPS") or 0)
                except Exception:
                    _tv_diag.falha('Titulos Virais.visible_range')
                    src_fps = 0.0
                if src_fps > 0:
                    _, tl = get_timeline()
                    tl_fps = float(tl.GetSetting("timelineFrameRate") or 0) if tl else 0.0
                    if tl_fps > 0 and abs(src_fps - tl_fps) > 0.01:
                        lo = int(round(lo * src_fps / tl_fps))
                        dur = int(round(dur * src_fps / tl_fps))
                return lo, lo + dur - 1
        except Exception:
            _tv_diag.falha('Titulos Virais.visible_range')
            pass
    return comp_range(entry["comp"])


def _output_image(tool, frame):
    try:
        return tool.Output[frame]
    except Exception:
        _tv_diag.falha('Titulos Virais._output_image')
        pass
    try:
        return tool.Output.GetValue(frame)
    except Exception:
        _tv_diag.falha('Titulos Virais._output_image')
        return None


def measure_bbox(entry, frame=None):
    """Caixa REAL do texto renderizado (DataWindow), normalizada.
    Retorna (largura, altura, centro_x, centro_y) ou None se a medição falhar."""
    comp, tool = entry.get("comp"), entry.get("tool")
    if comp is None or tool is None:
        return None
    try:
        s, e = visible_range(entry)
        frame = (s + e) // 2 if frame is None else frame
        img = _output_image(tool, frame)
        if img is None:
            return None
        W, H = float(img.Width), float(img.Height)
        dw = img.DataWindow
        if isinstance(dw, dict):
            vals = [dw[k] for k in sorted(dw.keys(), key=lambda k: float(k))]
        elif isinstance(dw, (list, tuple)):
            vals = list(dw)
        else:
            vals = [dw[i] for i in (1, 2, 3, 4)]
        x0, y0, x1, y1 = [float(v) for v in vals[:4]]
        if not W or not H or x1 <= x0 or y1 <= y0:
            return None
        bbox = ((x1 - x0) / W, (y1 - y0) / H,
                (x0 + x1) / 2.0 / W, (y0 + y1) / 2.0 / H)
        
        
        try:
            size = float(get_at(tool, "Size", frame) or 0)
            cx, cy = to_xy(get_at(tool, "Center", frame))
            if size > 0:
                tool.SetData("TV_preview_anchor", "%s\n%s\n%.12g,%.12g" % (
                    tool.GetInput("Font"), tool.GetInput("Style"),
                    (bbox[2] - cx) / size, (bbox[3] - cy) / size))
        except Exception:
            _tv_diag.falha('Titulos Virais.measure_bbox')
            pass
        return bbox
    except Exception as ex:
        _tv_diag.falha('Titulos Virais.measure_bbox')
        log("measure_bbox:", ex)
        return None





def _input(tool, name):
    try:
        return getattr(tool, name)
    except Exception:
        _tv_diag.falha('Titulos Virais._input')
        return None


def remove_modifier(tool, name):
    """Remove qualquer modificador/spline conectado ao input `name`.
    Verifica se a remoção pegou — modificador sobrevivente mistura keys
    velhas com novas e gera animação corrompida."""
    inp = _input(tool, name)
    if inp is None:
        return
    try:
        out = inp.GetConnectedOutput()
        if out:
            mod = out.GetTool()
            if mod:
                mod.Delete()
        out2 = inp.GetConnectedOutput()
        if out2 is not None:
            log("ERRO: modificador de", name, "resistiu ao Delete — keys antigas podem sobrar")
    except Exception as ex:
        _tv_diag.falha('Titulos Virais.remove_modifier')
        log("remove_modifier", name, ex)


def ensure_spline(tool, name):
    """Spline NOVA, sempre: spline antiga que resiste ao delete guarda keys
    fantasma no meio do clipe (causa do texto 'variando' o tempo todo)."""
    remove_modifier(tool, name)
    try:
        if _input(tool, name).GetConnectedOutput() is None:
            tool.AddModifier(name, "BezierSpline")
    except Exception:
        _tv_diag.falha('Titulos Virais.ensure_spline')
        tool.AddModifier(name, "BezierSpline")


def ensure_xypath(tool):
    remove_modifier(tool, "Center")
    try:
        out = tool.Center.GetConnectedOutput()
    except Exception:
        _tv_diag.falha('Titulos Virais.ensure_xypath')
        out = None
    if out is None:
        tool.AddModifier("Center", "XYPath")
    xy = tool.Center.GetConnectedOutput().GetTool()
    for axis in ("X", "Y"):
        
        try:
            o = _input(xy, axis).GetConnectedOutput()
            if o:
                o.GetTool().Delete()
        except Exception:
            _tv_diag.falha('Titulos Virais.ensure_xypath')
            pass
        try:
            xy.AddModifier(axis, "BezierSpline")
        except Exception as ex:
            _tv_diag.falha('Titulos Virais.ensure_xypath')
            log("AddModifier", axis, "falhou:", ex)
    return xy


def spline_times(owner, name):
    """Frames que já têm key na spline do input `name`. O AddModifier de
    BezierSpline SEMEIA uma key no frame atual do comp com o valor congelado
    — se não for sobrescrita, o texto deriva até ela no meio do clipe."""
    try:
        sp = _input(owner, name).GetConnectedOutput().GetTool()
        return [int(round(float(k))) for k in (sp.GetKeyFrames() or {}).keys()]
    except Exception:
        _tv_diag.falha('Titulos Virais.spline_times')
        return []


def set_key(tool, name, value, frame):
    try:
        tool.SetInput(name, value, frame)
    except Exception as ex:
        _tv_diag.falha('Titulos Virais.set_key')
        log("set_key falhou", name, frame, ex)


def set_val(tool, name, value):
    try:
        tool.SetInput(name, value)
    except Exception as ex:
        _tv_diag.falha('Titulos Virais.set_val')
        log("set_val falhou", name, ex)


def set_point(tool, name, x, y):
    """Seta um input de ponto (Center). Tenta lista e depois dict 1-based."""
    try:
        return tool.SetInput(name, [float(x), float(y)]) is not False
    except Exception:
        _tv_diag.falha('Titulos Virais.set_point')
        pass
    try:
        return tool.SetInput(name, {1: float(x), 2: float(y)}) is not False
    except Exception as ex:
        _tv_diag.falha('Titulos Virais.set_point')
        log("set_point falhou", name, ex)
        return False


def get_at(tool, name, frame):
    """Valor de um input avaliado num frame (funciona mesmo se animado)."""
    try:
        return tool.GetInput(name, frame)
    except Exception:
        _tv_diag.falha('Titulos Virais.get_at')
        return tool.GetInput(name)


def find_media_out(comp):
    mo = comp.FindToolByID("MediaOut")
    return mo


def get_blur_tool(comp, text_tool, create):
    blur = comp.FindTool("LD_Blur")
    if blur or not create:
        return blur
    mo = find_media_out(comp)
    try:
        pos = comp.GetToolPosition(text_tool) if hasattr(comp, "GetToolPosition") else None
    except Exception:
        _tv_diag.falha('Titulos Virais.get_blur_tool')
        pos = None
    blur = comp.AddTool("Blur", -32768, -32768)
    blur.SetAttrs({"TOOLS_Name": "LD_Blur"})
    try:
        blur.ConnectInput("Input", text_tool)
    except Exception:
        _tv_diag.falha('Titulos Virais.get_blur_tool')
        blur.Input.ConnectTo(text_tool.Output)
    
    
    
    destino = comp.FindTool("LD_Move") or mo
    if destino:
        try:
            destino.ConnectInput("Input", blur)
        except Exception:
            _tv_diag.falha('Titulos Virais.get_blur_tool')
            destino.Input.ConnectTo(blur.Output)
    return blur


def get_move_tool(comp, text_tool, create=False):
    """Transform 'LD_Move' logo antes do MediaOut. Mover por aqui custa UMA
    chamada (~7ms) em vez de reescrever ~100 keyframes (~1s) — é o que
    permite arrastar a posição em tempo real."""
    mv = comp.FindTool("LD_Move")
    if mv or not create:
        return mv
    mo = find_media_out(comp)
    if mo is None:
        return None
    try:
        origem = mo.Input.GetConnectedOutput().GetTool()
    except Exception:
        _tv_diag.falha('Titulos Virais.get_move_tool')
        origem = text_tool
    mv = comp.AddTool("Transform", -32768, -32768)
    mv.SetAttrs({"TOOLS_Name": "LD_Move"})
    try:
        mv.ConnectInput("Input", origem)
    except Exception:
        _tv_diag.falha('Titulos Virais.get_move_tool')
        mv.Input.ConnectTo(origem.Output)
    try:
        mo.ConnectInput("Input", mv)
    except Exception:
        _tv_diag.falha('Titulos Virais.get_move_tool')
        mo.Input.ConnectTo(mv.Output)
    return mv


def set_move(entry, dx, dy):
    """Deslocamento do bloco (0 = sem deslocamento). A ferramenta fica
    guardada na própria entrada: procurar por nome a cada evento de arrasto
    custaria caro."""
    try:
        mv = entry.get("_mv")
        if mv is None:
            criar = not (abs(dx) < 1e-6 and abs(dy) < 1e-6)
            mv = get_move_tool(entry["comp"], entry["tool"], criar)
            if mv is None:
                return not criar
            entry["_mv"] = mv
        return set_point(mv, "Center", 0.5 + dx, 0.5 + dy)
    except Exception as ex:
        _tv_diag.falha('Titulos Virais.set_move')
        entry.pop("_mv", None)
        log("set_move falhou:", ex)
        return False


def remove_blur_tool(comp, text_tool):
    blur = comp.FindTool("LD_Blur")
    if not blur:
        return
    mo = find_media_out(comp)
    
    
    destino = comp.FindTool("LD_Move") or mo
    if destino:
        try:
            destino.ConnectInput("Input", text_tool)
        except Exception:
            _tv_diag.falha('Titulos Virais.remove_blur_tool')
            destino.Input.ConnectTo(text_tool.Output)
    blur.Delete()





def ease_out(t):
    """Entrada: desacelera na chegada (quártica — padrão motion design)."""
    return 1 - (1 - t) ** 4


def ease_in(t):
    """Saída: acelera na partida."""
    return t ** 4


def piecewise(points, t):
    """Interpolação linear em pontos [(t,v),...] com t em 0..1."""
    if t <= points[0][0]:
        return points[0][1]
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        if t0 <= t <= t1:
            k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * k
    return points[-1][1]


BOUNCE_IN = [(0.0, 0.0), (0.55, 1.14), (0.8, 0.95), (1.0, 1.0)]
BOUNCE_OUT = [(0.0, 1.0), (0.25, 1.12), (1.0, 0.0)]
FLICKER_PAT = [0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1]

DIRS = {"left": (-1, 0), "right": (1, 0), "up": (0, 1), "down": (0, -1), "none": (0, 0)}





def new_state():
    return {
        "in": set(), "out": set(),          
        "dir_in": "left", "dir_out": "right",
        "shake": False, "jitter": False, "mblur": False,
        "base_center": None, "base_size": None,
        "last_range": None,    
        "seed": random.randint(1, 99999),
    }


class Animator(object):
    def __init__(self):
        self.states = {}        
        self.dur = 20           
        self.dist = 0.15        
        self.shake_amp = 0.006
        self.blur_amt = 30.0

    def state(self, entry):
        st = self.states.get(entry["uid"])
        if st is None:
            st = new_state()
            self.states[entry["uid"]] = st
        tool = entry["tool"]
        
        if st["base_center"] is None or st["base_size"] is None:
            s, e = visible_range(entry)
            mid = (s + e) // 2
            if st["base_center"] is None:
                st["base_center"] = to_xy(get_at(tool, "Center", mid))
            if st["base_size"] is None:
                try:
                    st["base_size"] = float(get_at(tool, "Size", mid) or 0.08)
                except Exception:
                    _tv_diag.falha('Titulos Virais.state')
                    st["base_size"] = 0.08
        return st

    
    def set_base(self, entry, center=None, size=None):
        st = self.state(entry)
        if center is not None:
            st["base_center"] = tuple(center)
        if size is not None:
            st["base_size"] = float(size)

    def has_anim(self, st):
        return bool(st["in"] or st["out"])

    
    def render(self, entry):
        """Reconstrói TODAS as keyframes do clipe a partir do estado."""
        tool, comp = entry["tool"], entry["comp"]
        st = self.state(entry)
        s, e = visible_range(entry)
        st["last_range"] = (s, e)
        length = e - s + 1
        dur = max(2, min(self.dur, max(2, length // 2)))
        rnd = random.Random(st["seed"])
        bx, by = st["base_center"]
        bsize = st["base_size"]

        comp.Lock()
        try:
            comp.StartUndo(APP_NAME)
        except Exception:
            _tv_diag.falha('Titulos Virais.render')
            pass
        try:
            
            pos = {}   
            def add(f, dx, dy):
                ox, oy = pos.get(f, (0.0, 0.0))
                pos[f] = (ox + dx, oy + dy)

            if "slide" in st["in"]:
                dx, dy = DIRS.get(st["dir_in"], (0, 0))
                for i in range(dur + 1):
                    t = i / float(dur)
                    k = 1 - ease_out(t)
                    add(s + i, -dx * self.dist * k, -dy * self.dist * k)
            if "slide" in st["out"]:
                dx, dy = DIRS.get(st["dir_out"], (0, 0))
                for i in range(dur + 1):
                    t = i / float(dur)
                    k = ease_in(t)
                    add(e - dur + i, dx * self.dist * k, dy * self.dist * k)
            if "shake" in st["in"]:
                for i in range(dur + 1):
                    k = 1 - i / float(dur)
                    a = self.dist * 0.25 * k
                    add(s + i, rnd.uniform(-a, a), rnd.uniform(-a, a))
            if "shake" in st["out"]:
                for i in range(dur + 1):
                    k = i / float(dur)
                    a = self.dist * 0.25 * k
                    add(e - dur + i, rnd.uniform(-a, a), rnd.uniform(-a, a))
            if pos:
                xy = ensure_xypath(tool)
                
                
                anchors = [s, e, min(e, s + dur + 1), max(s, e - dur - 1)]
                seeds = spline_times(xy, "X") + spline_times(xy, "Y")
                frames = sorted(set(list(pos.keys()) + anchors + seeds))
                for f in frames:
                    dx, dy = pos.get(f, (0.0, 0.0))
                    set_key(xy, "X", bx + dx, f)
                    set_key(xy, "Y", by + dy, f)
            else:
                remove_modifier(tool, "Center")
                set_point(tool, "Center", bx, by)

            
            size = {}
            def mul(f, k):
                size[f] = size.get(f, 1.0) * k

            if "bounce" in st["in"]:
                for i in range(dur + 1):
                    mul(s + i, piecewise(BOUNCE_IN, i / float(dur)))
            if "bounce" in st["out"]:
                for i in range(dur + 1):
                    mul(e - dur + i, piecewise(BOUNCE_OUT, i / float(dur)))
            if size:
                ensure_spline(tool, "Size")
                anchors = [s, e, min(e, s + dur + 1), max(s, e - dur - 1)]
                frames = sorted(set(list(size.keys()) + anchors + spline_times(tool, "Size")))
                for f in frames:
                    set_key(tool, "Size", bsize * size.get(f, 1.0), f)
            else:
                remove_modifier(tool, "Size")
                set_val(tool, "Size", bsize)

            
            
            
            
            blend = {}
            if st["in"]:
                if "flicker" in st["in"]:
                    for i in range(dur):
                        blend[s + i] = FLICKER_PAT[i % len(FLICKER_PAT)]
                    blend[s + dur] = 1
                else:
                    for i in range(dur + 1):
                        blend[s + i] = ease_out(i / float(dur))
            if st["out"]:
                if "flicker" in st["out"]:
                    for i in range(dur):
                        blend[e - dur + i] = FLICKER_PAT[(dur - i) % len(FLICKER_PAT)]
                    blend[e] = 0
                else:
                    for i in range(dur + 1):
                        blend[e - dur + i] = 1.0 - ease_in(i / float(dur))
            if blend:
                ensure_spline(tool, "Opacity1")
                anchors = [s, e, min(e, s + dur + 1), max(s, e - dur - 1)]
                frames = sorted(set(list(blend.keys()) + anchors + spline_times(tool, "Opacity1")))
                for f in frames:
                    set_key(tool, "Opacity1", float(blend.get(f, 1)), f)
            else:
                remove_modifier(tool, "Opacity1")
                set_val(tool, "Opacity1", 1.0)

            
            blur = {}
            if "blur" in st["in"]:
                for i in range(dur + 1):
                    blur[s + i] = self.blur_amt * (1 - ease_out(i / float(dur)))
            if "blur" in st["out"]:
                for i in range(dur + 1):
                    blur[e - dur + i] = self.blur_amt * ease_in(i / float(dur))
            if blur:
                bt = get_blur_tool(comp, tool, True)
                ensure_spline(bt, "XBlurSize")
                anchors = [s, e, min(e, s + dur + 1), max(s, e - dur - 1)]
                frames = sorted(set(list(blur.keys()) + anchors + spline_times(bt, "XBlurSize")))
                for f in frames:
                    set_key(bt, "XBlurSize", blur.get(f, 0.0), f)
            else:
                remove_blur_tool(comp, tool)

            
            set_val(tool, "MotionBlur", 1 if st["mblur"] else 0)
            if st["mblur"]:
                set_val(tool, "Quality", 4)
                set_val(tool, "ShutterAngle", 180)
        finally:
            try:
                comp.EndUndo(True)
            except Exception:
                _tv_diag.falha('Titulos Virais.render')
                pass
            comp.Unlock()

    def reset(self, entry):
        st = self.state(entry)
        try:                      
            entry["tool"].SetData(ANIM_KEY, "")
        except Exception:
            _tv_diag.falha('Titulos Virais.reset')
            pass
        st["in"], st["out"] = set(), set()
        st["shake"] = st["jitter"] = st["mblur"] = False
        self.render(entry)





CHAR_W = 0.62   

def est_width(text, size, aspect):
    """Largura estimada (normalizada em X) de uma linha de texto."""
    n = max(1, len(text))
    return n * size * CHAR_W * aspect


class Layouter(object):
    def __init__(self, animator):
        self.anim = animator
        self.cx = 0.5
        self.cy = 0.5
        self.gap = 1.0          
        self.width = 0.5        
        self.scale = 1.0        
        self.stair = 0.05       
        self.word_gap = 0.35    
        self.size_min = 0.001    
        self.size_max = 0.40
        self.hero_font = None      
        self.hero_color = HERO_COLOR
        self.small_font = DESIGN_FONT      
        self.small_color = SMALL_COLOR     
        self.tracking = DESIGN_TRACKING
        
        self.tracking_hero = DESIGN_TRACKING
        self.tracking_small = DESIGN_TRACKING

    def _fit(self, text, target, aspect):
        """Size que faz a largura estimada do texto bater com `target`."""
        w1 = est_width(text, 1.0, aspect)   
        sz = target / w1 if w1 else 0.08
        return max(self.size_min, min(self.size_max, sz))

    def _fit_real(self, entry, target, aspect):
        """Encaixe MEDIDO: seta Size, mede a largura real dos pixels renderizados
        e corrige até bater com `target`. Retorna (size, largura, altura)."""
        tool = entry["tool"]
        
        
        remove_modifier(tool, "Size")
        sz = self._fit(entry["text"], target, aspect)   
        w = h = None
        for _ in range(3):
            set_val(tool, "Size", sz)
            bb = measure_bbox(entry)
            if not bb or bb[0] <= 0:
                w = None
                break
            w, h = bb[0], bb[1]
            err = target / w
            if 0.985 <= err <= 1.015:
                break
            new_sz = max(self.size_min, min(self.size_max, sz * err))
            k = new_sz / sz if sz else 1.0
            w, h = w * k, h * k   
            sz = new_sz
        if w is None:   
            w = est_width(entry["text"], sz, aspect)
            h = sz * 0.75
        return sz, w, h

    def apply(self, entries, layout, aspect, hero_idx=None):
        if not entries:
            return
        n = len(entries)
        target = self.width * self.scale
        log("layout '%s': alvo=%.2f aspect=%.2f escala=%.2f heroi=%s" % (
            layout, target, aspect, self.scale, hero_idx))

        if layout.startswith("duo") and n >= 2:
            self._apply_duo(entries, target, aspect,
                            layout.endswith("_up"), hero_idx)
            return

        if layout.startswith(("badge", "cbadge")) and n >= 2:
            tuck = layout.startswith("badge")
            mode = ("up" if layout.endswith("_up")
                    else "down" if layout.endswith("_dn") else "auto")
            self._apply_badge(entries, target, aspect, tuck, mode, hero_idx)
            return

        
        
        
        heroi_unico = (len(entries) == 1 and hero_idx == 0)
        for e in entries:
            self._set_font(e, self.hero_font if heroi_unico else self.small_font,
                           self.tracking_hero if heroi_unico else self.tracking_small)
            if not heroi_unico:
                self._set_color(e, self.small_color)
        if heroi_unico and self.hero_font is not None:
            self._set_color(entries[0], self.hero_color)
        infos = [self._fit_real(e, target, aspect) for e in entries]
        line_h = [h * 1.12 * self.gap for (_, _, h) in infos]
        y = self.cy + sum(line_h) / 2.0
        for (sz, w, h), lh, e in zip(infos, line_h, entries):
            yc = y - lh / 2.0
            y -= lh
            self._place_dbg(e, self.cx, yc, sz)
        for e in entries:
            self._set_shadow(e)

    def _set_color(self, entry, rgb):
        tool, comp = entry["tool"], entry["comp"]
        comp.Lock()
        try:
            set_val(tool, "Red1", rgb[0])
            set_val(tool, "Green1", rgb[1])
            set_val(tool, "Blue1", rgb[2])
        finally:
            comp.Unlock()

    def _set_font(self, entry, font=None, trk=None):
        """font=None: NÃO mexe na fonte (só tracking + sombra off p/ medir).
        trk=None usa o tracking geral; senão o do papel (herói x apoio)."""
        tool, comp = entry["tool"], entry["comp"]
        comp.Lock()
        try:
            if font is not None:
                set_val(tool, "Font", font[0])
                set_val(tool, "Style", font[1])
            
            set_val(tool, "CharacterSpacing", self.tracking if trk is None else trk)
            
            set_val(tool, "Enabled3", 0)
        finally:
            comp.Unlock()

    def _set_shadow(self, entry):
        """Religa a sombra padrão DEPOIS da geometria (blur infla a medição)."""
        tool, comp = entry["tool"], entry["comp"]
        comp.Lock()
        try:
            set_val(tool, "Enabled3", 1)
            set_val(tool, "Offset3", {1: 0.083, 2: -0.045, 3: 0.0})
            set_val(tool, "SoftnessX3", 25.2)
            set_val(tool, "SoftnessY3", 25.51)
            set_val(tool, "Opacity3", 0.606)
        finally:
            comp.Unlock()

    def _measure_at_size(self, entry, sz, aspect):
        """Seta o Size e devolve (largura, altura) reais medidos."""
        tool = entry["tool"]
        remove_modifier(tool, "Size")
        set_val(tool, "Size", sz)
        bb = measure_bbox(entry)
        if bb:
            return bb[0], bb[1]
        return est_width(entry["text"], sz, aspect), sz * 0.75

    def _apply_badge(self, entries, target, aspect, tuck, mode, hero_idx=None):
        """Designs 'badge' (receita medida dos mockups do Bruno, Arial Bold):
        herói laranja encaixado na largura alvo; linhas menores brancas todas
        com o MESMO Size (22% do Size do herói), quase coladas.
        tuck=True: encostadas nas bordas esquerda (acima) / direita (abaixo);
        tuck=False: centralizadas.
        mode: 'auto' = ordem da timeline decide acima/abaixo;
        'up' = menores todas acima; 'down' = menores todas abaixo."""
        
        
        if self.hero_font is not None:
            hfont = self.hero_font
        else:
            try:
                cur = max(entries, key=lambda e: float(e["tool"].GetInput("Size") or 0))
                hfont = (str(cur["tool"].GetInput("Font") or DESIGN_FONT[0]),
                         str(cur["tool"].GetInput("Style") or DESIGN_FONT[1]))
            except Exception:
                _tv_diag.falha('Titulos Virais._apply_badge')
                hfont = DESIGN_FONT
        for e in entries:
            self._set_font(e, self.small_font, self.tracking_small)   
        
        
        n = len(entries)
        if hero_idx is not None and 0 <= hero_idx < n:
            hero_i = hero_idx
        elif mode == "up":
            hero_i = n - 1
        elif mode == "down":
            hero_i = 0
        else:
            hero_i = n // 2
        hero = entries[hero_i]
        others = [e for i, e in enumerate(entries) if i != hero_i]
        if mode == "up":
            above, below = others, []
        elif mode == "down":
            above, below = [], others
        else:
            above, below = entries[:hero_i], entries[hero_i + 1:]

        self._set_font(hero, hfont, self.tracking_hero)   
        hsz, hw, hh = self._fit_real(hero, target, aspect)
        left = self.cx - hw / 2.0
        right = self.cx + hw / 2.0

        self._set_color(hero, self.hero_color)
        self._place_dbg(hero, self.cx, self.cy, hsz)

        small_sz = max(hsz * SMALL_SIZE_FRAC, min(SMALL_SIZE_MIN * self.scale * min(1.0, target / 0.6), hsz * 0.35))
        
        
        
        smalls = above + below
        if smalls:
            drive = max(smalls, key=lambda e: len(e["text"]))
            w0, h0 = self._measure_at_size(drive, 0.1, aspect)
            if w0 > 0:
                sz_w = 0.1 * (hw * 0.62) / w0
                small_sz = max(small_sz, min(sz_w, hsz * 0.35))
        
        y = self.cy + hh / 2.0
        for e in reversed(above):
            w, h = self._measure_at_size(e, small_sz, aspect)
            self._set_color(e, self.small_color)
            pad = h * 0.15 * self.gap
            xc = (left + w / 2.0) if tuck else self.cx
            self._place_dbg(e, xc, y + pad + h / 2.0, small_sz)
            y += pad + h
        
        y = self.cy - hh / 2.0
        for e in below:
            w, h = self._measure_at_size(e, small_sz, aspect)
            self._set_color(e, self.small_color)
            pad = h * 0.30 * self.gap
            xc = (right - w / 2.0) if tuck else self.cx
            self._place_dbg(e, xc, y - pad - h / 2.0, small_sz)
            y -= pad + h
        for e in entries:
            self._set_shadow(e)

    def _apply_duo(self, entries, target, aspect, acima, hero_idx=None):
        """Modelos novos (medidos nos mockups do Bruno, 29/08): herói cheio e
        as menores LADO A LADO numa única fila — a primeira encostada na
        borda esquerda do herói, a última na direita.
        acima=True: fila em cima do herói; False: embaixo."""
        if self.hero_font is not None:
            hfont = self.hero_font
        else:
            try:
                cur = max(entries, key=lambda e: float(e["tool"].GetInput("Size") or 0))
                hfont = (str(cur["tool"].GetInput("Font") or DESIGN_FONT[0]),
                         str(cur["tool"].GetInput("Style") or DESIGN_FONT[1]))
            except Exception:
                _tv_diag.falha('Titulos Virais._apply_duo')
                hfont = DESIGN_FONT
        for e in entries:
            self._set_font(e, self.small_font, self.tracking_small)
        n = len(entries)
        if hero_idx is not None and 0 <= hero_idx < n:
            hero_i = hero_idx
        else:
            hero_i = n - 1 if acima else 0      
        hero = entries[hero_i]
        smalls = [e for i, e in enumerate(entries) if i != hero_i]

        self._set_font(hero, hfont, self.tracking_hero)
        hsz, hw, hh = self._fit_real(hero, target, aspect)
        self._set_color(hero, self.hero_color)
        self._place_dbg(hero, self.cx, self.cy, hsz)
        
        
        bb = measure_bbox(hero)
        if bb:
            hw, hh = bb[0], bb[1]
        left, right = self.cx - hw / 2.0, self.cx + hw / 2.0
        if not smalls:
            self._set_shadow(hero)
            return

        
        small_sz = max(hsz * 0.35, min(SMALL_SIZE_MIN * self.scale * min(1.0, target / 0.6), hsz * 0.35))
        med = [self._measure_at_size(e, small_sz, aspect) for e in smalls]
        larg = sum(w for w, _h in med)
        folga = hw * 0.06 * max(0, len(smalls) - 1)
        if larg + folga > hw and larg > 0:
            small_sz *= (hw - folga) / larg
            med = [self._measure_at_size(e, small_sz, aspect) for e in smalls]

        
        
        
        
        
        h_fila = max(h for _w, h in med)
        pad = h_fila * 0.20 * self.gap
        k = len(smalls)
        alvo_x = []
        for i, (w, _h) in enumerate(med):
            if k == 1:
                alvo_x.append(("c", self.cx))
            elif i == 0:
                alvo_x.append(("l", left))
            elif i == k - 1:
                alvo_x.append(("r", right))
            else:
                alvo_x.append(("c", left + (right - left) * (i / float(k - 1))))
        yc = (self.cy + hh / 2.0 + pad + h_fila / 2.0) if acima else             (self.cy - hh / 2.0 - pad - h_fila / 2.0)
        for i, e in enumerate(smalls):
            self._set_color(e, self.small_color)
            w = med[i][0]
            x0 = {"l": left + w / 2.0, "r": right - w / 2.0}.get(alvo_x[i][0],
                                                                alvo_x[i][1])
            self._place(e, x0, yc, small_sz, 1)

        
        
        bbs = [measure_bbox(e) for e in smalls]
        if all(bbs):
            topo = max(b[3] + b[1] / 2.0 for b in bbs)
            base = min(b[3] - b[1] / 2.0 for b in bbs)
            alvo = (self.cy + hh / 2.0 + pad) if acima else (self.cy - hh / 2.0 - pad)
            dy = (alvo - base) if acima else (alvo - topo)
            if abs(dy) > 0.0005:
                yc += dy
                for i, e in enumerate(smalls):
                    b = bbs[i]
                    self._place(e, b[2], yc, small_sz, 1)
                bbs = [measure_bbox(e) for e in smalls]

        
        for i, e in enumerate(smalls):
            b = bbs[i] if bbs and bbs[i] else measure_bbox(e)
            if not b:
                continue
            modo, val = alvo_x[i]
            if modo == "l":
                dx = left - (b[2] - b[0] / 2.0)
            elif modo == "r":
                dx = right - (b[2] + b[0] / 2.0)
            else:
                dx = val - b[2]
            if abs(dx) > 0.0005:
                self._place(e, b[2] + dx, yc, small_sz, 1)
        for e in entries:
            self._set_shadow(e)

    def _place_dbg(self, e, xc, yc, sz):
        self._place(e, xc, yc, sz, 1)
        
        
        tx, ty = xc, yc
        bb = None
        for _ in range(2):
            bb = measure_bbox(e)
            if not bb:
                break
            dx, dy = xc - bb[2], yc - bb[3]
            if abs(dx) <= 0.0015 and abs(dy) <= 0.0015:
                break
            tx, ty = tx + dx, ty + dy
            self._place(e, tx, ty, sz, 1)
        
        try:
            real_sz = e["tool"].GetInput("Size")
            log("  '%s': Size pedido=%.3f lido=%s  alvo=(%.2f,%.2f) caixa=%s"
                % (e["text"], sz, real_sz, xc, yc,
                   "(%.2f,%.2f)" % (bb[2], bb[3]) if bb else "sem medida"))
        except Exception as ex:
            _tv_diag.falha('Titulos Virais._place_dbg')
            log("  '%s': leitura de verificação falhou: %s" % (e["text"], ex))

    def _place(self, entry, x, y, size, hjust):
        tool, comp = entry["tool"], entry["comp"]
        self.anim.set_base(entry, center=(x, y), size=size)
        comp.Lock()
        try:
            set_val(tool, "HorizontalJustificationNew", hjust)   
            set_val(tool, "VerticalJustificationNew", 1)
        finally:
            comp.Unlock()
        
        self.anim.render(entry)





COLORS = [
    ("Branco", (1.0, 1.0, 1.0)),
    ("Azul Metálico", (0.22, 0.74, 0.97)),
    ("Azul Cobalto", (0.14, 0.39, 0.92)),
    ("Ciano Elétrico", (0.0, 0.95, 1.0)),
    ("Amarelo Ouro", (1.0, 0.85, 0.1)),
    ("Verde Neon", (0.1, 0.95, 0.55)),
    ("Roxo Titânio", (0.65, 0.35, 1.0)),
    ("Rosa Choque", (1.0, 0.25, 0.65)),
    ("Vermelho", (0.95, 0.25, 0.25)),
]

LAYOUTS = [
    ("badge", "Badge 3"),          
    ("badge_up", "Badge ↑"),       
    ("badge_dn", "Badge ↓"),       
    ("cbadge", "Central 3"),       
    ("cbadge_up", "Central ↑"),    
    ("cbadge_dn", "Central ↓"),    
    ("duo_up", "Duplo ↑"),         
    ("duo_dn", "Duplo ↓"),         
    ("center", "Centro"),          
]


GEN_LAY_MAX = 3
GEN_LAY_DEF = ["badge"]




HERO_POS = {
    "badge": "meio", "cbadge": "meio",
    "badge_up": "fim", "cbadge_up": "fim", "duo_up": "fim",
    "badge_dn": "ini", "cbadge_dn": "ini", "duo_dn": "ini",
    "center": None,
}



HERO_MAX_PALAVRAS = 2



HERO_MIN_CHARS = 5          
LINHA_LONGA = 26            
LAY_IRMAO_3 = {"badge_up": "badge", "badge_dn": "badge",
               "cbadge_up": "cbadge", "cbadge_dn": "cbadge"}


LAY_AUTO = [k for k, _ in LAYOUTS[:-1]]
LAY_LINHAS = {
    "badge": 3, "badge_up": 2, "badge_dn": 2,
    "cbadge": 3, "cbadge_up": 2, "cbadge_dn": 2,
    "duo_up": 3, "duo_dn": 3, "center": 3,
}

HERO_COLOR = (0.22, 0.74, 0.97)   
SMALL_COLOR = (1.0, 1.0, 1.0)
DESIGN_FONT = ("Arial", "Regular")   

FONTS_DESTAQUE = [
    ("Arial Regular", ("Arial", "Regular")),
    ("Arial Bold", ("Arial", "Bold")),
    ("Apple Garamond Italic", ("Apple Garamond", "Italic")),
    ("AwesomeSerif Italic", ("Awesome Serif Italic", "Semi Bold Regular")),
    ("Inter Black", ("Inter", "Black")),
    ("Barlow Cond SemiBold It.", ("Barlow Condensed", "SemiBold Italic")),
    ("Bebas Neue", ("Bebas Neue", "Regular")),
]


FONTS_BLOQUEIO = {"atakana sarif", "atakana script"}
_FONTE_SIMBOLO = ("symbol", "dingbat", "wingding", "webding", "emoji", "icons",
                  "ornament", "brush script mt", "marlett", "bodoni ornaments",
                  "apple color emoji", "apple symbols", "zapf dingbats",
                  "keyboard", "notoemoji", "notosans symbols")


def _fonte_de_texto(fam):
    f = fam.lower()
    if f in FONTS_BLOQUEIO or fam.startswith("."):
        return False
    return not any(s in f for s in _FONTE_SIMBOLO)


def _nome_da_fonte(caminho):
    """(família, estilo) de um .ttf/.otf/.ttc lendo a tabela 'name' na mão — sem
    PIL (o Resolve não tem). Prefere o nome tipográfico (16/17) ao legado (1/2),
    igual o que o CapCut mostra."""
    import struct
    with open(caminho, "rb") as f:
        data = f.read(200000)          
    tag0 = data[:4]
    if tag0 == b"ttcf":                
        base = struct.unpack(">I", data[12:16])[0]
    elif tag0 in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"):
        base = 0
    else:
        return None
    num = struct.unpack(">H", data[base + 4:base + 6])[0]
    name_off = None
    for i in range(num):
        rec = base + 12 + i * 16
        if data[rec:rec + 4] == b"name":
            name_off = struct.unpack(">I", data[rec + 8:rec + 12])[0]
            break
    if name_off is None:
        return None
    if len(data) < name_off + 6:
        with open(caminho, "rb") as f:
            data = f.read()
    count = struct.unpack(">H", data[name_off + 2:name_off + 4])[0]
    stor = name_off + struct.unpack(">H", data[name_off + 4:name_off + 6])[0]
    fam = sub = tfam = tsub = None
    for i in range(count):
        rec = name_off + 6 + i * 12
        pid, eid, lid, nid, ln, so = struct.unpack(">HHHHHH", data[rec:rec + 12])
        raw = data[stor + so:stor + so + ln]
        try:
            txt = raw.decode("utf-16-be" if pid in (0, 3) else "latin-1", "ignore").strip()
        except Exception:
            _tv_diag.falha('Titulos Virais._nome_da_fonte')
            continue
        if not txt:
            continue
        if nid == 1 and not fam:
            fam = txt
        elif nid == 2 and not sub:
            sub = txt
        elif nid == 16 and not tfam:
            tfam = txt
        elif nid == 17 and not tsub:
            tsub = txt
    familia = tfam or fam
    return (familia, tsub or sub or "Regular") if familia else None


def _pastas_de_fonte():
    if sys.platform == "darwin":
        return [os.path.expanduser("~/Library/Fonts"), "/Library/Fonts",
                "/System/Library/Fonts", "/System/Library/Fonts/Supplemental"]
    if sys.platform.startswith("win"):
        win = os.environ.get("WINDIR", "C:\\Windows")
        return [os.path.join(win, "Fonts"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""),
                             "Microsoft", "Windows", "Fonts")]
    return ["/usr/share/fonts", os.path.expanduser("~/.fonts")]


def _montar_fontes():
    """Mesma lista do CapCut: varre as fontes do sistema. Destaques primeiro, o
    resto por família (uma entrada por família). Se a varredura falhar, cai nos
    destaques (nunca fica sem lista)."""
    import glob
    fam_est = {}
    try:
        for pasta in _pastas_de_fonte():
            if not pasta or not os.path.isdir(pasta):
                continue
            for f in glob.glob(os.path.join(pasta, "*")):
                if not f.lower().endswith((".ttf", ".otf", ".ttc")):
                    continue
                try:
                    r = _nome_da_fonte(f)
                except Exception:
                    _tv_diag.falha('Titulos Virais._montar_fontes')
                    r = None
                if r:
                    fam_est.setdefault(r[0], set()).add(r[1])
    except Exception:
        _tv_diag.falha('Titulos Virais._montar_fontes')
        fam_est = {}
    if not fam_est:
        return list(FONTS_DESTAQUE)
    
    
    
    global FAM_EST
    FAM_EST = dict((f, sorted(s, key=lambda x: x.lower())) for f, s in fam_est.items())
    for _n, (f, s) in FONTS_DESTAQUE:      
        cur = set(FAM_EST.get(f, []))
        cur.add(s)
        FAM_EST[f] = sorted(cur, key=lambda x: x.lower())
    ja = set((f, s) for _, (f, s) in FONTS_DESTAQUE)
    lista = list(FONTS_DESTAQUE)
    for fam in sorted(fam_est, key=lambda x: x.lower()):
        if not _fonte_de_texto(fam):
            continue
        ests = fam_est[fam]
        est = "Regular" if "Regular" in ests else sorted(ests)[0]
        if (fam, est) in ja:
            continue
        lista.append((fam, (fam, est)))
    return lista


FAM_EST = {}                      
FONTS = _montar_fontes()
FONTS_SEC = [i for i, (n, _) in enumerate(FONTS)]
HERO_FONTS = FONTS                
FONT_MAIN_DEF = 1                 
FONT_SEC_DEF = 0                  





def _achar_programa(nomes, extras=()):
    """Procura um executável no PATH e nos lugares onde ele costuma morar."""
    import shutil
    for n in nomes:
        achado = shutil.which(n)
        if achado:
            return achado
    for c in extras:
        c = os.path.expanduser(c)
        if os.path.exists(c):
            return c
    return None


def _achar_arquivo(caminhos):
    for c in caminhos:
        c = os.path.expanduser(c)
        if os.path.exists(c):
            return c
    return None


def _pasta_motor():
    """Onde o motor de transcrição fica instalado, por usuário."""
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.path.expanduser("~/.local/share")
    return os.path.join(base, "TitulosVirais", "motor")


MOTOR_DIR = _pasta_motor()


MODELO_URL = ("https://github.com/Bradson1988/tv-motor/releases/download/v1/"
              "ggml-small.bin")
MODELO_MB = 465          

WHISPER_BIN = _achar_programa(
    ["whisper-cli"],
    [os.path.join(MOTOR_DIR, "whisper-cli.exe"),
     os.path.join(MOTOR_DIR, "whisper-cli"),
     "/opt/homebrew/bin/whisper-cli", "/usr/local/bin/whisper-cli"]) or ""
WHISPER_MODEL = _achar_arquivo([
    os.path.join(MOTOR_DIR, "ggml-small.bin"),
    "~/Documents/LEGENDAS VIRAIS CAPCUT/models/ggml-small.bin",
]) or ""
TEMPLATE_DRB = _achar_arquivo([
    os.path.join(RESOURCE_DIR, "caption-bin.drb"),
    _CAPTION_BIN_PATH,
    os.path.join(SCRIPT_DIR, "caption-bin.drb"),
    "~/Library/Application Support/Blackmagic Design/DaVinci Resolve/"
    "Fusion/Scripts/Utility/AutoSubs/caption-bin.drb",
    "~/AppData/Roaming/Blackmagic Design/DaVinci Resolve/Support/"
    "Fusion/Scripts/Utility/AutoSubs/caption-bin.drb",
]) or ""


def intervalo_geracao(tl):
    """Intervalo absoluto semiaberto; os dois tipos de marca restringem a área."""
    inicio, fim = int(tl.GetStartFrame()), int(tl.GetEndFrame()) + 1
    marks = tl.GetMarkInOut()
    if not isinstance(marks, dict):
        raise ValueError("Não foi possível conferir os limites I/O.")
    intervalos = []
    for tipo in ("video", "audio"):
        selecao = marks.get(tipo, {})
        if not isinstance(selecao, dict):
            raise ValueError("Não foi possível conferir os limites I/O.")
        if not any(k in selecao for k in ("in", "out")):
            continue
        a = inicio + int(selecao.get("in", 0))
        b = inicio + int(selecao["out"]) + 1 if "out" in selecao else fim
        intervalos.append((max(inicio, a), min(fim, b)))
    if not intervalos:
        return inicio, fim, False
    a, b = max(x[0] for x in intervalos), min(x[1] for x in intervalos)
    if b <= a:
        raise ValueError("Intervalo I/O inválido ou sem interseção entre áudio e vídeo.")
    return a, b, True


def palavras_no_intervalo(words, inicio, fim, fps):
    a, b = inicio * 1000.0 / fps, fim * 1000.0 / fps
    return [dict(w, a=max(a, w["a"]), b=min(b, max(w["a"], w["b"])))
            for w in words if a - 1e-6 <= w["a"] < b - 1e-6
            or w["a"] < a - 1e-6 and w["b"] > a + 1e-6]


def render_audio_timeline(proj, tl, aviso=None, intervalo=None):
    """Tira o áudio da timeline pelo próprio Resolve (preset 'Audio Only').
    Devolve o caminho do .wav ou None.

    Três cuidados aprendidos na marra:
      - o Resolve PULA para a aba Deliver ao renderizar; voltamos para a aba
        onde o usuário estava assim que termina;
      - o laço de espera tem que rodar o StepLoop, senão a janela do plugin
        congela e parece travada;
      - as configurações de render do projeto são devolvidas como estavam."""
    import tempfile as _tf
    import time as _time
    pagina = None
    try:
        pagina = resolve.GetCurrentPage()
    except Exception:
        _tv_diag.falha('Titulos Virais.render_audio_timeline')
        pass
    guardado = {}
    for k in ("targetDir", "customName"):
        try:
            guardado[k] = proj.GetSetting(k)
        except Exception:
            _tv_diag.falha('Titulos Virais.render_audio_timeline')
            pass
    pasta = _tf.mkdtemp(prefix="tv_audio_")
    job = None
    try:
        proj.LoadRenderPreset("Audio Only")
        settings = {
            "TargetDir": pasta, "CustomName": "tv_audio",
            "SelectAllFrames": True, "ExportVideo": False, "ExportAudio": True,
            "AudioBitDepth": 16, "AudioSampleRate": 48000,
        }
        if intervalo is not None:
            settings.update(SelectAllFrames=False, MarkIn=int(intervalo[0]), MarkOut=int(intervalo[1]) - 1)
        if not proj.SetRenderSettings(settings):
            raise RuntimeError("Falha ao definir intervalo de render.")
        job = proj.AddRenderJob()
        if not job:
            log("render de áudio: AddRenderJob não devolveu id")
            return None
        if intervalo is not None:
            jobs = proj.GetRenderJobList() or []
            dados = next((x for x in jobs if x.get("JobId") == job), None)
            if not dados or (int(dados.get("MarkIn", -1)), int(dados.get("MarkOut", -1))) != (int(intervalo[0]), int(intervalo[1]) - 1):
                raise RuntimeError("O Resolve não confirmou o intervalo I/O do render; geração cancelada para proteger a timeline.")
        if not proj.StartRendering([job], isInteractiveMode=False):
            raise RuntimeError("O Resolve não iniciou o render de áudio.")
        t0 = _time.time()
        parado = 0.0
        ultimo = -1
        while proj.IsRenderingInProgress() and _time.time() - t0 < 3600:
            pct = -1
            try:
                st = proj.GetRenderJobStatus(job) or {}
                pct = int(st.get("CompletionPercentage", -1))
                situacao = str(st.get("JobStatus", ""))
                if situacao in ("Failed", "Cancelled"):
                    log("render de áudio %s: %s"
                        % (situacao, st.get("Error", "sem detalhe")))
                    break
            except Exception:
                _tv_diag.falha('Titulos Virais.render_audio_timeline')
                pass
            if aviso:
                aviso(pct)
            
            for _ in range(2):
                try:
                    disp.StepLoop()
                except Exception:
                    _tv_diag.falha('Titulos Virais.render_audio_timeline')
                    break
            if pct >= 0 and pct == ultimo:
                parado += 0.4
            else:
                parado = 0.0
                ultimo = pct
            if parado > 300:          
                log("render de áudio empacou em %d%%" % pct)
                try:
                    proj.StopRendering()
                except Exception:
                    _tv_diag.falha('Titulos Virais.render_audio_timeline')
                    pass
                break
            _time.sleep(0.4)
        for nome in sorted(os.listdir(pasta)):
            if nome.lower().endswith(".wav"):
                return os.path.join(pasta, nome)
        log("render de áudio: nenhum wav em %s (a timeline tem áudio?)" % pasta)
        return None
    except Exception as ex:
        _tv_diag.falha('Titulos Virais.render_audio_timeline')
        log("render de áudio:", ex)
        return None
    finally:
        try:
            if job:
                proj.DeleteRenderJob(job)
        except Exception:
            _tv_diag.falha('Titulos Virais.render_audio_timeline')
            pass
        for k, v in guardado.items():
            try:
                proj.SetSetting(k, v)
            except Exception:
                _tv_diag.falha('Titulos Virais.render_audio_timeline')
                pass
        if pagina:                     
            try:
                resolve.OpenPage(pagina)
            except Exception:
                _tv_diag.falha('Titulos Virais.render_audio_timeline')
                pass


def _ler_wav_qualquer(entrada):
    """(canais, taxa, amostras_int16_intercaladas) de QUALQUER WAV — 16/24/32-bit
    int ou 32-bit float, inclusive WAVE_FORMAT_EXTENSIBLE. Lê os chunks na mão
    porque o Resolve exporta em profundidades variadas (não só 16-bit) e o módulo
    `wave` nem lê float. Sem ffmpeg, sem audioop."""
    import struct
    import array
    with open(entrada, "rb") as f:
        buf = f.read()
    if buf[:4] != b"RIFF" or buf[8:12] != b"WAVE":
        raise ValueError("não é um WAV")
    formato = canais = taxa = bits = None
    pcm = None
    i = 12
    while i + 8 <= len(buf):
        cid = buf[i:i + 4]
        tam = struct.unpack("<I", buf[i + 4:i + 8])[0]
        corpo = buf[i + 8:i + 8 + tam]
        if cid == b"fmt " and len(corpo) >= 16:
            formato, canais, taxa, _br, _ba, bits = struct.unpack("<HHIIHH", corpo[:16])
            if formato == 0xFFFE and len(corpo) >= 26:      
                formato = struct.unpack("<H", corpo[24:26])[0]
            elif formato == 0xFFFE:
                formato = 1
        elif cid == b"data":
            pcm = corpo
        i += 8 + tam + (tam & 1)                            
    if not bits or pcm is None:
        raise ValueError("WAV sem fmt/data")
    
    if bits == 16 and formato == 1:
        a = array.array("h")
        a.frombytes(pcm[:len(pcm) - (len(pcm) % 2)])
        if sys.byteorder == "big":
            a.byteswap()
    elif bits == 32 and formato == 3:                        
        fa = array.array("f")
        fa.frombytes(pcm[:len(pcm) - (len(pcm) % 4)])
        if sys.byteorder == "big":
            fa.byteswap()
        a = array.array("h", (int(max(-1.0, min(1.0, x)) * 32767) for x in fa))
    elif bits == 32 and formato == 1:                        
        ia = array.array("i")
        ia.frombytes(pcm[:len(pcm) - (len(pcm) % 4)])
        if sys.byteorder == "big":
            ia.byteswap()
        a = array.array("h", (x >> 16 for x in ia))
    elif bits == 24:                                         
        a = array.array("h")
        for p in range(0, len(pcm) - 2, 3):
            v = pcm[p] | (pcm[p + 1] << 8) | (pcm[p + 2] << 16)
            if v & 0x800000:
                v -= 1 << 24
            a.append(v >> 8)
    elif bits == 8:                                          
        a = array.array("h", ((b - 128) << 8 for b in pcm))
    else:
        raise ValueError("formato de áudio não suportado: %d bits, fmt %s"
                         % (bits, formato))
    return canais, taxa, a


def wav_para_16k_mono(entrada, saida, alvo=16000):
    """Qualquer WAV do Resolve -> 16 kHz mono 16-bit (o que o Whisper quer). Só
    biblioteca padrão: nada de ffmpeg, e sem audioop (sumiu no Python 3.13)."""
    import wave
    import array
    canais, taxa, a = _ler_wav_qualquer(entrada)
    if canais and canais > 1:
        separados = [a[c::canais] for c in range(canais)]
        m = array.array("h", bytes(len(a) // canais * 2))
        for c in range(canais):
            parte = separados[c]
            if c == 0:
                for i, v in enumerate(parte):
                    m[i] = v // canais
            else:
                for i, v in enumerate(parte):
                    m[i] += v // canais
        
        
        
        energia_mix = sum(int(v) * int(v) for v in m)
        energias = [sum(int(v) * int(v) for v in parte) for parte in separados]
        maior = max(energias) if energias else 0
        if maior and energia_mix * 20 < maior:  
            m = array.array("h", separados[energias.index(maior)])
        a = m
    passo = max(1, int(round(taxa / float(alvo))))
    if passo > 1:
        a = a[::passo]
        taxa = taxa // passo
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa)
        w.writeframes(a.tobytes())
    return taxa


def _baixar(url, destino, aviso=None, minimo=0):
    """Baixa mostrando progresso. Grava num .parcial e só renomeia no fim —
    download interrompido não deixa arquivo quebrado para trás."""
    import urllib.request
    parcial = destino + ".parcial"
    try:
        req = urllib.request.Request(
            url, headers={"user-agent": "TitulosVirais/%s" % APP_VERSION})
        with urllib.request.urlopen(req, timeout=60) as r:
            total = int(r.headers.get("content-length") or 0)
            feito = 0
            marco = 0
            with open(parcial, "wb") as f:
                while True:
                    pedaco = r.read(1024 * 256)
                    if not pedaco:
                        break
                    f.write(pedaco)
                    feito += len(pedaco)
                    if aviso and total and feito - marco > total / 50.0:
                        marco = feito
                        aviso(feito / float(total), feito, total)
        if minimo and os.path.getsize(parcial) < minimo:
            raise IOError("arquivo veio menor que o esperado")
        if os.path.exists(destino):
            os.remove(destino)
        os.rename(parcial, destino)
        return True
    except Exception as ex:
        _tv_diag.falha('Titulos Virais._baixar')
        log("download de %s:" % os.path.basename(destino), ex)
        try:
            os.remove(parcial)
        except Exception:
            _tv_diag.falha('Titulos Virais._baixar')
            pass
        return False


def instalar_motor(aviso=None):
    """Baixa o motor de transcrição (whisper + modelo) na primeira vez.
    Devolve (ok, mensagem). O plugin não embute isso porque são ~470 MB."""
    import zipfile
    global WHISPER_BIN, WHISPER_MODEL
    try:
        if not os.path.isdir(MOTOR_DIR):
            os.makedirs(MOTOR_DIR)
    except Exception as ex:
        _tv_diag.falha('Titulos Virais.instalar_motor')
        return False, "Não consegui criar a pasta do motor: %s" % ex

    exe = os.path.join(MOTOR_DIR,
                       "whisper-cli.exe" if sys.platform.startswith("win")
                       else "whisper-cli")
    def _binarios_ok():
        if not sys.platform.startswith("win"):
            return os.path.isfile(exe)
        marcador = os.path.join(MOTOR_DIR, "motor-static.json")
        if os.path.isfile(marcador):
            try:
                import hashlib, json
                with open(marcador, encoding="utf-8") as f:
                    esperado = json.load(f)["sha256"]
                with open(exe, "rb") as f:
                    return hashlib.sha256(f.read()).hexdigest() == esperado
            except Exception:
                _tv_diag.falha('Titulos Virais.instalar_motor._binarios_ok')
                return False
        obrigatorios = ("whisper-cli.exe", "whisper.dll", "ggml.dll",
                        "ggml-base.dll", "ggml-cpu-x64.dll")
        return all(os.path.isfile(os.path.join(MOTOR_DIR, nome))
                   and os.path.getsize(os.path.join(MOTOR_DIR, nome)) > 1024
                   for nome in obrigatorios)
    if not _binarios_ok():
        if sys.platform.startswith("win"):
            return False, "Motor ausente ou alterado. Reinstale o pacote completo do Títulos Virais."
        nome = "whisper-windows.zip" if sys.platform.startswith("win")            else "whisper-macos.zip"
        zp = os.path.join(MOTOR_DIR, nome)
        if aviso:
            aviso(0.0, 0, 0, "Baixando o motor de transcrição…")
        if not _baixar(LICENCA_API.rstrip("/") + "/motor/" + nome, zp,
                       lambda f, a, t: aviso and aviso(f * 0.05, a, t,
                                                       "Baixando o motor…"),
                       minimo=500000):
            return False, "Não consegui baixar o motor. Confira a internet."
        try:
            with zipfile.ZipFile(zp) as z:
                z.extractall(MOTOR_DIR)
            os.remove(zp)
        except Exception as ex:
            _tv_diag.falha('Titulos Virais.instalar_motor')
            return False, "Não consegui abrir o pacote do motor: %s" % ex
        
        alt = os.path.join(MOTOR_DIR, "motor-macos")
        if os.path.exists(alt) and not os.path.exists(exe):
            os.rename(alt, exe)
        try:
            os.chmod(exe, 0o755)
        except Exception:
            _tv_diag.falha('Titulos Virais.instalar_motor')
            pass
    if not _binarios_ok():
        if sys.platform.startswith("win"):
            return False, "Motor ausente ou alterado. Reinstale o pacote completo do Títulos Virais."
        return False, "O motor não ficou instalado."

    modelo = os.path.join(MOTOR_DIR, "ggml-small.bin")
    if not os.path.exists(modelo):
        if aviso:
            aviso(0.06, 0, 0, "Baixando o modelo de transcrição (%d MB)…" % MODELO_MB)
        if not _baixar(MODELO_URL, modelo,
                       lambda f, a, t: aviso and aviso(
                           0.06 + f * 0.9, a, t,
                           "Baixando o modelo… %d%% (%d de %d MB)"
                           % (int(f * 100), a // 1000000, t // 1000000)),
                       minimo=100 * 1000 * 1000):
            return False, "Não consegui baixar o modelo. Confira a internet."

    WHISPER_BIN, WHISPER_MODEL = exe, modelo
    return True, "Motor instalado."


def checar_dependencias():
    """Devolve a lista do que está faltando para gerar legenda, em português.
    Sem isso o plugin morria com um erro do sistema no meio da geração."""
    falta = []
    if not (WHISPER_BIN and os.path.exists(WHISPER_BIN)):
        falta.append("Whisper")
    if not (WHISPER_MODEL and os.path.exists(WHISPER_MODEL)):
        falta.append("modelo de transcrição")
    if not TEMPLATE_DRB:
        falta.append("template de legenda")
    return falta



TEMPLATE_NAME = "Basic Template"
GEN_GAP_MS = 600        
GEN_BLOCK_CHARS = 32    
LINHA_CHARS_REF = 14    
GEN_PAD_MS = 150        
GEN_MAX_PALAVRAS = 6    












_FIM_FRASE = ".,;:!?…"   


def _cj(s):
    return set(s.split())




REGRAS_IDIOMA = {
    "pt": {
        "liga": _cj("de do da dos das e ou o a os as um uma uns umas que com para pra "
                    "por no na nos nas em ao aos se seu sua seus suas meu minha teu tua "
                    "num numa nesse nessa neste nesta desse dessa deste desta "
                    "é são era foi vai está tá ser"),
        "extra": _cj("esse essa esses essas este esta estes estas isso isto aquele "
                     "aquela aquilo aqueles aquelas mesmo mesma tudo todo toda todos "
                     "todas nada algo alguém quando onde como porque porquê enquanto "
                     "então portanto assim aqui ali lá aí muito muita muitos muitas "
                     "mais menos já ainda também só apenas talvez quase sim quê qual "
                     "quais quanto quanta quantos quantas cada"),
        "adj": ("oso", "osa", "osos", "osas", "ável", "ível", "áveis", "íveis", "ado",
                "ada", "ados", "adas", "ido", "ida", "idos", "idas", "al", "ais",
                "ante", "ente", "antes", "entes", "ivo", "iva", "ivos", "ivas",
                "inho", "inha", "íssimo", "íssima"),
        "verbo": ("ando", "endo", "indo", "ar", "er", "ir", "ou", "aram", "eram",
                  "iram", "ará", "erá", "irá", "aria", "eria", "iria", "asse", "esse",
                  "isse", "amos", "emos", "imos", "ava", "avam", "ram"),
    },
    "en": {
        "liga": _cj("the a an of to in on at by for with from as into onto over under "
                    "and or but nor so yet if then than that this these those it its "
                    "i you he she we they me him her us them my your his our their "
                    "is are was were be been being am has have had do does did will "
                    "would can could should may might must shall about up out off"),
        "extra": _cj("here there when where how why very more most just also only "
                     "really quite too now then always never each all some any no not "
                     "what which who whom whose"),
        "adj": ("ous", "ful", "ive", "able", "ible", "ic", "ical", "less", "ish",
                "ary", "ory", "ant", "ent", "al"),
        "verbo": ("ing", "ize", "ise", "ate", "ify", "ed"),
    },
    "es": {
        "liga": _cj("el la los las un una unos unas de del al a y e o u que con para "
                    "por en su sus mi mis tu tus se lo le les me te nos os yo tú él "
                    "ella ellos ellas es son era fue va está ser como pero si no "
                    "más menos"),
        "extra": _cj("este esta estos estas ese esa esos esas aquel aquella aquello "
                     "esto eso aquí allí cuando donde cómo porque muy ya también solo "
                     "sólo cada todo toda todos todas nada algo alguien qué cuál "
                     "cuáles cuánto cuánta"),
        "adj": ("oso", "osa", "osos", "osas", "able", "ible", "al", "ico", "ica",
                "ivo", "iva", "ante", "ente", "ado", "ada", "ido", "ida"),
        "verbo": ("ando", "iendo", "ar", "er", "ir", "ó", "aron", "ará", "aría",
                  "ase", "iese", "amos", "emos", "imos", "aba", "aban"),
    },
    "de": {
        "liga": _cj("der die das den dem des ein eine einen einem einer eines und oder "
                    "aber für mit von zu zum zur im in an auf aus bei nach über unter "
                    "ist sind war waren sein ich du er sie es wir ihr mich dich sich "
                    "mein dein als dass wenn"),
        "extra": _cj("hier da dort wann wo wie warum sehr mehr nur auch schon noch "
                     "immer nie jeder alle etwas nichts was welche"),
        "adj": ("lich", "ig", "isch", "bar", "sam", "haft", "los", "voll"),
        "verbo": ("en", "st", "et", "te", "ten"),
    },
    "fr": {
        "liga": _cj("le la les un une des de du au aux à et ou mais donc car ni or "
                    "dans sur sous par pour avec sans que qui je tu il elle nous vous "
                    "ils elles me te se mon ma mes ton ta est sont était être ce cet "
                    "cette ces son sa ses"),
        "extra": _cj("ici là quand où comment pourquoi très plus moins déjà aussi "
                     "seulement encore toujours jamais chaque tout toute tous toutes "
                     "rien quoi quel quelle"),
        "adj": ("eux", "euse", "if", "ive", "able", "ible", "al", "ique", "ant",
                "ent", "é", "ée", "és", "ées"),
        "verbo": ("er", "ir", "re", "ant", "é", "ée", "ons", "ez", "ait", "aient"),
    },
    "it": {
        "liga": _cj("il lo la i gli le un uno una di del della dei delle a al alla e "
                    "ed o ma però quindi per con senza che chi io tu lui lei noi voi "
                    "loro mi ti si mio mia è sono era essere questo questa in su tra fra"),
        "extra": _cj("qui là quando dove come perché molto più meno già anche solo "
                     "ancora sempre mai ogni tutto tutta tutti tutte niente cosa "
                     "quale quali"),
        "adj": ("oso", "osa", "ivo", "iva", "abile", "ibile", "ale", "ico", "ica",
                "ante", "ente", "ato", "ata", "ito", "ita"),
        "verbo": ("are", "ere", "ire", "ando", "endo", "ò", "ato", "ito", "iamo",
                  "ano", "ava", "avano"),
    },
}
for _r in REGRAS_IDIOMA.values():
    _r["nao_heroi"] = _r["liga"] | _r["extra"]

_IDIOMA = ["pt"]


def _definir_idioma(idi):
    _IDIOMA[0] = idi if idi in REGRAS_IDIOMA else "pt"


def _regras():
    return REGRAS_IDIOMA.get(_IDIOMA[0], REGRAS_IDIOMA["pt"])


LIGA = REGRAS_IDIOMA["pt"]["liga"]          


def _classe_heroi(palavra):
    """Prioridade de uma palavra como herói (maior = mais merece destaque).
    0 = nunca (ligação/demonstrativo/advérbio). Aproximado por terminação; segue
    o idioma escolhido. Prefere adjetivo > verbo > substantivo."""
    r = _regras()
    p = palavra.strip(".,;:!?—-\"'…“”").lower()
    if not p or p in r["nao_heroi"]:
        return 0
    if p.endswith(r["adj"]):
        return 4                       
    if p.endswith(r["verbo"]):
        return 2                       
    return 1                           



HERO_MIN = 5   


def _eh_numero(t):
    return any(c.isdigit() for c in str(t))


def _strip_pal(w):
    return str(w).strip(".,;:!?—-\"'…“”").lower()


def _hero_score(hg):
    """Herói único: adjetivo > verbo > substantivo; ligação nunca recebe destaque."""
    if len(hg) != 1:
        return -1.0
    palavra = hg[0]
    if _eh_numero(palavra):
        return -0.5
    classe = _classe_heroi(palavra)
    if classe == 0:
        return -1.0
    letras = sum(c.isalpha() for c in str(palavra))
    if letras < HERO_MIN:
        return -0.3
    return classe * 10 + letras * 0.05


def _melhor_unidade_heroi(palavras):
    """Uma única palavra de conteúdo com pelo menos cinco letras."""
    best = None
    for i, palavra in enumerate(palavras):
        if sum(c.isalpha() for c in str(palavra)) < HERO_MIN:
            continue
        score = _hero_score([palavra])
        if score > 0 and (best is None or score > best[1]):
            best = (i, score)
    return (best[0], 1) if best else None


def _por_sentenca(ws):
    """Quebra as palavras [{t,a,b}] em frases na pontuação final. Assim um
    conjunto nunca junta o fim de uma frase com o começo da próxima."""
    frases, atual = [], []
    for w in ws:
        if atual:
            ant = atual[-1]["t"].rstrip()
            while ant and ant[-1] in '")”’»':
                ant = ant[:-1]
            if ant[-1:] in _FIM_FRASE:
                frases.append(atual)
                atual = []
        atual.append(w)
    if atual:
        frases.append(atual)
    return frases


def _fatiar_frase(ws, max_pal=GEN_MAX_PALAVRAS, max_chars=GEN_BLOCK_CHARS,
                  max_ms=4000):
    """Divide UMA frase em conjuntos cortando em pausa/vírgula, nunca no meio de
    um sintagma (programação dinâmica: cada conjunto custa um pouco e quebrar em
    lugar ruim custa caro; tempos em ms)."""
    m = len(ws)
    if m <= 1:
        return [ws] if ws else []
    ini = [w["a"] for w in ws]
    fim = [w["b"] for w in ws]
    ln = [len(w["t"]) for w in ws]
    liga = _regras()["liga"]

    def penalidade(j):
        if j == m - 1:
            return 0
        gap = max(0, ini[j + 1] - fim[j])                
        t = ws[j]["t"].rstrip()
        virg = 400 if t[-1:] in ",;:" else (250 if t[-1:] in "—-" else 0)
        prox = ws[j + 1]["t"].strip(".,;:!?—-\"'").lower()
        bonus = 300 if prox in liga else 0               
        pen = max(0, 400 - gap - virg - bonus)
        limpa = t.strip(".,;:!?—-\"'").lower()
        if limpa in liga:                                
            pen += 350
        return pen

    GRUPO, INF = 120, float("inf")
    custo = [INF] * (m + 1)
    prox = [m] * (m + 1)
    custo[m] = 0
    for i in range(m - 1, -1, -1):
        for j in range(i, m):
            wc = j - i + 1
            if wc > max_pal:
                break
            chars = sum(ln[i:j + 1]) + (j - i)
            if chars > max_chars and wc > 1:
                break
            if fim[j] - ini[i] > max_ms and wc > 1:
                break
            orfao = 250 if wc == 1 else 0
            c = GRUPO + orfao + penalidade(j) + custo[j + 1]
            if c < custo[i]:
                custo[i] = c
                prox[i] = j + 1
    grupos, i = [], 0
    while i < m:
        j = prox[i]
        grupos.append(ws[i:j])
        i = j
    return grupos


def montar_blocos(words):
    """palavras [{t,a,b}] -> blocos (listas de palavras), com o conceito acima."""
    blocos = []
    for frase in _por_sentenca(words):
        blocos.extend(_fatiar_frase(frase))
    return blocos
GEN_CLIP_COLOR = "Orange"   
DESIGN_TRACKING = 0.96            
ANIM_KEY = "TV_anim"              


ANIM_IN = [
    (("slide",), "left"),
    (("slide",), "right"),
    (("slide",), "up"),
    (("slide",), "down"),
    (("blur",), "none"),
    (("slide", "blur"), "left"),
    (("slide", "blur"), "right"),
    (("slide", "blur"), "up"),
    (("slide", "blur"), "down"),
    (("flicker",), "none"),
]
ANIM_IN_STEP = 3                  
ANIM_OUT = (("blur",), "none")    


def dirs_permitidas(linha, total):
    """Nenhuma linha entra ATRAVESSANDO o espaço de outra (regra do Bruno).
    'up' = vem de baixo subindo; 'down' = vem de cima descendo.
      - linha de cima : nunca de baixo  -> sem 'up'
      - linha do meio : só na horizontal (qualquer vertical cruza a vizinha)
      - linha de baixo: nunca de cima   -> sem 'down'
    """
    if total <= 1:
        return ("left", "right", "up", "down", "none")
    if linha == 0:
        return ("left", "right", "down", "none")
    if linha >= total - 1:
        return ("left", "right", "up", "none")
    return ("left", "right", "none")


def _passo_primo(n):
    """Passo coprimo com n: sem isso a rotação repete poucas receitas.
    (a linha do meio tem lista menor e ficava alternando só duas)"""
    def mdc(a, b):
        while b:
            a, b = b, a % b
        return a
    for k in (5, 3, 7, 2):
        if n > 1 and mdc(k, n) == 1:
            return k
    return 1


def anim_receita(bloco, linha, total=3):
    ok = dirs_permitidas(linha, total)
    lista = [r for r in ANIM_IN if r[1] in ok]
    if not lista:
        lista = ANIM_IN
    return lista[(bloco * _passo_primo(len(lista)) + linha) % len(lista)]
SMALL_SIZE_FRAC = 0.22            
SMALL_SIZE_MIN = 0.05             

STYLE = """
QWidget { background-color: #151517; color: #e8e8ea; font-size: 12px; }
QPushButton { background-color: #26262a; border: 1px solid #35353a; border-radius: 8px; padding: 6px 10px; }
QPushButton:hover { background-color: #333338; border-color: #4a4a50; }
QPushButton:pressed { background-color: %(a)s; }
QPushButton:checked { background-color: %(a)s; color: #ffffff; border-color: %(a)s; font-weight: bold; }
QTreeWidget { background-color: #1b1b1e; border: 1px solid #2c2c30; border-radius: 8px; }
QTreeWidget::item:selected { background-color: %(a)s; color: #ffffff; }
QHeaderView::section { background-color: #232327; border: none; padding: 4px; color: #9a9aa0; }
QComboBox { background-color: #232327; border: 1px solid #3a3a40; border-radius: 12px; padding: 6px 10px; min-height: 18px; }
QComboBox::drop-down { border: none; width: 26px; background: transparent;
  border-top-right-radius: 12px; border-bottom-right-radius: 12px; }
QComboBox QAbstractItemView { background-color: #232327; selection-background-color: %(a)s; }
QSpinBox, QDoubleSpinBox { background-color: #232327; border: 1px solid #3a3a40; border-radius: 10px; padding: 5px 8px; min-height: 16px; }
QSpinBox::up-button, QDoubleSpinBox::up-button { background: transparent; border: none; width: 16px; border-top-right-radius: 10px; }
QSpinBox::down-button, QDoubleSpinBox::down-button { background: transparent; border: none; width: 16px; border-bottom-right-radius: 10px; }
QSlider::groove:horizontal { height: 4px; background: #35353a; border-radius: 2px; }
QSlider::handle:horizontal { width: 14px; margin: -6px 0; background: %(a)s; border-radius: 7px; }
QSlider::sub-page:horizontal { background: %(a)s; border-radius: 2px; }
QCheckBox { spacing: 8px; background: transparent; }
QCheckBox::indicator { width: 34px; height: 18px; border: none; background: transparent; }
QLineEdit { background-color: #0f0f11; border: 1px solid #3a3a40; border-radius: 10px;
  padding: 6px 10px; color: #e8e8ea; selection-background-color: %(a)s; }
QLineEdit:focus { border-color: %(a)s; }
QLabel { background: transparent; }
""" % {"a": ACCENT}


STYLE += (
    'QComboBox::down-arrow { image: url("%s/arrow_down.png"); width: 12px; height: 7px; }'
    'QSpinBox::up-arrow, QDoubleSpinBox::up-arrow { image: url("%s/spin_up.png"); width: 8px; height: 5px; }'
    'QSpinBox::down-arrow, QDoubleSpinBox::down-arrow { image: url("%s/spin_dn.png"); width: 8px; height: 5px; }'
) % (ICON_URL, ICON_URL, ICON_URL)


STYLE += (
    'QCheckBox::indicator:unchecked { image: url("%s/toggle_off.png"); }'
    'QCheckBox::indicator:checked { image: url("%s/toggle_on.png"); }'
) % (ICON_URL, ICON_URL)


SECT_HTML_G = ("<span style=\"font-family:'Arial'; font-size:12px; font-weight:bold;"
               " letter-spacing:1px; color:%s;\">%%s</span>" % ACCENT)



CTA_CSS = ("QPushButton{background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
           "stop:0 #38bdf8, stop:0.5 #2563eb, stop:1 #1d4ed8); color:#ffffff; font-size:14px;"
           "font-weight:bold; border:1px solid #60a5fa; border-radius:8px; padding:7px 14px;}"
           "QPushButton:hover{background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
           "stop:0 #60a5fa, stop:0.5 #3b82f6, stop:1 #1e40af); border-color:#93c5fd;}")
CTA_BUSY_CSS = ("QPushButton{background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #1e3a8a, stop:1 #1e40af); color:#93c5fd; font-size:13px;"
                "font-weight:bold; border:1px solid #38bdf8; border-radius:8px; padding:7px 14px;}")
PILL_CSS = ("QPushButton{background-color:#232327; border:1px solid #35353a;"
            "border-radius:17px; padding:9px 14px; font-weight:bold; color:#c8c8cc;}"
            "QPushButton:hover{border-color:#5a5a60;}"
            "QPushButton:checked{background-color:#0f1d38; border:2px solid %(a)s;"
            "color:%(a)s;}" % {"a": ACCENT})






LICENCA_ATIVA = False
LICENCA_API = "https://titulos-virais.brunoadsons.workers.dev"
LICENCA_GRACA = 0      
COMPRAR_EM = "titulosvirais.com"


def _licenca_arquivo():
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.path.expanduser("~/Library/Application Support")            if sys.platform == "darwin" else os.path.expanduser("~/.config")
    pasta = os.path.join(base, "TitulosVirais")
    try:
        if not os.path.isdir(pasta):
            os.makedirs(pasta)
    except Exception:
        _tv_diag.falha('Titulos Virais._licenca_arquivo')
        pass
    return os.path.join(pasta, "licenca.json")


def maquina_id():
    """Identificador estável do computador (sem dado pessoal: é um hash)."""
    import hashlib
    import subprocess
    bruto = ""
    try:
        if sys.platform == "darwin":
            saida = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                stderr=subprocess.DEVNULL).decode("utf-8", "ignore")
            for linha in saida.split("\n"):
                if "IOPlatformUUID" in linha:
                    bruto = linha.split('"')[-2]
                    break
        elif sys.platform.startswith("win"):
            saida = subprocess.check_output(
                ["reg", "query", r"HKLM\SOFTWARE\Microsoft\Cryptography",
                 "/v", "MachineGuid"], stderr=subprocess.DEVNULL,
                **_sem_janela()).decode("utf-8", "ignore")
            bruto = saida.strip().split()[-1]
        else:
            bruto = io.open("/etc/machine-id").read().strip()
    except Exception:
        _tv_diag.falha('Titulos Virais.maquina_id')
        bruto = ""
    if not bruto:
        import uuid
        bruto = str(uuid.getnode())
    return hashlib.sha256(("TV|" + bruto).encode("utf-8")).hexdigest()[:32]


def apelido_maquina():
    try:
        import socket
        return socket.gethostname()[:40]
    except Exception:
        _tv_diag.falha('Titulos Virais.apelido_maquina')
        return ""


def licenca_ler():
    try:
        return json.loads(io.open(_licenca_arquivo(), encoding="utf-8").read())
    except Exception:
        _tv_diag.falha('Titulos Virais.licenca_ler')
        return {}


import types as _perm_types
_perm = _perm_types.ModuleType('tv_permissoes')
exec('"""Persistência de sessão: nunca publica uma gravação parcial."""\nimport json\nimport os\nimport stat\nimport tempfile\n\nMENSAGEM = "Não foi possível salvar seu acesso neste computador. Clique em Corrigir acesso e tente entrar novamente."\n\n\ndef gravar_sessao(caminho, dados):\n    pasta = os.path.dirname(caminho)\n    temporario = None\n    try:\n        os.makedirs(pasta, exist_ok=True)\n        # Não seguir redirecionamentos ao reparar o armazenamento da licença.\n        if os.path.islink(caminho) or os.path.islink(pasta):\n            raise OSError("O armazenamento da sessão é um link simbólico.")\n        if os.name != "nt" and os.stat(pasta).st_uid == os.getuid():\n            modo = stat.S_IMODE(os.stat(pasta).st_mode)\n            if modo & 0o700 != 0o700:\n                os.chmod(pasta, modo | 0o700)\n        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=pasta,\n                                         prefix=".sessao-", delete=False) as f:\n            temporario = f.name\n            json.dump(dados, f, ensure_ascii=False, indent=2)\n            f.flush()\n            os.fsync(f.fileno())\n        os.replace(temporario, caminho)\n        temporario = None\n        with open(caminho, encoding="utf-8") as f:\n            salvo = json.load(f)\n        return salvo == dados\n    finally:\n        if temporario:\n            try:\n                os.unlink(temporario)\n            except OSError:\n                pass\n\n\ndef corrigir_acesso(caminho):\n    """Repara somente a pasta de sessão e o arquivo solicitado, com confirmação do SO."""\n    import subprocess\n    import sys\n    import shlex\n    import base64\n    pasta = os.path.abspath(os.path.dirname(caminho))\n    base = (os.environ.get("APPDATA") if sys.platform.startswith("win") else\n            os.path.expanduser("~/Library/Application Support"))\n    if not base or pasta != os.path.abspath(os.path.join(base, "TitulosVirais")):\n        return False, "Pasta de acesso inesperada; procure o suporte."\n    if os.path.normcase(os.path.realpath(pasta)) != os.path.normcase(pasta) or os.path.islink(caminho):\n        return False, "A pasta de acesso está redirecionada; procure o suporte."\n    try:\n        if sys.platform == "darwin":\n            uid, gid = os.getuid(), os.getgid()\n            if uid == 0:\n                return False, "Abra o aplicativo na sua conta normal."\n            quote = shlex.quote\n            # Sem recursão: não altera mídia, motor, bibliotecas ou outros arquivos.\n            cmd = "set -e; test ! -L {p}; /bin/mkdir -p {p}; /usr/sbin/chown {u}:{g} {p}; /bin/chmod u+rwx {p}".format(p=quote(pasta), u=uid, g=gid)\n            cmd += "; if test -e {f}; then test ! -L {f}; /usr/sbin/chown {u}:{g} {f}; /bin/chmod u+rw {f}; fi".format(f=quote(caminho), u=uid, g=gid)\n            comando = ["/usr/bin/osascript", "-e", "do shell script " + json.dumps(cmd, ensure_ascii=False) + " with administrator privileges"]\n        elif sys.platform.startswith("win"):\n            # Captura a identidade ANTES do UAC: credenciais administrativas podem ser de outra conta.\n            opts = {"creationflags": subprocess.CREATE_NO_WINDOW}\n            sid = subprocess.check_output(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",\n                "[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value"], **opts).decode().strip()\n            import re\n            if not re.fullmatch(r"S-1-[0-9-]+", sid):\n                raise ValueError("Identidade inválida")\n            psquote = lambda v: "\'" + v.replace("\'", "\'\'") + "\'"\n            script = "$ErrorActionPreference=\'Stop\'; $p=" + psquote(pasta) + "; $f=" + psquote(caminho) + "; "\n            script += "if(Test-Path -LiteralPath $p){if((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){exit 2}}; "\n            script += "New-Item -ItemType Directory -Force -Path $p | Out-Null; & icacls.exe $p /grant " + psquote(\'*\'+sid+\':(OI)(CI)M\') + "; if($LASTEXITCODE -ne 0){exit 3}; "\n            script += "if(Test-Path -LiteralPath $f){if((Get-Item -LiteralPath $f -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){exit 2}; & icacls.exe $f /grant " + psquote(\'*\'+sid+\':M\') + "; if($LASTEXITCODE -ne 0){exit 3}; (Get-Item -LiteralPath $f -Force).IsReadOnly=$false}; exit 0"\n            payload = base64.b64encode(script.encode(\'utf-16le\')).decode()\n            outer = "$ErrorActionPreference=\'Stop\'; try {$p=Start-Process powershell.exe -Verb RunAs -WindowStyle Hidden -Wait -PassThru -ArgumentList \'-NoProfile -NonInteractive -EncodedCommand " + payload + "\'; exit $p.ExitCode} catch {exit 1}"\n            comando = ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", base64.b64encode(outer.encode(\'utf-16le\')).decode()]\n        else:\n            return False, "Correção automática disponível no Mac e Windows."\n        r = subprocess.run(comando, capture_output=True, **({"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform.startswith("win") else {}))\n        if r.returncode:\n            return False, "A correção não foi concluída. Autorize a solicitação do sistema ou procure o suporte."\n        # Prova de acesso sem alterar/apagar a licença existente.\n        with tempfile.NamedTemporaryFile(dir=pasta, prefix=".teste-acesso-") as teste:\n            teste.write(b"ok"); teste.flush()\n        return True, "Acesso corrigido. Entre novamente."\n    except Exception:\n        return False, "Não foi possível corrigir o acesso. Verifique as permissões de privacidade do sistema ou procure o suporte."\n\n\ndef verificar_acesso(caminho):\n    pasta = os.path.dirname(caminho)\n    try:\n        os.makedirs(pasta, exist_ok=True)\n        if os.path.islink(pasta) or os.path.islink(caminho):\n            return False\n        if os.name != \'nt\' and os.stat(pasta).st_uid == os.getuid():\n            os.chmod(pasta, stat.S_IMODE(os.stat(pasta).st_mode) | 0o700)\n        with tempfile.NamedTemporaryFile(dir=pasta, prefix=\'.teste-acesso-\') as f:\n            f.write(b\'ok\'); f.flush()\n        return True\n    except OSError:\n        return False\n', _perm.__dict__)
_gravar_sessao = _perm.gravar_sessao
_ERRO_PERMISSAO = _perm.MENSAGEM
_corrigir_acesso = _perm.corrigir_acesso
_verificar_acesso = _perm.verificar_acesso


import types as _ac_types
_ac_mod = _ac_types.ModuleType('tv_acesso_davinci')
exec('"""Preflight do armazenamento próprio do DaVinci; nunca toca projetos ou mídia."""\nimport errno\nimport json\nimport os\nimport stat\nimport subprocess\nimport sys\nimport tempfile\n\n\ndef alvos(licenca, motor):\n    result = [(os.path.dirname(licenca), \'pasta\'), (motor, \'pasta\'), (licenca, \'arquivo\')]\n    for name in (\'whisper-cli\', \'whisper-cli.exe\', \'ffmpeg\', \'ffmpeg.exe\', \'ggml-small.bin\'):\n        result.append((os.path.join(motor, name), \'executavel\' if name in (\'whisper-cli\', \'ffmpeg\') else \'arquivo\'))\n    if os.path.isdir(motor):\n        try: nomes = os.listdir(motor)\n        except OSError: nomes = []\n        result.extend((os.path.join(motor, n), \'arquivo\') for n in nomes if n.lower().endswith(\'.dll\'))\n    return result\n\n\ndef _sem_link(path):\n    path = os.path.abspath(path)\n    if os.path.realpath(path) != path:\n        raise OSError(errno.ELOOP, \'Pasta ou arquivo redirecionado; procure o suporte.\', path)\n\n\ndef verificar(licenca, motor, diag):\n    problemas = []\n    try:\n        targets = alvos(licenca, motor)\n    except OSError as e:\n        targets = [(os.path.dirname(licenca), \'pasta\'), (motor, \'pasta\'), (licenca, \'arquivo\')]\n        diag.falha(\'acesso.listar_motor\', e, arquivo=motor)\n        problemas.append({\'arquivo\': motor, \'operacao\': \'listar\', \'errno\': e.errno})\n    for path, kind in targets:\n        try:\n            _sem_link(path)\n            if kind != \'pasta\' and not os.path.exists(path):\n                continue  # ausência é tratada pela instalação do motor/login\n            if kind == \'pasta\':\n                os.makedirs(path, exist_ok=True)\n            st = os.stat(path)\n            needed = 0o700 if kind == \'pasta\' else (0o500 if kind == \'executavel\' else 0o400)\n            if os.name != \'nt\' and st.st_uid == os.getuid() and stat.S_IMODE(st.st_mode) & needed != needed:\n                os.chmod(path, stat.S_IMODE(st.st_mode) | needed)\n                diag.evento(\'acesso.reparo_sem_admin\', arquivo=path, modo=oct(needed))\n            if kind == \'pasta\':\n                # Criação, gravação, sincronização, renomeação e remoção reais.\n                fd, tmp = tempfile.mkstemp(dir=path, prefix=\'.tv-acesso-\')\n                try:\n                    with os.fdopen(fd, \'wb\') as f:\n                        f.write(b\'ok\'); f.flush(); os.fsync(f.fileno())\n                    novo = tmp + \'.ok\'; os.replace(tmp, novo); tmp = novo\n                finally:\n                    os.unlink(tmp)\n            else:\n                with open(path, \'rb\') as f: f.read(1)\n                if os.name == \'nt\' and path == licenca and not st.st_mode & stat.S_IWRITE:\n                    raise PermissionError(errno.EACCES, \'Arquivo de acesso somente leitura\', path)\n                if kind == \'executavel\' and not os.access(path, os.X_OK):\n                    raise PermissionError(errno.EACCES, \'Motor sem permissão de execução\', path)\n        except OSError as e:\n            info = {\'arquivo\': path, \'operacao\': kind, \'errno\': e.errno}\n            try:\n                st = os.lstat(path); info.update(dono_uid=st.st_uid, modo=oct(stat.S_IMODE(st.st_mode)))\n            except OSError: pass\n            diag.falha(\'acesso.verificar\', e, **info)\n            problemas.append(info)\n    try:\n        with tempfile.TemporaryFile() as f: f.write(b\'ok\'); f.flush()\n    except OSError as e:\n        diag.falha(\'acesso.temporario\', e, arquivo=tempfile.gettempdir())\n        problemas.append({\'arquivo\': tempfile.gettempdir(), \'operacao\': \'temporario\', \'errno\': e.errno})\n    diag.evento(\'acesso.resultado\', aprovado=not problemas, falhas=len(problemas))\n    return problemas\n\n\ndef corrigir(licenca, motor, diag):\n    """Chamado apenas pelo botão do usuário; elevação nativa, alvos fixos, sem -R."""\n    import shlex\n    import base64\n    try:\n        base = os.path.expanduser(\'~/Library/Application Support\') if sys.platform == \'darwin\' else os.environ.get(\'APPDATA\', \'\')\n        motorbase = base if sys.platform == \'darwin\' else os.environ.get(\'LOCALAPPDATA\', \'\')\n        if not base or not motorbase or os.path.abspath(licenca) != os.path.join(base, \'TitulosVirais\', \'licenca.json\') or os.path.abspath(motor) != os.path.join(motorbase, \'TitulosVirais\', \'motor\'):\n            raise ValueError(\'Destino de reparo inesperado\')\n        targets = alvos(licenca, motor)\n        # LOCALAPPDATA pode ser diferente de APPDATA no Windows.\n        if os.path.dirname(motor) != os.path.dirname(licenca):\n            targets.insert(1, (os.path.dirname(motor), \'pasta\'))\n        for path, _ in targets: _sem_link(path)\n        if sys.platform == \'darwin\':\n            uid, gid = os.getuid(), os.getgid()\n            if uid == 0: raise ValueError(\'Abra o Resolve na conta normal\')\n            commands = [\'set -e\']\n            for path, kind in targets:\n                p = shlex.quote(path)\n                # Validar a cadeia de pais também no instante da elevação.\n                chain = path\n                while chain != \'/\':\n                    commands.append(\'test ! -L \'+shlex.quote(chain)); chain = os.path.dirname(chain)\n                if kind == \'pasta\': commands.append(\'/bin/mkdir -p \'+p)\n                mode = \'u+rwx\' if kind in (\'pasta\', \'executavel\') else \'u+rw\'\n                commands.append(\'if test -e {p}; then /usr/sbin/chown {u}:{g} {p}; /bin/chmod {m} {p}; fi\'.format(p=p,u=uid,g=gid,m=mode))\n            cmd = [\'/usr/bin/osascript\', \'-e\', \'do shell script \'+json.dumps(\'; \'.join(commands))+\' with administrator privileges\']\n        elif sys.platform.startswith(\'win\'):\n            import re\n            sid = subprocess.check_output([\'powershell.exe\',\'-NoProfile\',\'-NonInteractive\',\'-Command\',\'[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value\'], creationflags=0x08000000).decode().strip()\n            if not re.fullmatch(r\'S-1-[0-9-]+\', sid): raise ValueError(\'Identidade inválida\')\n            quote = lambda v: "\'"+v.replace("\'", "\'\'")+"\'"\n            script = "$ErrorActionPreference=\'Stop\'; "\n            for path, kind in targets:\n                script += \'$p=\'+quote(path)+\'; \'\n                script += "if(Test-Path -LiteralPath $p){if((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){exit 2}}; "\n                if kind == \'pasta\': script += \'New-Item -ItemType Directory -Force -Path $p | Out-Null; \'\n                script += \'if(Test-Path -LiteralPath $p){& icacls.exe $p /grant \'+quote(\'*\'+sid+(\':(OI)(CI)M\' if kind==\'pasta\' else \':M\'))+\'; if($LASTEXITCODE -ne 0){exit 3}; if(-not (Get-Item -LiteralPath $p -Force).PSIsContainer){(Get-Item -LiteralPath $p -Force).IsReadOnly=$false}}; \'\n            script += \'exit 0\'\n            payload=base64.b64encode(script.encode(\'utf-16le\')).decode()\n            outer="$ErrorActionPreference=\'Stop\'; try {$p=Start-Process powershell.exe -Verb RunAs -WindowStyle Hidden -Wait -PassThru -ArgumentList \'-NoProfile -NonInteractive -EncodedCommand "+payload+"\'; exit $p.ExitCode} catch {exit 1}"\n            cmd=[\'powershell.exe\',\'-NoProfile\',\'-NonInteractive\',\'-EncodedCommand\',base64.b64encode(outer.encode(\'utf-16le\')).decode()]\n        else: return False\n        result=subprocess.run(cmd,capture_output=True,**({\'creationflags\':0x08000000} if sys.platform.startswith(\'win\') else {}))\n        diag.evento(\'acesso.reparo_admin\',retorno=result.returncode)\n        return result.returncode == 0 and not verificar(licenca,motor,diag)\n    except Exception as e:\n        diag.falha(\'acesso.reparo_admin\',e)\n        return False\n', _ac_mod.__dict__)
_verificar_ambiente = _ac_mod.verificar
_corrigir_ambiente = _ac_mod.corrigir


def problemas_acesso():
    global WHISPER_BIN, WHISPER_MODEL
    falhas = _verificar_ambiente(_licenca_arquivo(), MOTOR_DIR, _tv_diag)
    if not falhas:
        
        if not WHISPER_BIN:
            WHISPER_BIN = _achar_programa(["whisper-cli"], [os.path.join(MOTOR_DIR, "whisper-cli.exe"), os.path.join(MOTOR_DIR, "whisper-cli")]) or ""
        if not WHISPER_MODEL:
            WHISPER_MODEL = _achar_arquivo([os.path.join(MOTOR_DIR, "ggml-small.bin")]) or ""
    return falhas


def texto_acesso(pt, es):
    return es if IDIOMA == 'es' else pt


def corrigir_permissao():
    ok = _corrigir_ambiente(_licenca_arquivo(), MOTOR_DIR, _tv_diag)
    return ok, (texto_acesso("Acesso corrigido. Você pode continuar.", "Acceso corregido. Puedes continuar.") if ok else
                texto_acesso("A correção não foi concluída. Autorize a solicitação do sistema ou procure o suporte.", "No se completó la reparación. Autoriza la solicitud del sistema o contacta con soporte."))


def licenca_gravar(d):
    try:
        return _gravar_sessao(_licenca_arquivo(), d)
    except Exception as ex:
        _tv_diag.falha('Titulos Virais.licenca_gravar')
        log("não consegui gravar a licença:", ex)
        return False


def _contexto_ssl():
    """Contexto HTTPS que funciona mesmo em Python sem os certificados do
    sistema. O Python do Resolve (e o do python.org) muitas vezes não confia em
    CA nenhuma até rodar 'Install Certificates' — sem isso, todo HTTPS falha com
    CERTIFICATE_VERIFY_FAILED, que o usuário via como 'Sem conexão'. O certifi
    (standalone ou o embutido no pip, que todo Python tem) resolve isso."""
    import ssl
    ctx = ssl.create_default_context()
    if ctx.cert_store_stats().get("x509_ca", 0) > 0:
        return ctx
    for achar in (lambda: __import__("certifi").where(),
                  lambda: __import__("pip._vendor.certifi",
                                     fromlist=["where"]).where()):
        try:
            return ssl.create_default_context(cafile=achar())
        except Exception:
            _tv_diag.falha('Titulos Virais._contexto_ssl')
            continue
    return ctx


def licenca_post(rota, dados, timeout=10):
    """(ok, resposta_ou_erro, houve_internet)"""
    import urllib.request
    import urllib.error
    corpo = json.dumps(dados).encode("utf-8")
    req = urllib.request.Request(
        LICENCA_API.rstrip("/") + rota, data=corpo,
        headers={"content-type": "application/json",
                 "user-agent": "TitulosVirais/%s" % APP_VERSION})
    try:
        with urllib.request.urlopen(req, timeout=timeout,
                                    context=_contexto_ssl()) as r:
            return True, json.loads(r.read().decode("utf-8")), True
    except urllib.error.HTTPError as e:
        _tv_diag.falha('Titulos Virais.licenca_post', rota=rota, timeout_s=timeout)
        if e.code >= 500 or e.code == 429:
            return False, {"erro": "Servidor temporariamente indisponível."}, False
        try:
            return False, json.loads(e.read().decode("utf-8")), True
        except Exception:
            _tv_diag.falha('Titulos Virais.licenca_post', rota=rota, timeout_s=timeout)
            return False, {"erro": "Servidor respondeu %s." % e.code}, True
    except Exception as ex:
        _tv_diag.falha('Titulos Virais.licenca_post', rota=rota, timeout_s=timeout)
        log("falha de rede em", rota, ":", type(ex).__name__, ex)
        return False, {"erro": "Sem conexão com o servidor."}, False


def _num_versao(v):
    """'v3.10.2' -> (3, 10, 2), para comparar de verdade (10 > 9)."""
    partes = []
    for p in str(v or "").lstrip("vV").split("."):
        n = ""
        for c in p:
            if c.isdigit():
                n += c
            else:
                break
        partes.append(int(n) if n else 0)
    while len(partes) < 3:
        partes.append(0)
    return tuple(partes[:3])


def checar_atualizacao(detailed=False):
    return (_update_module.check_status(APP_VERSION) if detailed
            else _update_module.check(APP_VERSION))
def _old_update():
    """Pergunta ao servidor se saiu versão nova. Devolve (versao, link, notas)
    ou None. Falha em silêncio: sem internet o plugin abre normal."""
    ok, resp, _net = licenca_post("/api/versao",
                                  {"produto": APP_ALVO + "-" + IDIOMA}, timeout=6)
    if not ok or not isinstance(resp, dict):
        return None
    nova = resp.get("versao")
    if not nova or _num_versao(nova) <= _num_versao(APP_VERSION):
        return None
    return (str(nova), resp.get("link") or LICENCA_API.rstrip("/") + "/baixar/", resp.get("notas") or "")


def abrir_link(url):
    """Abre o navegador no link da atualização."""
    try:
        if sys.platform == "darwin":
            os.system("open %s &" % json.dumps(url))
        elif sys.platform.startswith("win"):
            os.startfile(url)          
        else:
            os.system("xdg-open %s &" % json.dumps(url))
        return True
    except Exception as ex:
        _tv_diag.falha('Titulos Virais.abrir_link')
        log("abrir link:", ex)
        return False


def _hoje():
    import datetime
    return datetime.date.today().isoformat()


def _dias_desde(iso):
    import datetime
    try:
        a = datetime.date(*[int(x) for x in iso.split("-")])
        return (datetime.date.today() - a).days
    except Exception:
        _tv_diag.falha('Titulos Virais._dias_desde')
        return 999


def licenca_sair():
    """Esquece a sessão gravada neste computador. A licença continua valendo —
    o mesmo PC entra de novo sem gastar outra vaga."""
    try:
        os.remove(_licenca_arquivo())
        return True
    except Exception as ex:
        _tv_diag.falha('Titulos Virais.licenca_sair')
        log("sair:", ex)
        return False


def licenca_estado():
    """Decide se o plugin abre. Não bloqueia por falta de internet: usa o
    prazo offline de até sete dias desde a última conferência."""
    falhas = problemas_acesso()
    if falhas:
        return {"ok": False, "motivo": "permissao", "erro": texto_acesso("Sem acesso à pasta: ", "Sin acceso a la carpeta: ") + falhas[0]['arquivo'] + texto_acesso(". Clique em Corrigir acesso.", ". Pulsa Corregir acceso.")}
    d = licenca_ler()
    if not d.get("email") or not d.get("token"):
        return {"ok": False, "motivo": "sem_login", "dados": d}
    if d.get("maquina") != maquina_id():
        return {"ok": False, "motivo": "outra_maquina", "dados": d}
    expira = d.get("expira") or "1970-01-01"

    ok, resp, teve_net = licenca_post("/api/verificar", {
        "email": d["email"], "maquina": d["maquina"],
        "produto": APP_ALVO + "-" + IDIOMA})
    if ok and resp.get("ok"):
        d.update({"expira": resp["expira"], "token": resp["token"],
                  "conferida_em": _hoje()})
        if not licenca_gravar(d):
            return {"ok": False, "motivo": "permissao", "erro": _ERRO_PERMISSAO, "dados": d}
        return {"ok": True, "motivo": "renovada", "dados": d}
    if teve_net:
        licenca_sair()
        return {"ok": False, "motivo": "recusada",
                "erro": resp.get("erro", "Acesso inválido."), "dados": d}
    if expira >= _hoje() and 0 <= _dias_desde(d.get("conferida_em", "1970-01-01")) <= 7:
        return {"ok": True, "motivo": "tolerancia", "dados": d,
                "aviso": "Sem internet — reconferindo em breve."}
    return {"ok": False, "motivo": "offline_demais", "dados": d,
            "erro": "Não consegui confirmar o acesso. Conecte à internet uma vez."}


def _guarda_sessao(email, resp):
    return licenca_gravar({"email": resp.get("email", email), "nome": resp.get("nome"),
                    "produto": resp.get("produto"), "maquina": maquina_id(),
                    "expira": resp["expira"], "token": resp["token"],
                    "conferida_em": _hoje()})


def conta_status(email):
    """(existe, tem_senha, erro) — para o plugin saber o que perguntar."""
    ok, resp, net = licenca_post("/api/status", {
        "email": (email or "").strip(), "produto": APP_ALVO + "-" + IDIOMA})
    if not net:
        return None, None, "Sem conexão com o servidor."
    if not ok:
        return None, None, resp.get("erro", "Não consegui consultar.")
    return bool(resp.get("existe")), bool(resp.get("tem_senha")), resp.get("erro")


def conta_entrar(email, senha, transferir_de=None):
    if not _verificar_acesso(_licenca_arquivo()):
        return False, _ERRO_PERMISSAO
    ok, resp, _n = licenca_post("/api/entrar", {
        "email": (email or "").strip(), "senha": senha or "",
        "produto": APP_ALVO + "-" + IDIOMA, "maquina": maquina_id(),
        "apelido": apelido_maquina(), "transferir_de": transferir_de})
    if ok and resp.get("ok"):
        if not _guarda_sessao(email, resp):
            return False, _ERRO_PERMISSAO
        return True, "Tudo certo. Bom trabalho!"
    if resp.get("codigo") == "confirmar_transferencia" and resp.get("transferir_de"):
        return False, resp
    return False, resp.get("erro", "Não consegui entrar.")


def conta_criar_senha(email, senha):
    if not _verificar_acesso(_licenca_arquivo()):
        return False, _ERRO_PERMISSAO
    ok, resp, _n = licenca_post("/api/criar-senha", {
        "email": (email or "").strip(), "senha": senha or "",
        "produto": APP_ALVO + "-" + IDIOMA, "maquina": maquina_id(),
        "apelido": apelido_maquina()})
    if ok and resp.get("ok"):
        if not _guarda_sessao(email, resp):
            return False, _ERRO_PERMISSAO
        return True, "Senha criada. Bom trabalho!"
    return False, resp.get("erro", "Não consegui criar a senha.")


def conta_recuperar(email):
    ok, resp, net = licenca_post("/api/recuperar", {
        "email": (email or "").strip(), "produto": APP_ALVO + "-" + IDIOMA})
    if not net:
        return False, "Sem conexão com o servidor."
    return True, "Se este e-mail estiver na compra, o código chegou nele."


def conta_redefinir(email, codigo, senha):
    ok, resp, _n = licenca_post("/api/redefinir", {
        "email": (email or "").strip(), "codigo": (codigo or "").strip(),
        "senha": senha or "", "produto": APP_ALVO + "-" + IDIOMA})
    if ok and resp.get("ok"):
        return True, "Senha trocada. Agora é só entrar."
    return False, resp.get("erro", "Não consegui trocar a senha.")


MSG_SEM_EMAIL = "Não achei esse e-mail. Use o mesmo da compra ou fale com o suporte."


class Login(object):
    """Entrada do plugin: e-mail da compra + senha.
    Três estados — entrar / criar senha (1º acesso) / esqueci a senha."""

    def __init__(self, estado):
        self.estado = estado
        self.liberado = False
        self.modo = "entrar"
        for wid in (LOGIN_ID, WIN_ID) + OLD_WIN_IDS:
            for _ in range(6):
                try:
                    v = ui.FindWindow(wid)
                    if not v:
                        break
                    v.Close()
                except Exception:
                    _tv_diag.falha('Titulos Virais.__init__')
                    break
        for _ in range(12):
            try:
                disp.StepLoop()
            except Exception:
                _tv_diag.falha('Titulos Virais.__init__')
                break
        d = estado.get("dados") or {}
        ROT = ("color:#8a8a92;font-size:10px;letter-spacing:1px;"
               "background:transparent;")
        self.win = disp.AddWindow({
            "ID": LOGIN_ID, "WindowTitle": APP_NAME,
            "Geometry": [420, 180, 460, 500],
            "WindowFlags": {"Window": True, "WindowStaysOnTopHint": True},
            "StyleSheet": STYLE,
        }, [
          ui.HGroup({"Spacing": 0, "Margin": 0}, [
            ui.HGap(0, 1),
            ui.VGroup({"ID": "lg_caixa", "Spacing": 9, "Margin": 10,
                       "MinimumSize": [420, 420], "MaximumSize": [2000, 10000]}, [
                ui.HGroup({"Spacing": 10, "Weight": 0}, [
                    ui.Label({"Text": "<img src='%s/brand_icon.png' width='54' height='54'>"
                                      % ICON_URL,
                              "MinimumSize": [56, 56], "MaximumSize": [56, 58]}),
                    ui.Label({"Text": "<img src='%s/brand_word.png' width='179' height='53'>"
                                      % ICON_URL,
                              "MinimumSize": [180, 53], "MaximumSize": [188, 55]}),
                    ui.HGap(0, 1),
                ]),
                ui.Label({"Text": "", "MinimumSize": [200, 2], "MaximumSize": [400, 2],
                          "StyleSheet": "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                                        "stop:0 %s, stop:1 #1b1b1e);" % ACCENT}),
                ui.Label({"ID": "lg_titulo", "Text": SECT_HTML_G % "ENTRAR",
                          "StyleSheet": "background:transparent;",
                          "MinimumSize": [200, 16], "MaximumSize": [400, 18]}),
                ui.Label({"ID": "lg_sub",
                          "Text": "Use o e-mail da compra. No primeiro acesso, deixe a senha em branco.",
                          "StyleSheet": "color:#9a9aa0;background:transparent;",
                          "MaximumSize": [400, 18]}),

                ui.Label({"Text": "E-MAIL DA COMPRA", "StyleSheet": ROT,
                          "MaximumSize": [400, 14]}),
                ui.LineEdit({"ID": "lg_email", "Text": d.get("email", ""),
                             "PlaceholderText": "voce@email.com",
                             "MinimumSize": [200, 32], "MaximumSize": [400, 34]}),

                ui.Label({"ID": "lg_rot_codigo", "Text": "CÓDIGO QUE CHEGOU NO E-MAIL",
                          "StyleSheet": ROT, "MaximumSize": [400, 14]}),
                ui.LineEdit({"ID": "lg_codigo", "PlaceholderText": "000000",
                             "MinimumSize": [200, 32], "MaximumSize": [400, 34]}),

                ui.Label({"ID": "lg_rot_senha", "Text": "SENHA", "StyleSheet": ROT,
                          "MaximumSize": [400, 14]}),
                ui.LineEdit({"ID": "lg_senha", "EchoMode": "Password",
                             "PlaceholderText": "sua senha",
                             "MinimumSize": [200, 32], "MaximumSize": [400, 34]}),

                ui.Button({"ID": "lg_ok", "Text": "ENTRAR", "StyleSheet": CTA_CSS,
                           "MinimumSize": [200, 44], "MaximumSize": [400, 46]}),
                ui.Label({"ID": "lg_msg", "Text": estado.get("erro", ""),
                          "Alignment": {"AlignHCenter": True}, "WordWrap": True,
                          "StyleSheet": "color:#38bdf8;background:transparent;",
                          "MinimumSize": [200, 32], "MaximumSize": [400, 40]}),
                ui.Button({"ID": "lg_acesso", "Text": "Corrigir acesso", "MaximumSize": [400, 26]}),
                ui.Button({"ID": "lg_link", "Text": "esqueci minha senha",
                           "Flat": True, "MinimumSize": [200, 22],
                           "MaximumSize": [400, 24],
                           "StyleSheet": "QPushButton{border:none;background:transparent;"
                                         "color:#9a9aa0;}"
                                         "QPushButton:hover{color:%s;}" % ACCENT}),
                ui.Label({"Text": "Ainda não tem? <b>%s</b>" % COMPRAR_EM,
                          "Alignment": {"AlignHCenter": True},
                          "StyleSheet": "color:#77777d;font-size:11px;background:transparent;",
                          "MaximumSize": [400, 16]}),
                ui.VGap(0, 30),
            ]),
            ui.HGap(0, 1),
          ]),
        ])
        self.itens = self.win.GetItems()
        self.win.On[LOGIN_ID].Close = self._fechar
        self.win.On.lg_acesso.Clicked = self._corrigir_permissao
        self.win.On.lg_ok.Clicked = self._confirmar
        self.win.On.lg_link.Clicked = self._link
        self.modo = "entrar"

    def _corrigir_permissao(self, ev):
        self.itens["lg_acesso"].Enabled = False
        try:
            ok, mensagem = corrigir_permissao()
            self.itens["lg_msg"].Text = mensagem
        finally:
            self.itens["lg_acesso"].Enabled = True

    
    
    
    
    
    def _vis(self, wid, mostra, alt):
        """Esconde de verdade: no UIManager o widget oculto ainda ocupa a
        altura mínima, então zeramos o tamanho junto."""
        w = self.itens[wid]
        try:
            w.MinimumSize = [200, alt] if mostra else [0, 0]
            w.MaximumSize = [400, alt + 2] if mostra else [0, 0]
        except Exception:
            _tv_diag.falha('Titulos Virais._vis')
            pass
        w.Hidden = not mostra

    def _relayout(self):
        """O UIManager só refaz o layout quando a janela muda de tamanho — sem
        isso o campo escondido continua ocupando o lugar dele. Então a janela
        cresce 1px e volta, só para o Qt refazer as contas."""
        try:
            g = self.win.Geometry
            if isinstance(g, dict):
                g = [g[1], g[2], g[3], g[4]]
            g = [int(v) for v in g]
            self.win.Geometry = [g[0], g[1], g[2], g[3] + 1]
            self._passo()
            self.win.Geometry = g
        except Exception as ex:
            _tv_diag.falha('Titulos Virais._relayout')
            log("relayout do login:", ex)

    def _modo(self, modo, msg=None):
        self.modo = modo
        i = self.itens
        cfg = {
            "transferir": ("TRANSFERIR ACESSO", "Deseja desconectar o outro computador e entrar neste?", "SIM, TRANSFERIR", "SENHA"),
            "entrar":  ("ENTRAR", "Use o e-mail da compra. No primeiro acesso, "
                        "deixe a senha em branco.", "ENTRAR", "SENHA"),
            "criar":   ("PRIMEIRO ACESSO", "Crie a senha que você vai usar daqui em diante.",
                        "CRIAR SENHA E ENTRAR", "CRIE UMA SENHA (mín. 6)"),
            "esqueci": ("RECUPERAR SENHA", "Confirme o e-mail e clique em enviar código.",
                        "ENVIAR CÓDIGO", "SENHA"),
            "codigo":  ("NOVA SENHA", "Digite o código que chegou e escolha a senha nova.",
                        "TROCAR SENHA", "NOVA SENHA (mín. 6)"),
        }[modo]
        try:
            i["lg_titulo"].Text = SECT_HTML_G % cfg[0]
            i["lg_sub"].Text = cfg[1]
            i["lg_ok"].Text = cfg[2]
            i["lg_rot_senha"].Text = cfg[3]
            self._vis("lg_rot_codigo", modo == "codigo", 14)
            self._vis("lg_codigo", modo == "codigo", 32)
            self._vis("lg_rot_senha", modo not in ("esqueci", "transferir"), 14)
            self._vis("lg_senha", modo not in ("esqueci", "transferir"), 32)
            i["lg_link"].Text = ("esqueci minha senha" if modo == "entrar"
                                 else "voltar para o login")
            if modo == "transferir":
                i["lg_link"].Text = "NÃO, CANCELAR"
            if msg is not None:
                i["lg_msg"].Text = msg
        except Exception as ex:
            _tv_diag.falha('Titulos Virais._modo')
            log("modo do login:", ex)
        self._relayout()

    def _link(self, ev):
        self._transferencia = None
        self._modo("esqueci" if self.modo == "entrar" else "entrar", "")

    def _passo(self):
        for _ in range(3):
            try:
                disp.StepLoop()
            except Exception:
                _tv_diag.falha('Titulos Virais._passo')
                break

    def _confirmar(self, ev):
        i = self.itens
        email = i["lg_email"].Text
        senha = i["lg_senha"].Text
        i["lg_msg"].Text = "Conferindo…"
        self._passo()

        if self.modo == "transferir":
            dados = getattr(self, "_transferencia", None)
            self._transferencia = None
            if not dados:
                self._modo("entrar", "Login cancelado.")
                return
            ok, msg = conta_entrar(*dados)
            if isinstance(msg, dict):
                msg = "A sessão mudou. Entre novamente para confirmar a transferência."
            if ok:
                self.liberado = True
                self._sair = True
            else:
                self._modo("entrar", msg)
            return

        if self.modo == "esqueci":
            _ok, msg = conta_recuperar(email)
            self._modo("codigo", msg)
            return

        if self.modo == "codigo":
            ok, msg = conta_redefinir(email, i["lg_codigo"].Text, senha)
            if ok:
                self._modo("entrar", msg)
            else:
                i["lg_msg"].Text = msg
            return

        if self.modo == "entrar":
            existe, tem_senha, erro = conta_status(email)
            if existe is None:
                i["lg_msg"].Text = erro or "Não consegui falar com o servidor."
                return
            if not existe:
                i["lg_msg"].Text = MSG_SEM_EMAIL
                return
            if erro:
                i["lg_msg"].Text = erro
                return
            if not tem_senha:
                self._modo("criar", "Primeiro acesso: escolha sua senha.")
                return
            ok, msg = conta_entrar(email, senha)
        else:
            ok, msg = conta_criar_senha(email, senha)

        if not ok and isinstance(msg, dict) and msg.get("codigo") == "confirmar_transferencia":
            self._transferencia = (email, senha, msg["transferir_de"])
            self._modo("transferir", "")
            return
        i["lg_msg"].Text = msg
        if ok:
            self.liberado = True
            self._sair = True

    def _fechar(self, ev):
        if not getattr(self, "_fechavel", False):
            return
        self._sair = True

    def run(self):
        self.win.Show()
        for _m in ("Raise", "ActivateWindow"):
            try:
                getattr(self.win, _m)()
            except Exception:
                _tv_diag.falha('Titulos Virais.run')
                pass
        self._passo()
        self._modo("entrar")
        self._sair = False
        self._fechavel = False
        import time as _t
        aberto = _t.time()
        if getattr(disp, "StepLoop", None):
            subiu = False
            while not self._sair:
                try:
                    disp.StepLoop()
                except Exception as ex:
                    _tv_diag.falha('Titulos Virais.run')
                    log("laço do login parou:", ex)
                    break
                _t.sleep(0.03)
                if not self._fechavel and _t.time() - aberto > 1.0:
                    self._fechavel = True
                if not subiu and _t.time() - aberto > 0.4:
                    _recuperar_janela(APP_NAME, _tv_diag)
                    subiu = True
                    for _m in ("Show", "Raise", "ActivateWindow"):
                        try:
                            getattr(self.win, _m)()
                        except Exception:
                            _tv_diag.falha('Titulos Virais.run')
                            pass
        else:
            self._fechavel = True
            disp.RunLoop()
        self.win.Hide()
        try:
            self.win.Close()
        except Exception:
            _tv_diag.falha('Titulos Virais.run')
            pass
        return self.liberado


class App(object):
    def __init__(self):
        
        
        for wid in (WIN_ID,) + OLD_WIN_IDS:
            
            
            try:
                todas = ui.FindWindows(wid)
                if todas:
                    vals = todas.values() if hasattr(todas, "values") else todas
                    for w in list(vals):
                        try:
                            w.Hide()
                            w.Close()
                        except Exception:
                            _tv_diag.falha('Titulos Virais.__init__')
                            pass
                    log("Fechada janela anterior (%s)." % wid)
            except Exception:
                _tv_diag.falha('Titulos Virais.__init__')
                pass
            for _ in range(8):        
                try:
                    w = ui.FindWindow(wid)
                    if not w:
                        break
                    w.Hide()
                    w.Close()
                except Exception:
                    _tv_diag.falha('Titulos Virais.__init__')
                    break
        
        for _ in range(12):
            try:
                disp.StepLoop()
            except Exception:
                _tv_diag.falha('Titulos Virais.__init__')
                break
        self._busy = False
        self._sfx = _sound_module.SoundEffects(RESOURCE_DIR)
        self.anim = Animator()
        self.layout = Layouter(self.anim)
        self.entries = []
        self.last_tc = None
        self.gen_layouts = list(GEN_LAY_DEF)
        self.gen_auto = True        
        self.build()
        self.mostrar_update()
        self._preview_ready = True
        self._try(self._gpreview)
        self._try(self.update_preview)

    
    def build(self):
        def lay_btn(key, label):
            ic = icon("layout_" + key)
            d = {"ID": "lay_" + key, "Text": "" if ic else label, "ToolTip": label,
                 "Flat": False, "MinimumSize": [92, 58], "MaximumSize": [116, 88]}
            if ic:
                d["Icon"] = ic
                d["IconSize"] = [80, 55]
            return ui.Button(d)

        
        
        
        GLAY_CSS = ("QPushButton{background-color:#1d1d22; border:1px solid #2c2c31;"
                    "border-radius:12px;}"
                    "QPushButton:hover{border-color:#4a4a50;}"
                    "QPushButton:checked{background-color:#0f1d38;"
                    "border:2px solid %s;}" % ACCENT)

        def glay_btn(key, label):
            ic = icon("layout_" + key)
            d = {"ID": "glay_" + key, "Text": "" if ic else label[:3], "ToolTip": label,
                 "Checkable": True, "StyleSheet": GLAY_CSS, "Weight": 1,
                 "MinimumSize": [94, 56], "MaximumSize": [116, 58]}
            if ic:
                d["Icon"] = ic
                d["IconSize"] = [82, 42]
            return ui.Button(d)

        def anim_side(side, title):
            p = side
            return ui.VGroup({"Spacing": 4, "MinimumSize": [212, 190],
                              "MaximumSize": [225, 230]}, [
                ui.Label({"Text": SECT_HTML % title, "Alignment": {"AlignHCenter": True},
                          "StyleSheet": "background:transparent;"}),
                ui.HGroup({"Spacing": 4}, [
                    ui.Button({"ID": p + "_slide", "Text": "Slide", "Checkable": True}),
                    ui.Button({"ID": p + "_bounce", "Text": "Bounce", "Checkable": True}),
                ]),
                ui.VGroup({"Spacing": 2}, [
                    ui.HGroup({}, [ui.HGap(0, 1), ui.Button({"ID": p + "_up", "Text": "▲", "Checkable": True, "MinimumSize": [30, 24], "MaximumSize": [30, 24]}), ui.HGap(0, 1)]),
                    ui.HGroup({"Spacing": 2}, [
                        ui.HGap(0, 1),
                        ui.Button({"ID": p + "_left", "Text": "◀", "Checkable": True, "MinimumSize": [30, 24], "MaximumSize": [30, 24]}),
                        ui.Button({"ID": p + "_none", "Text": "•", "Checkable": True, "MinimumSize": [30, 24], "MaximumSize": [30, 24], "ToolTip": "Sem direção"}),
                        ui.Button({"ID": p + "_right", "Text": "▶", "Checkable": True, "MinimumSize": [30, 24], "MaximumSize": [30, 24]}),
                        ui.HGap(0, 1),
                    ]),
                    ui.HGroup({}, [ui.HGap(0, 1), ui.Button({"ID": p + "_down", "Text": "▼", "Checkable": True, "MinimumSize": [30, 24], "MaximumSize": [30, 24]}), ui.HGap(0, 1)]),
                ]),
                ui.HGroup({"Spacing": 4}, [
                    ui.Button({"ID": p + "_flicker", "Text": "Flicker", "Checkable": True}),
                    ui.Button({"ID": p + "_shake", "Text": "Shake", "Checkable": True}),
                    ui.Button({"ID": p + "_blur", "Text": "Blur", "Checkable": True}),
                ]),
                ui.Label({"Text": "Efeito sonoro"}),
                ui.ComboBox({"ID": p + "_sound", "MinimumSize": [190, 26]}),
            ])

        FIELD_CSS = ("QPushButton{background-color:#232327; border:1px solid #3a3a40;"
                     "border-radius:13px; padding:4px 10px; text-align:left;"
                     "color:#e8e8ea;}"
                     "QPushButton:hover{border-color:#5a5a60;}"
                     "QPushButton:checked{background-color:#232327;}")

        def style_rows(pfx):
            """Fonte + cor da linha Principal e das Secundárias (mesmo bloco
            nas duas abas; tudo espelhado pelo sync_style)."""
            DOT = ("QPushButton{background-color: rgb(%d,%d,%d); border-radius:8px;"
                   "border:1px solid #333;}"
                   "QPushButton:hover{border:2px solid #bbb;}"
                   "QPushButton:checked{border:2px solid white;}")

            def dots(kind):
                out = []
                for i, (n, rgb) in enumerate(COLORS):
                    r, g, b = [int(c * 255) for c in rgb]
                    out.append(ui.Button({
                        "ID": "%s%s_%d" % (pfx, kind, i), "Text": "", "ToolTip": n,
                        "Checkable": True, "MinimumSize": [17, 17],
                        "MaximumSize": [17, 17], "StyleSheet": DOT % (r, g, b)}))
                return out

            def row(nome, cid, kind):
                return ui.HGroup({"Spacing": 6}, [
                    ui.Label({"Text": nome, "StyleSheet": ROWLBL,
                              "MinimumSize": [72, 18], "MaximumSize": [72, 24]}),
                    ui.Button({"ID": cid, "Text": "", "MinimumSize": [132, 26],
                               "MaximumSize": [146, 28], "StyleSheet": FIELD_CSS}),
                ] + dots(kind) + [ui.HGap(0, 1)])
            return [row("Principal", pfx + "fmain", "m"),
                    row("Apoio", pfx + "fsec", "s")]

        SEC = "color:%s;font-size:14px;font-weight:bold;background:transparent;" % ACCENT
        SECT = ("color:%s;font-size:11px;font-weight:bold;letter-spacing:1px;"
                "background:transparent;" % ACCENT)
        
        
        SECT_HTML = SECT_HTML_G

        def sec(txt):
            """Cabeçalho de categoria: laranja em negrito + régua (estilo
            Inspector do Resolve) — separa visualmente cada bloco."""
            return ui.VGroup({"Spacing": 3, "Weight": 0,
                              "MaximumSize": [452, 22]}, [
                ui.Label({"Text": SECT_HTML % txt, "StyleSheet": "background:transparent;",
                          "MinimumSize": [160, 15], "MaximumSize": [452, 17]}),
                ui.Label({"Text": "", "MinimumSize": [160, 1],
                          "MaximumSize": [452, 1],
                          "StyleSheet": "background-color:#3a3a42;"}),
            ])

        def slider_row(nome, sid, lid, mn, mx, val, txt):
            return ui.HGroup({"Spacing": 8}, [
                ui.Label({"Text": nome, "StyleSheet": ROWLBL,
                          "MinimumSize": [58, 18], "MaximumSize": [58, 20]}),
                ui.Slider({"Tracking": True, "Events": {"SliderMoved": True}, "ID": sid, "Minimum": mn, "Maximum": mx, "Value": val,
                           "Orientation": "Horizontal", "MaximumSize": [330, 22]}),
                ui.LineEdit({"ID": lid, "Text": txt, "StyleSheet": NUM_CSS,
                          "Alignment": {"AlignRight": True},
                          "MinimumSize": [44, 18], "MaximumSize": [46, 20]}),
                ui.HGap(4),
            ])
        CAPS = ("color:#8a8a92;font-size:10px;font-weight:bold;"
                "letter-spacing:1px;background:transparent;")
        SUB = "color:#9a9aa0;font-size:11px;background:transparent;"
        ROWLBL = "color:#c9c9ce;background:transparent;"
        NUM_CSS = ("QLineEdit{color:#e8e8ea;background:#171719;"
                   "font-family:'Arial';font-size:11px;padding:0px 2px;"
                   "border:1px solid #45454d;border-radius:3px;}")
        CARD = ("QLabel{background-color:#1d1d22; border:1px solid #2c2c31;"
                "border-radius:14px; padding:8px; color:#9a9aa0;}")
        TIP = ("QLabel{background-color:#241a10; border:1px solid #3a2a16;"
               "border-radius:12px; padding:10px 12px; color:#c9a065;}")

        def toggle_row(cid, label, tip=None):
            
            return ui.HGroup({"Spacing": 8}, [
                ui.CheckBox({"ID": cid, "Text": label, "ToolTip": tip or label,
                             "MinimumSize": [260, 22], "MaximumSize": [340, 24]}),
                ui.HGap(0, 1),
            ])

        def toggle_par(a, b=None):
            """Dois switches na mesma linha (metade da altura). b=None deixa
            a segunda coluna vazia."""
            def cel(t):
                if t is None:
                    return ui.HGap(0, 1)
                cid, label, tip = t
                return ui.CheckBox({"ID": cid, "Text": label, "ToolTip": tip,
                                    "MinimumSize": [196, 22], "MaximumSize": [214, 24]})
            return ui.HGroup({"Spacing": 8}, [cel(a), cel(b), ui.HGap(0, 1)])

        
        try:
            _proj, _tl = get_timeline()
            _tw = float(_tl.GetSetting("timelineResolutionWidth") or 1080)
            _th = float(_tl.GetSetting("timelineResolutionHeight") or 1920)
        except Exception:
            _tv_diag.falha('Titulos Virais.build')
            _tw, _th = 1080.0, 1920.0
        _box_w, _box_h = 190.0, 212.0
        _s = min(_box_w / _tw, _box_h / _th)
        self.prev_w = int(_tw * _s)
        self.prev_h = int(_th * _s)
        
        _gbw, _gbh = 118.0, 210.0
        _gs = min(_gbw / _tw, _gbh / _th)
        self.gprev_w = int(_tw * _gs)
        self.gprev_h = int(_th * _gs)
        
        
        
        self.gmid_h = max(self.gprev_h, 214)

        
        
        QSEC_HTML = ("<span style=\"font-family:'Arial'; font-size:12px; font-weight:bold;"
                     " letter-spacing:1px; color:#c9c9d0;\">%s</span>")

        def qsec(txt):
            return ui.HGroup({"Spacing": 7, "Weight": 0, "MaximumSize": [420, 18]}, [
                ui.Label({"Text": "", "MinimumSize": [3, 13], "MaximumSize": [3, 13],
                          "StyleSheet": "QLabel{background-color:%s;border-radius:1px;}" % ACCENT}),
                ui.Label({"Text": QSEC_HTML % txt, "StyleSheet": "background:transparent;",
                          "MinimumSize": [150, 15], "MaximumSize": [400, 17]}),
                ui.HGap(0, 1),
            ])

        def subhead(txt):
            return ui.Label({"Text": ("<span style=\"font-family:'Arial';font-size:10px;"
                                      "font-weight:bold;letter-spacing:1px;color:#6f6f78;\">"
                                      "%s</span>") % txt,
                             "StyleSheet": "background:transparent;",
                             "MinimumSize": [120, 13], "MaximumSize": [260, 15]})

        VAL_CSS = ("QLineEdit{color:%s;background:#171719;font-family:'Arial';"
                   "font-size:11px;font-weight:bold;padding:0px 2px;"
                   "border:1px solid #45454d;border-radius:3px;}"
                   "QLineEdit:focus{border-color:%s;}" % (ACCENT, ACCENT))

        def field2(nome, sid, lid, mn, mx, val, txt):
            """Slider em 2 linhas (spec): rótulo à esquerda + valor à direita na
            mesma linha, trilho logo abaixo. Altura 32. HGap(8) no fim do valor
            pra não cortar o último dígito na borda do grupo."""
            return ui.VGroup({"Spacing": 2, "Weight": 0,
                              "MinimumSize": [240, 32], "MaximumSize": [300, 34]}, [
                ui.HGroup({"Spacing": 4, "MaximumSize": [300, 14]}, [
                    ui.Label({"Text": nome, "StyleSheet": ROWLBL,
                              "MinimumSize": [80, 13], "MaximumSize": [180, 15]}),
                    ui.HGap(0, 1),
                    ui.LineEdit({"ID": lid, "Text": txt, "StyleSheet": VAL_CSS,
                              "Alignment": {"AlignRight": True},
                              "MinimumSize": [40, 13], "MaximumSize": [46, 15]}),
                    ui.HGap(8),
                ]),
                ui.HGroup({"Spacing": 0, "MaximumSize": [300, 16]}, [
                    ui.Slider({"Tracking": True, "Events": {"SliderMoved": True}, "ID": sid, "Minimum": mn, "Maximum": mx, "Value": val,
                               "Orientation": "Horizontal",
                               "MinimumSize": [190, 14], "MaximumSize": [300, 16]}),
                    ui.HGap(8),
                ]),
            ])

        def gswatch(kind, i, n, rgb):
            r, g, b = [int(c * 255) for c in rgb]
            return ui.Button({"ID": "g%s_%d" % (kind, i), "Text": "", "ToolTip": n,
                "Checkable": True, "MinimumSize": [27, 27], "MaximumSize": [28, 28],
                "StyleSheet": ("QPushButton{background-color:rgb(%d,%d,%d);border-radius:8px;"
                               "border:1px solid #3a3a40;}"
                               "QPushButton:hover{border:2px solid #cfcfcf;}"
                               "QPushButton:checked{border:3px solid %s;}"
                               % (r, g, b, ACCENT))})

        def fontrow_g(rotulo, cid, kind):
            
            return ui.HGroup({"Spacing": 8, "MaximumSize": [420, 34]}, [
                ui.Label({"Text": rotulo, "StyleSheet": ROWLBL,
                          "MinimumSize": [74, 18], "MaximumSize": [74, 22]}),
                ui.Button({"ID": cid, "Text": "", "MinimumSize": [150, 30],
                           "MaximumSize": [200, 32], "StyleSheet": FIELD_CSS}),
                ui.ComboBox({"ID": "gest_%s" % kind, "MinimumSize": [96, 30],
                             "MaximumSize": [120, 32]}),
                ui.HGap(0, 1),
            ])

        def swrow_g(kind):
            
            
            
            
            
            
            
            
            
            
            return ui.HGroup({"Spacing": 7, "MaximumSize": [444, 30]},
                [gswatch(kind, i, n, rgb) for i, (n, rgb) in enumerate(COLORS)]
                + [ui.HGap(6),
                   ui.LineEdit({"ID": "ghex_%s" % kind, "Text": "",
                                "ToolTip": "Código da cor, ex: #38bdf8",
                                "Alignment": {"AlignHCenter": True},
                                "MinimumSize": [92, 26], "MaximumSize": [96, 28]}),
                   ui.HGap(0, 1)])

        def fontcor_row_g(rotulo, kind):
            
            linha1 = ui.HGroup({"Spacing": 8, "MaximumSize": [744, 32]}, [
                ui.Label({"Text": rotulo, "StyleSheet": ROWLBL,
                          "MinimumSize": [96, 20], "MaximumSize": [96, 24]}),
                ui.ComboBox({"ID": "gfam_%s" % kind, "MinimumSize": [240, 30],
                             "MaximumSize": [372, 32]}),
                ui.ComboBox({"ID": "gest_%s" % kind, "MinimumSize": [150, 30],
                             "MaximumSize": [200, 32]}),
                ui.HGap(0, 1),
            ])
            linha2 = ui.HGroup({"Spacing": 8, "MaximumSize": [744, 30]}, [
                ui.HGap(96),   
            ] + [gswatch(kind, i, n, rgb) for i, (n, rgb) in enumerate(COLORS)]
              + [ui.HGap(8),
                 ui.LineEdit({"ID": "ghex_%s" % kind, "Text": "",
                              "ToolTip": "Código da cor, ex: #38bdf8",
                              "Alignment": {"AlignHCenter": True},
                              "MinimumSize": [92, 28], "MaximumSize": [112, 30]}),
                 ui.HGap(0, 1)])
            return ui.VGroup({"Spacing": 6, "Weight": 0, "MaximumSize": [744, 74]},
                             [linha1, linha2])

        def chk3(a, b, c=None):
            
            def cel(t):
                cid, label, tip = t
                return ui.CheckBox({"ID": cid, "Text": label, "ToolTip": tip,
                                    "MinimumSize": [240, 26], "MaximumSize": [258, 28]})
            return ui.HGroup({"Spacing": 8}, [cel(t) for t in (a, b, c) if t is not None] + [ui.HGap(0, 1)])

        page_gerar = ui.VGroup({"Spacing": 4, "Margin": 0}, [
            
            
            qsec("TRANSCRIÇÃO"),
            ui.VGap(2),
            ui.HGroup({"Spacing": 8, "MaximumSize": [744, 16]}, [
                ui.Label({"Text": "IDIOMA DO ÁUDIO", "StyleSheet": CAPS,
                          "MinimumSize": [230, 14], "MaximumSize": [238, 16]}),
                ui.Label({"Text": "MODO DE TRANSCRIÇÃO", "StyleSheet": CAPS,
                          "MinimumSize": [230, 14], "MaximumSize": [238, 16]}),
                ui.HGap(14),
            ]),
            ui.HGroup({"Spacing": 8, "MaximumSize": [744, 34]}, [
                
                
                
                
                ui.ComboBox({"ID": "glang", "MinimumSize": [234, 32], "MaximumSize": [234, 34]}),
                ui.ComboBox({"ID": "gmodel", "MinimumSize": [234, 32], "MaximumSize": [234, 34]}),
                ui.Button({"ID": "generate", "Text": "GERAR LEGENDAS",
                           "StyleSheet": CTA_CSS, "MinimumSize": [232, 32],
                           "MaximumSize": [232, 34]}),
                ui.HGap(0, 1),
            ]),
            ui.Label({"Text": "Deixe ativas apenas as faixas de voz. Silencie músicas e efeitos na timeline.", "WordWrap": True, "StyleSheet": SUB}),
            ui.Label({"ID": "gbar", "Text": "",
                      "MinimumSize": [716, 8], "MaximumSize": [716, 8],
                      "StyleSheet": "QLabel{background-color:#26262b;border-radius:5px;}"}),
            ui.Label({"ID": "gstatus", "Text": "", "Alignment": {"AlignHCenter": True},
                      "MinimumSize": [200, 14], "MaximumSize": [744, 16], "StyleSheet": SUB}),
            ui.VGap(10),
            
            ui.HGroup({"Spacing": 0, "Weight": 0, "MaximumSize": [744, 270]}, [
                ui.VGroup({"Spacing": 4, "Weight": 0, "MinimumSize": [400, 240],
                           "MaximumSize": [400, 262]}, [
                    qsec("COMPOSIÇÃO"),
                    ui.VGap(2),
                    ui.HGroup({"Spacing": 12, "Weight": 0,
                               "MaximumSize": [400, self.gmid_h + 4]}, [
                        ui.Label({"ID": "gpreview", "Text": "",
                                  "Alignment": {"AlignHCenter": True, "AlignVCenter": True},
                                  "WordWrap": True,
                                  "MinimumSize": [self.gprev_w, self.gprev_h],
                                  "MaximumSize": [self.gprev_w, self.gprev_h],
                                  "StyleSheet":
                                      "QLabel{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                                      "stop:0 #1b1712, stop:0.5 #141318, stop:1 #0c0c0f);"
                                      "border:1px solid #2c2c33;border-radius:14px;padding:8px;}"}),
                        ui.VGroup({"Spacing": 3, "Weight": 1,
                                   "MinimumSize": [258, self.gmid_h],
                                   "MaximumSize": [274, self.gmid_h]}, [
                            subhead("POSIÇÃO"),
                            field2("Altura", "galt", "galt_lbl", 0, 100, 61, "61"),
                            field2("Horizontal", "ghor", "ghor_lbl", 0, 100, 50, "50"),
                            field2("Tamanho", "gwidth", "gwidth_lbl", 1, 95, 60, "60%"),
                            subhead("TRACKING"),
                            field2("Principal", "gtrackH", "gtrackH_lbl", 50, 150, 96, "0.96"),
                            field2("Apoio", "gtrackA", "gtrackA_lbl", 50, 150, 96, "0.96"),
                        ]),
                    ]),
                ]),
                ui.HGap(8),
                ui.Label({"Text": "", "MinimumSize": [1, self.gmid_h - 4],
                          "MaximumSize": [1, self.gmid_h],
                          "StyleSheet": "background-color:#2c2c33;"}),
                ui.HGap(7),
                ui.VGroup({"Spacing": 6, "Weight": 1, "MinimumSize": [328, 240],
                           "MaximumSize": [328, 262]}, [
                    ui.HGroup({"Spacing": 7, "Weight": 0, "MaximumSize": [328, 20]}, [
                        ui.Label({"Text": "", "MinimumSize": [3, 13], "MaximumSize": [3, 13],
                                  "StyleSheet": "QLabel{background-color:%s;border-radius:1px;}" % ACCENT}),
                        ui.Label({"Text": QSEC_HTML % "LAYOUTS", "StyleSheet": "background:transparent;",
                                  "MinimumSize": [80, 15], "MaximumSize": [140, 17]}),
                        ui.HGap(0, 1),
                        ui.Button({"ID": "glay_auto", "Text": "AUTO", "Checkable": True,
                                   "ToolTip": "Deixa o plugin sortear um layout por bloco",
                                   "MinimumSize": [64, 22], "MaximumSize": [72, 24],
                                   "StyleSheet":
                                       "QPushButton{background-color:#26262a;color:#9a9aa0;"
                                       "border:1px solid #35353a;border-radius:7px;"
                                       "font-size:10px;padding:0px;}"
                                       "QPushButton:hover{border-color:#4a4a50;}"
                                       "QPushButton:checked{background-color:%s;"
                                       "color: #ffffff;border-color:%s;font-weight:bold;}"
                                       % (ACCENT, ACCENT)}),
                        ui.HGap(16),   
                    ]),
                    ui.HGroup({"Spacing": 0, "MaximumSize": [328, 14]}, [
                        ui.Label({"ID": "glay_info", "Text": "", "StyleSheet": SUB,
                                  "MinimumSize": [200, 13], "MaximumSize": [328, 15]}),
                        ui.HGap(0, 1),
                    ]),
                    ui.VGap(2),
                    ui.HGroup({"Spacing": 8}, [glay_btn(k, l) for k, l in LAYOUTS[0:3]] + [ui.HGap(18)]),
                    ui.HGroup({"Spacing": 8}, [glay_btn(k, l) for k, l in LAYOUTS[3:6]] + [ui.HGap(18)]),
                    ui.HGroup({"Spacing": 8}, [glay_btn(k, l) for k, l in LAYOUTS[6:9]] + [ui.HGap(18)]),
                    ui.VGap(0, 1),
                ]),
            ]),
            ui.VGap(8),
            
            qsec("FONTE E COR"),
            ui.VGap(2),
            fontcor_row_g("Principal", "m"),
            ui.VGap(4),
            fontcor_row_g("Apoio", "s"),
            ui.VGap(8),
            
            qsec("CONFIGURAÇÕES"),
            ui.VGap(2),
            chk3(("ganim_in", "Animar entrada", "Animação de entrada variada por linha e por bloco"),
                 ("ganim_out", "Animar saída", "Animação de saída (blur + opacidade)"),
                 ("gpunct", "Usar pontuação", "Manter a pontuação da fala")),
            chk3(("gcapsH", "Caixa alta principal", "Texto principal em CAIXA ALTA"),
                 ("gcapsA", "Caixa alta apoio", "Linhas de apoio em CAIXA ALTA"),
                 ("gsfx", "Efeitos sonoros", "Whoosh no Slide, impacto no Bounce, glitch no Flicker, cliques no Shake, ar no Blur e névoa no Motion Blur.")),
            ui.VGap(0, 20),
        ])

        def fonte_btn(i, nome, fam, sty):
            d = {"ID": "fnt_%d" % i, "Text": nome, "Checkable": True,
                 "MinimumSize": [300, 34], "MaximumSize": [452, 36],
                 "StyleSheet":
                     "QPushButton{background-color:#232327;"
                     "border:1px solid #3a3a40;border-radius:10px;"
                     "text-align:left;padding:4px 14px;color:#f2f2f4;}"
                     "QPushButton:hover{border-color:#5a5a60;}"
                     "QPushButton:checked{background-color:%s;"
                     "border:1px solid %s;color: #ffffff;}" % (ACCENT, ACCENT)}
            try:   
                d["Font"] = ui.Font({"Family": fam, "StyleName": sty,
                                     "PixelSize": 17})
            except Exception:
                _tv_diag.falha('Titulos Virais.build.fonte_btn')
                pass
            return ui.Button(d)

        page_fonte = ui.VGroup({"Spacing": 6, "Margin": 10}, [
            ui.HGroup({"Spacing": 8, "Weight": 0}, [
                ui.Button({"ID": "fnt_voltar", "Text": "‹ voltar", "Flat": True,
                           "MinimumSize": [70, 24], "MaximumSize": [80, 26],
                           "StyleSheet": "QPushButton{border:none;"
                                         "background:transparent;color:#9a9aa0;}"
                                         "QPushButton:hover{color:%s;}" % ACCENT}),
                ui.Label({"ID": "fnt_titulo", "Text": "",
                          "StyleSheet": "background:transparent;",
                          "MinimumSize": [200, 18], "MaximumSize": [360, 20]}),
                ui.HGap(0, 1),
            ]),
            ui.Label({"Text": "", "MinimumSize": [200, 1], "MaximumSize": [452, 1],
                      "StyleSheet": "background-color:#3a3a42;"}),
            
            
            ui.ComboBox({"ID": "fnt_combo", "MinimumSize": [300, 30], "MaximumSize": [452, 32]}),
            ui.Button({"ID": "fnt_usar", "Text": "Usar fonte",
                       "MinimumSize": [120, 32], "MaximumSize": [452, 36],
                       "StyleSheet": "QPushButton{background-color:%s;border:none;"
                                     "border-radius:10px;color: #ffffff;font-weight:bold;}"
                                     "QPushButton:hover{background-color:%s;}" % (ACCENT, ACCENT)}),
            ui.VGap(0, 1),
        ])

        page_design = ui.VGroup({"Spacing": 8, "Margin": 10}, [
            ui.Label({"Text": "Escolha um estilo para aplicar às linhas sob o playhead.",
                      "StyleSheet": SUB, "MaximumSize": [452, 18]}),
            sec("LAYOUT"),
            ui.HGroup({"Spacing": 6}, [lay_btn(k, l) for k, l in LAYOUTS[0:3]] + [ui.HGap(0, 1)]),
            ui.HGroup({"Spacing": 6}, [lay_btn(k, l) for k, l in LAYOUTS[3:6]] + [ui.HGap(0, 1)]),
            ui.HGroup({"Spacing": 6}, [lay_btn(k, l) for k, l in LAYOUTS[6:9]] + [ui.HGap(0, 1)]),
            sec("FONTE E COR"),
            ui.Label({"Text": "aplica só no bloco sob o playhead",
                      "StyleSheet": SUB, "MaximumSize": [452, 16]}),
        ] + style_rows("d") + [
            sec("AJUSTES"),
            slider_row("Tamanho", "width", "width_lbl", 1, 95, 60, "60%"),
            ui.HGroup({"Spacing": 8}, [
                ui.Label({"Text": "Posição X", "StyleSheet": ROWLBL,
                          "MinimumSize": [58, 18], "MaximumSize": [58, 20]}),
                ui.Slider({"Tracking": True, "Events": {"SliderMoved": True}, "ID": "posx", "Minimum": 0, "Maximum": 100, "Value": 50,
                           "Orientation": "Horizontal", "MaximumSize": [268, 22]}),
                ui.LineEdit({"ID": "posx_lbl", "Text": "0.50", "StyleSheet": NUM_CSS,
                          "Alignment": {"AlignRight": True},
                          "MinimumSize": [44, 18], "MaximumSize": [46, 20]}),
                ui.HGap(66),
            ]),
            ui.HGroup({"Spacing": 8}, [
                ui.Label({"Text": "Posição Y", "StyleSheet": ROWLBL,
                          "MinimumSize": [58, 18], "MaximumSize": [58, 20]}),
                ui.Slider({"Tracking": True, "Events": {"SliderMoved": True}, "ID": "posy", "Minimum": 0, "Maximum": 100, "Value": 50,
                           "Orientation": "Horizontal", "MaximumSize": [268, 22]}),
                ui.LineEdit({"ID": "posy_lbl", "Text": "0.50", "StyleSheet": NUM_CSS,
                          "Alignment": {"AlignRight": True},
                          "MinimumSize": [44, 18], "MaximumSize": [46, 20]}),
                ui.Button({"ID": "poscenter", "Text": "centro",
                           "MinimumSize": [58, 22], "MaximumSize": [62, 24]}),
                ui.HGap(4),
            ]),
            ui.Button({"ID": "pos_all", "Text": "Aplicar posição a todos",
                       "ToolTip": "Aplica X e Y a todos os Text+ desta timeline. Alterações seguintes continuam locais.",
                       "MinimumSize": [250, 32], "MaximumSize": [452, 36], "StyleSheet": CTA_CSS}),
            ui.Label({"ID": "pos_all_status", "Text": "", "WordWrap": True, "MaximumSize": [452, 40], "StyleSheet": SUB}),
            ui.VGap(0, 12),
        ])

        page_anim = ui.VGroup({"Spacing": 8, "Margin": 10}, [
            ui.Label({"Text": "Entrada desacelera, saída acelera. Só nas linhas selecionadas.",
                      "StyleSheet": SUB, "MaximumSize": [452, 18]}),
            sec("ENTRADA E SAÍDA"),
            ui.HGroup({"Spacing": 10}, [
                anim_side("in", "ENTRADA"),
                anim_side("out", "SAÍDA"),
                ui.HGap(0, 1),
            ]),
            ui.Button({"ID": "sfx_map_open", "Text": "Sons por animação…",
                       "ToolTip": "Escolha o som de cada animação e aplique aos títulos correspondentes.",
                       "MinimumSize": [250, 32], "MaximumSize": [452, 36], "StyleSheet": CTA_CSS}),
            sec("AJUSTES"),
            slider_row("Duração", "dur", "dur_lbl", 2, 60, 20, "20f"),
            slider_row("Distância", "dist", "dist_lbl", 2, 50, 15, "15"),
            ui.HGroup({"Spacing": 6}, [
                ui.CheckBox({"ID": "asfx", "Text": "Efeitos sonoros", "MinimumSize": [140, 22]}),
                ui.CheckBox({"ID": "mblur", "Text": "Motion Blur",
                             "MinimumSize": [130, 22], "MaximumSize": [150, 24]}),
                ui.HGap(16),
                ui.Button({"ID": "reset_anim", "Text": "Limpar animação",
                           "MinimumSize": [120, 24], "MaximumSize": [140, 28]}),
                ui.Button({"ID": "debug", "Text": "Debug",
                           "MinimumSize": [60, 24], "MaximumSize": [70, 28]}),
                ui.HGap(0, 1),
            ]),
            
            ui.HGroup({"Spacing": 8, "Weight": 0}, [
                ui.VGroup({"Spacing": 4, "Weight": 0}, [
                    ui.Label({"Text": SECT_HTML % "PRÉVIA",
                              "StyleSheet": "background:transparent;",
                              "MinimumSize": [60, 15], "MaximumSize": [120, 17]}),
                    ui.Label({"ID": "preview", "Text": "",
                              "Alignment": {"AlignHCenter": True, "AlignTop": True},
                              "WordWrap": True,
                              "MinimumSize": [self.prev_w, self.prev_h],
                              "MaximumSize": [self.prev_w, self.prev_h],
                              "StyleSheet": "background-color:#0e0e11;"
                                            "border:1px solid #26262b;"
                                            "border-radius:10px; padding:4px;"}),
                    ui.VGap(0, 1),
                ]),
                ui.VGroup({"Spacing": 4, "Weight": 1}, [
                    ui.Label({"Text": SECT_HTML % "LINHAS SOB O PLAYHEAD",
                              "StyleSheet": "background:transparent;",
                              "MinimumSize": [150, 15], "MaximumSize": [180, 17]}),
                    ui.Tree({"ID": "tree", "SelectionMode": "ExtendedSelection",
                             "RootIsDecorated": False, "AlternatingRowColors": True,
                             "Weight": 1, "MinimumSize": [316, 110], "MaximumSize": [9999, 132],
                             "Events": {"ItemSelectionChanged": True, "ItemClicked": True,
                                        "CurrentItemChanged": True}}),
                    ui.HGroup({"Spacing": 6}, [
                        ui.Button({"ID": "sel_all", "Text": "Todas", "MaximumSize": [80, 26]}),
                        ui.Button({"ID": "sel_none", "Text": "Nenhuma", "MaximumSize": [80, 26]}),
                        ui.Button({"ID": "refresh", "Text": "↻",
                                   "ToolTip": "Reler os Text+ sob o playhead",
                                   "MinimumSize": [26, 22], "MaximumSize": [28, 26]}),
                        ui.HGap(0, 1),
                    ]),
                    ui.HGroup({"Spacing": 6}, [
                        ui.Label({"Text": "Sem seleção = todas · 1 = principal",
                                  "MinimumSize": [160, 14], "MaximumSize": [200, 16],
                                  "StyleSheet": "color:#77777d;font-size:10px;background:transparent;"}),
                        ui.HGap(0, 1),
                        ui.Label({"Text": APP_VERSION, "MinimumSize": [44, 14], "MaximumSize": [60, 16],
                                  "StyleSheet": "color:%s;font-size:10px;font-weight:bold;"
                                                "background:transparent;" % ACCENT}),
                    ]),
                ]),
            ]),
            ui.VGap(0, 30),
        ])

        
        TAB_CSS = ("QPushButton{background-color:#111622; border:1px solid #232d3f;"
                   "border-radius:8px; padding:10px 8px; font-size:12px;"
                   "font-weight:bold; letter-spacing:1.2px; color:#8b949e;}"
                   "QPushButton:hover{color:#f0f6fc; border-color:#38bdf8; background-color:#161f30;}"
                   "QPushButton:checked{background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #172554, stop:1 #0f172a);"
                   "color:#38bdf8; border:1.5px solid #38bdf8;}")

        def tab_btn(i, label):
            d = {"ID": "tab_%d" % i, "Text": " " + label, "Checkable": True,
                 "Weight": 1, "StyleSheet": TAB_CSS,
                 "MinimumSize": [86, 40], "MaximumSize": [148, 42]}
            ic = icon("num%d_off" % (i + 1))
            if ic:
                d["Icon"] = ic
                d["IconSize"] = [20, 20]
            return ui.Button(d)

        logo_ic = icon("titan_logo") or icon("logo")
        logo_btn = {"ID": "logo", "Text": "", "Flat": True,
                    "MinimumSize": [46, 46], "MaximumSize": [48, 48],
                    "StyleSheet": "QPushButton{border:none;background:transparent;}"}
        if logo_ic:
            logo_btn["Icon"] = logo_ic
            logo_btn["IconSize"] = [44, 44]

        
        
        
        geo = [200, 40, 820, 900]
        try:      
            g = fusion.GetData("TitulosVirais.winGeo")
            if g:
                v = [int(float(x)) for x in str(g).split(",")]
                if len(v) == 4 and v[2] > 300 and v[3] > 300:
                    geo = v
        except Exception:
            _tv_diag.falha('Titulos Virais.build')
            pass
        
        
        
        geo[2] = 820 if (geo[2] < 790 or geo[2] > 900) else geo[2]
        geo[3] = max(700, min(geo[3], 940))
        _tv_diag.evento("janela.geometria", solicitada=geo, plataforma=sys.platform)
        self.win = disp.AddWindow({
            "ID": WIN_ID, "WindowTitle": "%s %s" % (APP_NAME, APP_VERSION),
            "Geometry": geo,
            "WindowFlags": {"Window": True, "WindowStaysOnTopHint": True},
            "StyleSheet": STYLE,
        }, [
            ui.VGroup({"Spacing": 8, "Margin": 20,
                       "MinimumSize": [780, 700], "MaximumSize": [840, 10000]}, [
                
                ui.HGroup({"Spacing": 6, "Weight": 0}, [
                    ui.VGroup({"Spacing": 1, "Weight": 0}, [
                        ui.Label({"Text": "<img src='%s/titan_word.png' width='185' height='38'>" % ICON_URL,
                                  "MinimumSize": [185, 38], "MaximumSize": [200, 40],
                                  "StyleSheet": "background:transparent;"}),
                    ]),
                    ui.HGap(0, 1),
                    ui.ComboBox({"ID": "ui_language", "ToolTip": "Idioma da interface",
                                 "MinimumSize": [134, 28], "MaximumSize": [152, 32]}),
                    ui.Button({"ID": "about", "Text": "About", "MaximumSize": [80, 28]}),
                    ui.Button({"ID": "abrir_logs", "Text": texto_acesso("Abrir logs", "Abrir registros"),
                               "MaximumSize": [110, 28], "MinimumSize": [95, 26]}),
                    ui.VGroup({"Spacing": 2, "MinimumSize": [126, 40],
                               "MaximumSize": [142, 44]}, [
                        ui.Label({"ID": "status", "Text": "", "StyleSheet": SUB,
                                  "Alignment": {"AlignRight": True},
                                  "MinimumSize": [124, 16], "MaximumSize": [140, 18]}),
                        ui.Button({"ID": "reparar_acesso", "Text": "Corrigir acesso", "Flat": True}),
                        ui.Button({"ID": "sair", "Text": "sair", "Flat": True,
                                   "Hidden": not LICENCA_ATIVA,
                                   "MinimumSize": [124, 18], "MaximumSize": [140, 20],
                                   "StyleSheet": "QPushButton{border:none;"
                                                 "background:transparent;color:#77777d;"
                                                 "text-align:right;}"
                                                 "QPushButton:hover{color:%s;}" % ACCENT}),
                    ]),
                    ui.HGap(4),
                ]),
                
                ui.HGroup({"ID": "cx_update", "Spacing": 8, "Weight": 0,
                           "Hidden": True, "MaximumSize": [452, 30]}, [
                    ui.Label({"ID": "up_txt", "Text": "", "WordWrap": False,
                              "StyleSheet": "color:#38bdf8;background:transparent;",
                              "MinimumSize": [200, 24], "MaximumSize": [330, 26]}),
                    ui.Button({"ID": "up_btn", "Text": "Baixar",
                               "MinimumSize": [72, 24], "MaximumSize": [76, 26],
                               "StyleSheet":
                                   "QPushButton{background-color:%s;color: #ffffff;"
                                   "border:none;border-radius:7px;font-weight:bold;}"
                                   % ACCENT}),
                    ui.HGap(0, 1),
                ]),
                
                ui.Label({"Text": "", "MinimumSize": [200, 2], "MaximumSize": [452, 2],
                          "StyleSheet": "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                                        "stop:0 #38bdf8, stop:0.45 #1e40af, stop:1 #0b0f17);"}),
                ui.HGroup({"Spacing": 6}, [
                    tab_btn(0, "LEGENDAS"),
                    tab_btn(1, "TÍTULOS"),
                    tab_btn(2, "ANIMAÇÕES"),
                ]),
                ui.VGroup({"Weight": 1}, [
                    ui.Stack({"ID": "stack"}, [page_gerar, page_design, page_anim,
                                              page_fonte]),
                ]),
            ]),
        ])
        self.items = _locale.wrap_items(self.win.GetItems())
        self.tree = self.items["tree"]
        for language_name in _locale.LANGUAGE_NAMES:
            self.items["ui_language"].AddItem(language_name)
        self.items["ui_language"].CurrentIndex = _locale.LANGUAGES.index(UI_LANGUAGE)
        for nm in ("Automático", "Português", "English", "Español",
                   "Deutsch", "Français", "Italiano"):
            self.items["glang"].AddItem(nm)
        
        self._try(lambda: setattr(self.items["glang"], "CurrentIndex",
                                  {"pt": 1, "es": 3}.get(IDIOMA, 1)))
        self.items["gmodel"].AddItem("Alta (recomendado)")
        for (nm, _fs) in FONTS:               
            self._try(lambda nm=nm: self.items["fnt_combo"].AddItem(nm))
            self._try(lambda nm=nm: self.items["gfam_m"].AddItem(nm))
            self._try(lambda nm=nm: self.items["gfam_s"].AddItem(nm))
        self.hero_font_idx = FONT_MAIN_DEF     
        self.small_font_idx = FONT_SEC_DEF      
        self.hero_color_idx = 1                 
        self.small_color_idx = 0                
        
        self.hero_style = None
        self.small_style = None
        
        self.hero_color_rgb = None
        self.small_color_rgb = None
        self._load_prefs()
        for side in ("in", "out"):
            for label in _sound_module.LABELS:
                self.items[side + "_sound"].AddItem(tr(label))
            self.items[side + "_sound"].CurrentIndex = 0
        self.items["gsfx"].Checked = self.sfx_enabled
        self.items["asfx"].Checked = self.sfx_enabled

        self.sync_gen_layouts()

        
        
        for _cb in ("ganim_in", "ganim_out"):
            try:
                self.items[_cb].Checked = True
            except Exception:
                _tv_diag.falha('Titulos Virais.build')
                pass
        try:
            self.items["tab_0"].Checked = True   
            self.items["stack"].CurrentIndex = 0
        except Exception:
            _tv_diag.falha('Titulos Virais.build')
            pass
        hdr = self.tree.NewItem()
        hdr.Text[0] = "#"
        hdr.Text[1] = tr("Faixa")
        hdr.Text[2] = tr("Texto")
        self.tree.SetHeaderItem(hdr)
        try:
            self.tree.ColumnWidth[0] = 26
            self.tree.ColumnWidth[1] = 44
            self.tree.ColumnWidth[2] = 190
        except Exception:
            _tv_diag.falha('Titulos Virais.build')
            pass
        self.wire()
        self.sync_style()
        self.sync_slider_labels()
        
        _hf = FONTS[self.hero_font_idx][1]
        _sf = FONTS[self.small_font_idx][1]
        self._popular_estilos("gest_m", _hf[0], getattr(self, "_estilo_saved_m", None) or _hf[1])
        self._popular_estilos("gest_s", _sf[0], getattr(self, "_estilo_saved_s", None) or _sf[1])
        self._try(self._gsliders)   
        self.on_tab(0)   
        self.refresh(force=True)

    
    def _on(self, elem_id, event, fn):
        """win.On.<id>.<event> = fn, com ID dinâmico."""
        setattr(getattr(self.win.On, elem_id), event, fn)

    def wire(self):
        self._syncing = False
        self._on(WIN_ID, "Close", self.on_close)
        self._on("refresh", "Clicked", lambda ev: self.refresh(force=True))
        self._on("sel_all", "Clicked", lambda ev: self._try(self.tree.SelectAll))
        self._on("sel_none", "Clicked", lambda ev: self._try(self.tree.ClearSelection))
        self._on("tree", "ItemSelectionChanged", lambda ev: self.sync_buttons())
        self._on("tree", "ItemClicked", lambda ev: self.sync_buttons())
        self._on("tree", "CurrentItemChanged", lambda ev: self.sync_buttons())
        for k, _ in LAYOUTS:
            self._on("lay_" + k, "Clicked", self._mk(self.on_layout, k))
            self._on("glay_" + k, "Clicked", self._mk(self.on_gen_layout, k))
        self._on("glay_auto", "Clicked", self._mk(self.on_gen_auto))
        self._on("up_btn", "Clicked", self._mk(self.on_baixar_update))

        for side in ("in", "out"):
            self._on(side + "_sound", "CurrentIndexChanged", self._mk(self.on_sound_choice, side))
            for a in ("slide", "bounce", "flicker", "shake", "blur"):
                self._on(side + "_" + a, "Clicked", self._mk(self.on_anim, side, a))
            for d in ("left", "right", "up", "down", "none"):
                self._on(side + "_" + d, "Clicked", self._mk(self.on_dir, side, d))
        for cb in ("mblur",):
            self._on(cb, "Clicked", self._mk(self.on_flag, cb))
        self._on("width", "ValueChanged", self._mk(self.on_layout_param))
        self._on("posx", "ValueChanged", self._mk(self.on_pos))
        self._on("posy", "ValueChanged", self._mk(self.on_pos))
        self._on("poscenter", "Clicked", self._mk(self.on_pos_center))
        self._on("pos_all", "Clicked", self._mk(self.on_apply_position_all))
        self._on("sfx_map_open", "Clicked", self._mk(self.on_open_sfx_map))
        self._on("ui_language", "CurrentIndexChanged", self._mk(self.on_ui_language))
        self._on("about", "Clicked", self._mk(self.on_about))
        self._on("gsfx", "Clicked", self._mk(self.on_sfx_setting, "gsfx"))
        self._on("asfx", "Clicked", self._mk(self.on_sfx_setting, "asfx"))
        self._on("galt", "ValueChanged", self._mk(self._gsliders))
        self._on("ghor", "ValueChanged", self._mk(self._gsliders))
        self._on("gwidth", "ValueChanged", self._mk(self._gsliders))
        self._on("gtrackH", "ValueChanged", self._mk(self._gsliders))
        self._on("gtrackA", "ValueChanged", self._mk(self._gsliders))
        for sid in ("galt", "ghor", "gwidth", "gtrackH", "gtrackA"):
            self._on(sid, "SliderMoved", self._mk(self._poll_gsliders))
        for sid, factor, callback in (("galt", 1, self._gsliders), ("ghor", 1, self._gsliders),
                ("gwidth", 1, self._gsliders), ("gtrackH", 100, self._gsliders),
                ("gtrackA", 100, self._gsliders), ("width", 1, self.on_layout_param),
                ("posx", 100, self.on_pos), ("posy", 100, self.on_pos),
                ("dur", 1, self.on_timing), ("dist", 1, self.on_timing)):
            self._on(sid + "_lbl", "EditingFinished", self._mk(self._numero_confirmar, sid, factor, callback))
        self._on("gcapsH", "Clicked", self._mk(lambda: self._try(self._gpreview)))
        self._on("gcapsA", "Clicked", self._mk(lambda: self._try(self._gpreview)))
        for sid in ("width", "dur", "dist"):
            self._on(sid, "SliderMoved", self._mk(self._poll_edit_sliders))
        self._edit_sliders_ultimo = tuple(int(self.items[s].Value) for s in ("width", "dur", "dist"))
        self._on("dur", "ValueChanged", self._mk(self.on_timing))
        self._on("dist", "ValueChanged", self._mk(self.on_timing))
        self._on("reset_anim", "Clicked", self._mk(self.on_reset))
        self._on("debug", "Clicked", self._mk(self.on_debug))
        for i in range(3):
            self._on("tab_%d" % i, "Clicked", self._mk(self.on_tab, i))
        self._on("abrir_logs", "Clicked", self._mk(self.on_abrir_logs))
        self._on("sair", "Clicked", self._mk(self.on_sair))
        self._on("reparar_acesso", "Clicked", self._mk(self.on_reparar_acesso))
        self._on("fnt_voltar", "Clicked", self._mk(self._voltar_da_fonte))
        self._on("fnt_usar", "Clicked", self._mk(self._usar_fonte_combo))
        for pfx in ("g", "d"):
            self._on(pfx + "fmain", "Clicked",
                     self._mk(self.open_font_picker, True, pfx))
            self._on(pfx + "fsec", "Clicked",
                     self._mk(self.open_font_picker, False, pfx))
            for i in range(len(COLORS)):
                self._on("%sm_%d" % (pfx, i), "Clicked",
                         self._mk(self.on_style_color, i, True, pfx))
                self._on("%ss_%d" % (pfx, i), "Clicked",
                         self._mk(self.on_style_color, i, False, pfx))
        
        
        self._on("gfam_m", "CurrentIndexChanged", self._mk(self.on_fam, "m"))
        self._on("gfam_s", "CurrentIndexChanged", self._mk(self.on_fam, "s"))
        self._on("gest_m", "CurrentIndexChanged", self._mk(self.on_estilo, "m"))
        self._on("gest_s", "CurrentIndexChanged", self._mk(self.on_estilo, "s"))
        
        self._on("ghex_m", "EditingFinished", self._mk(self.on_hex, "m"))
        self._on("ghex_s", "EditingFinished", self._mk(self.on_hex, "s"))
        self._on("ghex_m", "TextEdited", self._mk(self.on_hex_digitado))
        self._on("ghex_s", "TextEdited", self._mk(self.on_hex_digitado))
        self._on("generate", "Clicked", self._mk(self.on_generate))

    def on_ui_language(self):
        global UI_LANGUAGE
        if getattr(self, "_syncing", False):
            return
        index = int(self.items["ui_language"].CurrentIndex)
        if not 0 <= index < len(_locale.LANGUAGES):
            return
        language = _locale.LANGUAGES[index]
        if language == UI_LANGUAGE:
            return
        if getattr(self, "_busy", False):
            self.items["ui_language"].CurrentIndex = _locale.LANGUAGES.index(UI_LANGUAGE)
            return
        self._save_prefs()
        fusion.SetData("TitanTitlesStudio.uiLanguage", language)
        UI_LANGUAGE = _locale.configure(language)
        self._restart_language = True
        self._exit = True
        self._close_about()
        disp.ExitLoop()

    def _close_about(self):
        window = getattr(self, "about_window", None)
        if window:
            self.about_window = None
            window.Hide()
            window.Close()

    def on_about(self):
        if getattr(self, "about_window", None):
            self.about_window.Show()
            return
        window = self.about_window = disp.AddWindow({"ID": "TitanAbout", "WindowTitle": tr("Sobre o Titan Titles Studio"),
            "Geometry": [460, 220, 520, 430], "StyleSheet": STYLE,
            "WindowFlags": {"Window": True, "WindowStaysOnTopHint": True}}, [
            ui.VGroup({"Spacing": 12, "Margin": 24}, [
                ui.Label({"Text": APP_NAME, "StyleSheet": "font-size:24px;font-weight:bold;color:#38bdf8;"}),
                ui.HGroup({"Spacing": 8}, [
                    ui.Label({"Text": "Versão " + APP_VERSION}),
                    ui.Button({"ID": "about_update_btn", "Text": "Buscar atualizações"}),
                ]),
                ui.Label({"ID": "about_update_status", "Text": ""}),
                ui.Label({"Text": "Direitos de criação: RangelMaker_"}),
                ui.Label({"Text": "Todos os direitos reservados."}),
                ui.Button({"ID": "about_rangel", "Text": "Instagram · @RangelMaker_"}),
                ui.Button({"ID": "about_wilder", "Text": "Instagram · @oWilder.cine"}),
                ui.Button({"ID": "about_telegram", "Text": "Comunidade no Telegram"}),
                ui.Button({"ID": "about_close", "Text": "Fechar"}),
            ])])
        window.On.TitanAbout.Close = lambda ev: self._close_about()
        window.On.about_close.Clicked = lambda ev: self._close_about()
        window.On.about_update_btn.Clicked = lambda ev: self.on_about_update()
        window.On.about_rangel.Clicked = lambda ev: abrir_link("https://www.instagram.com/RangelMaker_/")
        window.On.about_wilder.Clicked = lambda ev: abrir_link("https://www.instagram.com/oWilder.cine/")
        window.On.about_telegram.Clicked = lambda ev: abrir_link("https://t.me/+y2SoJmZgRTwyOTI5")
        window.Show()

    def on_apply_position_all(self):
        if getattr(self, "_busy", False):
            return
        cx = float(self.items["posx"].Value) / 100.0
        cy = float(self.items["posy"].Value) / 100.0
        _, timeline = get_timeline()
        if not timeline:
            self.items["status"].Text = "Sem timeline"
            return
        entries = find_textplus_under_playhead(timeline, all_titles=True)
        if not entries:
            self.items["status"].Text = "Nenhum título Text+ encontrado."
            return
        applied = sum(1 for entry in entries if set_move(entry, cx - 0.5, cy - 0.5))
        self.refresh(force=True)
        message = (("Posição aplicada a %d títulos." % applied) if applied == len(entries)
                   else "Não foi possível aplicar a posição a %d títulos." % (len(entries) - applied))
        self.items["status"].Text = message
        self.items["pos_all_status"].Text = message

    def on_sound_choice(self, side):
        if self._syncing:
            return
        index = int(self.items[side + "_sound"].CurrentIndex)
        if not 0 <= index < len(_sound_module.CHOICES):
            return
        choice = _sound_module.CHOICES[index]
        self.refresh()
        entries = self.selected()
        for entry in entries:
            state = self.anim.state(entry)
            state["sfx_" + side] = choice
            self._anim_salvar(entry, state)
        self._sync_sounds(entries)
        self.sync_buttons()

    def _mapped_sound_for_state(self,state,side):
        for key in ("mblur","flicker","shake","bounce","slide","blur"):
            active=key in state.get(side,set()) if key!="mblur" else bool(state.get("mblur"))
            if not active:continue
            choice=fusion.GetData("TitanTitlesStudio.sfxMap."+key)
            if choice in _sound_module.CHOICES:return choice
        return None

    def on_open_sfx_map(self):
        window=getattr(self,"sfx_map_window",None)
        if window:
            window.Show()
            return
        rows=[]
        for key,label in _sound_module.ANIMATION_SOUNDS:
            combo_id="sfx_map_"+key
            rows.append(ui.HGroup({"Spacing":8},[
                ui.Label({"Text":tr(label),"MinimumSize":[105,24],"MaximumSize":[120,26]}),
                ui.ComboBox({"ID":combo_id,"MinimumSize":[180,26]}),
                ui.Button({"ID":combo_id+"_apply","Text":tr("Aplicar aos títulos"),
                           "MinimumSize":[145,28],"MaximumSize":[170,30]}),
            ]))
        rows.extend([
            ui.Label({"ID":"sfx_map_status","Text":"","WordWrap":True}),
            ui.Button({"ID":"sfx_map_close","Text":tr("Fechar"),"MinimumSize":[100,30]}),
        ])
        window=self.sfx_map_window=disp.AddWindow({"ID":"TitanSoundMap","WindowTitle":tr("Sons por animação"),
            "Geometry":[500,260,560,390],"StyleSheet":STYLE},[
            ui.VGroup({"Spacing":10,"Margin":18},[
                ui.Label({"Text":tr("Escolha o efeito sonoro para cada animação. Aplicar atualiza todos os títulos com essa animação."),"WordWrap":True}),
                *rows,
            ])])
        self.sfx_map_items=_locale.wrap_items(window.GetItems())
        for key,label in _sound_module.ANIMATION_SOUNDS:
            combo=self.sfx_map_items["sfx_map_"+key]
            for sound_label in _sound_module.LABELS:
                combo.AddItem(tr(sound_label))
            saved=fusion.GetData("TitanTitlesStudio.sfxMap."+key) or "auto"
            combo.CurrentIndex=_sound_module.CHOICES.index(saved) if saved in _sound_module.CHOICES else 0
            getattr(window.On,"sfx_map_"+key+"_apply").Clicked=self._mk(self.on_apply_sfx_map,key)
        window.On.sfx_map_close.Clicked=lambda ev:self._close_sfx_map()
        window.On.TitanSoundMap.Close=lambda ev:self._close_sfx_map()
        window.Show()

    def _close_sfx_map(self):
        window=getattr(self,"sfx_map_window",None)
        if window:
            window.Hide()
            self.sfx_map_window=None

    def on_apply_sfx_map(self,key):
        if getattr(self,"_busy",False):return
        choice_idx=int(self.sfx_map_items["sfx_map_"+key].CurrentIndex)
        if not 0<=choice_idx<len(_sound_module.CHOICES):return
        choice=_sound_module.CHOICES[choice_idx]
        fusion.SetData("TitanTitlesStudio.sfxMap."+key,choice)
        self.refresh(force=True)
        _project,timeline=get_timeline()
        if not timeline:
            self.sfx_map_items["sfx_map_status"].Text=tr("Sem timeline")
            return
        all_entries=find_textplus_under_playhead(timeline,all_titles=True)
        changed=[]
        for entry in all_entries:
            state=self._anim_carregar(entry)
            matched=False
            for side in ("in","out"):
                active=key in state.get(side,set()) if key!="mblur" else bool(state.get("mblur"))
                if active:
                    state["sfx_"+side]=choice
                    matched=True
            if matched:
                self._anim_salvar(entry,state)
                changed.append(entry)
        self._sync_sounds(changed)
        self.sync_buttons()
        status=(tr("Som aplicado a %d títulos.")%len(changed) if changed else tr("Nenhum título usa essa animação."))
        self.sfx_map_items["sfx_map_status"].Text=status
        self._gstatus(status)

    def on_sfx_setting(self, identity):
        self.sfx_enabled = bool(self.items[identity].Checked)
        self.items["gsfx"].Checked = self.sfx_enabled
        self.items["asfx"].Checked = self.sfx_enabled
        fusion.SetData("TitanTitlesStudio.sfxEnabled", 1 if self.sfx_enabled else 0)
        self._gstatus("Efeitos sonoros ativados." if self.sfx_enabled else
                      "Efeitos sonoros desativados. Sons existentes permanecem até reaplicar a animação.")

    def _sync_sounds(self, entries):
        if not entries:
            return
        project, timeline = get_timeline()
        if not project or not timeline:
            return
        try:
            self._sfx.sync(project, timeline, entries, self.anim.state, self.anim.dur, self.sfx_enabled)
        except Exception as erro:
            _tv_diag.falha("Titan.sfx.sync", erro)
            detail = str(erro)[:180]
            self.items["status"].Text = "Falha nos efeitos sonoros"
            self.items["status"].ToolTip = "Não foi possível sincronizar os efeitos sonoros: " + detail
            self._gstatus("Falha ao inserir efeitos sonoros: " + detail)

    def on_abrir_logs(self):
        try:
            pasta = _tv_diag.abrir_pasta()
            self._gstatus(texto_acesso("Pasta de logs: ", "Carpeta de registros: ") + pasta)
        except Exception as erro:
            self._gstatus(texto_acesso("Não foi possível abrir os logs: ", "No se pudieron abrir los registros: ") + str(erro))

    def on_reparar_acesso(self):
        if garantir_acesso():
            self._gstatus(texto_acesso("Acesso verificado. Você pode gerar as legendas.", "Acceso verificado. Puedes generar los subtítulos."))

    def on_sair(self):
        """Sai da conta neste computador. Não gasta vaga: ao entrar de novo o
        servidor reconhece a mesma máquina."""
        d = licenca_ler()
        quem = d.get("email") or ""
        self.items["status"].Text = "saindo…"
        licenca_sair()
        log("sessão encerrada%s" % ((" (%s)" % quem) if quem else ""))
        self.items["status"].Text = "conta desconectada"
        self.items["sair"].Hidden = True
        self._gstatus("Você saiu da conta. Feche e abra o plugin para entrar de novo.")

    def on_tab(self, i):
        self._syncing = True
        try:
            for j in range(3):
                self.items["tab_%d" % j].Checked = (j == i)
                ic = icon("num%d_%s" % (j + 1, "on" if j == i else "off"))
                if ic:
                    try:
                        self.items["tab_%d" % j].Icon = ic
                    except Exception:
                        _tv_diag.falha('Titulos Virais.on_tab')
                        pass
        finally:
            self._syncing = False
        self.tab_atual = i
        self.items["stack"].CurrentIndex = i

    
    PREF = "TitulosVirais."

    def _load_prefs(self):
        self.sfx_enabled = True
        try:
            value = fusion.GetData("TitanTitlesStudio.sfxEnabled")
            if value is not None:
                self.sfx_enabled = bool(int(value))
        except Exception:
            pass
        for chave, attr, teto in (("fontMain", "hero_font_idx", len(FONTS)),
                                  ("fontSec", "small_font_idx", len(FONTS)),
                                  ("colorMain", "hero_color_idx", len(COLORS)),
                                  ("colorSec", "small_color_idx", len(COLORS))):
            try:
                v = fusion.GetData(self.PREF + chave)
                if v is not None and 0 <= int(v) < teto:
                    setattr(self, attr, int(v))
            except Exception:
                _tv_diag.falha('Titulos Virais._load_prefs')
                pass
        
        for chave, attr in (("colorMainHex", "hero_color_rgb"),
                            ("colorSecHex", "small_color_rgb")):
            try:
                h = fusion.GetData(self.PREF + chave)
                rgb = self._hex2rgb(str(h)) if h else None
                setattr(self, attr, rgb)
            except Exception:
                _tv_diag.falha('Titulos Virais._load_prefs')
                pass
        
        try:
            self._estilo_saved_m = fusion.GetData(self.PREF + "estiloMain") or None
            self._estilo_saved_s = fusion.GetData(self.PREF + "estiloSec") or None
        except Exception:
            _tv_diag.falha('Titulos Virais._load_prefs')
            self._estilo_saved_m = self._estilo_saved_s = None
        try:
            v = fusion.GetData(self.PREF + "genLayouts")
            if v:
                validos = [k for k, _ in LAYOUTS]
                sel = [k for k in str(v).split(",") if k in validos][:GEN_LAY_MAX]
                if sel:
                    self.gen_layouts = sel
            _ga = fusion.GetData(self.PREF + "genAuto")
            if _ga is not None:              
                self.gen_auto = bool(int(_ga))
        except Exception:
            _tv_diag.falha('Titulos Virais._load_prefs')
            pass

    def _save_prefs(self):
        
        
        for chave, attr in (("fontMain", "hero_font_idx"), ("fontSec", "small_font_idx"),
                            ("colorMain", "hero_color_idx"), ("colorSec", "small_color_idx")):
            try:
                v = int(getattr(self, attr))
                if v >= 0:
                    fusion.SetData(self.PREF + chave, v)
            except Exception:
                _tv_diag.falha('Titulos Virais._save_prefs')
                pass
        for chave, attr in (("colorMainHex", "hero_color_rgb"),
                            ("colorSecHex", "small_color_rgb")):
            try:
                rgb = getattr(self, attr)
                fusion.SetData(self.PREF + chave, self._rgb2hex(rgb) if rgb else "")
            except Exception:
                _tv_diag.falha('Titulos Virais._save_prefs')
                pass
        for chave, cid in (("estiloMain", "gest_m"), ("estiloSec", "gest_s")):
            try:
                fusion.SetData(self.PREF + chave, self._estilo_de(cid) or "")
            except Exception:
                _tv_diag.falha('Titulos Virais._save_prefs')
                pass
        try:
            fusion.SetData(self.PREF + "genLayouts", ",".join(self.gen_layouts))
            fusion.SetData(self.PREF + "genAuto", 1 if self.gen_auto else 0)
        except Exception:
            _tv_diag.falha('Titulos Virais._save_prefs')
            pass

    def _combo_font(self, cid, fam, sty):
        """O próprio campo é a prévia: fica escrito na fonte escolhida."""
        if cid not in self.items:
            return
        try:
            self.items[cid].Font = ui.Font({"Family": fam, "StyleName": sty,
                                            "PixelSize": 13})
        except Exception:
            _tv_diag.falha('Titulos Virais._combo_font')
            pass

    
    @staticmethod
    def _hex2rgb(s):
        s = (s or "").strip().lstrip("#")
        if len(s) == 3:
            s = "".join(c * 2 for c in s)
        if len(s) != 6:
            return None
        try:
            return (int(s[0:2], 16) / 255.0, int(s[2:4], 16) / 255.0,
                    int(s[4:6], 16) / 255.0)
        except Exception:
            _tv_diag.falha('Titulos Virais._hex2rgb')
            return None

    @staticmethod
    def _rgb2hex(rgb):
        return "#%02X%02X%02X" % tuple(int(round(c * 255)) for c in rgb)

    def _cor_hero(self):
        return self.hero_color_rgb or COLORS[self.hero_color_idx][1]

    def _cor_small(self):
        return self.small_color_rgb or COLORS[self.small_color_idx][1]

    def _estilo_de(self, cid):
        """Estilo selecionado no ComboBox (lido direto — combos aqui não são
        amarrados a evento). '' -> None (usa o estilo padrão da família)."""
        combo = self.items.get(cid)
        if combo is None:
            return None
        try:
            t = str(combo.CurrentText).strip()
            return t or None
        except Exception:
            _tv_diag.falha('Titulos Virais._estilo_de')
            return None

    def _fonte_hero(self):
        fam, sty = FONTS[self.hero_font_idx][1]
        return (fam, self._estilo_de("gest_m") or sty)

    def _fonte_small(self):
        fam, sty = FONTS[self.small_font_idx][1]
        return (fam, self._estilo_de("gest_s") or sty)

    def _popular_estilos(self, cid, fam, sel):
        """Enche o ComboBox de estilo (bold/italic/etc) da família escolhida.
        ComboBox.Clear() não tinha precedente no arquivo — por isso o fallback."""
        combo = self.items.get(cid)
        if combo is None:
            return
        ests = FAM_EST.get(fam) or [sel or "Regular"]
        limpou = False
        try:
            combo.Clear()
            limpou = True
        except Exception:
            _tv_diag.falha('Titulos Virais._popular_estilos')
            try:
                while int(combo.Count) > 0:
                    combo.RemoveItem(0)
                limpou = True
            except Exception:
                _tv_diag.falha('Titulos Virais._popular_estilos')
                limpou = False
        if not limpou:
            return          
        for e in ests:
            self._try(lambda e=e: combo.AddItem(e))
        try:
            combo.CurrentIndex = ests.index(sel) if sel in ests else 0
        except Exception:
            _tv_diag.falha('Titulos Virais._popular_estilos')
            pass

    def confirmar_cores(self):
        """Lê ambos os campos antes de gerar, mesmo sem Enter/perda de foco."""
        values = []
        for cid, attr in (("ghex_m", "hero_color_rgb"), ("ghex_s", "small_color_rgb")):
            field = self.items.get(cid)
            if field is None:
                continue
            rgb = self._hex2rgb(str(field.Text))
            if rgb is None:
                self._gstatus("Cor inválida: use #RRGGBB ou #RGB.")
                return False
            values.append((attr, rgb))
        for attr, rgb in values:
            setattr(self, attr, rgb)
        return True

    def on_hex_digitado(self):
        
        
        for cid, attr in (("ghex_m", "hero_color_rgb"), ("ghex_s", "small_color_rgb")):
            rgb = self._hex2rgb(str(self.items[cid].Text))
            if rgb is not None:
                setattr(self, attr, rgb)
        self._try(self._gpreview)

    def on_hex(self, kind):
        cid = "ghex_%s" % kind
        try:
            txt = str(self.items[cid].Text)
        except Exception:
            _tv_diag.falha('Titulos Virais.on_hex')
            return
        rgb = self._hex2rgb(txt)
        if rgb is None:
            self.sync_style()     
            return
        
        if kind == "m":
            self.hero_color_rgb = rgb
        else:
            self.small_color_rgb = rgb
        self.sync_style()

    def on_estilo(self, kind):
        
        self.sync_style()

    def on_fam(self, kind):
        """Família escolhida no dropdown (layout largo). Repopula o estilo e
        atualiza tudo. O guarda de índice evita loop com o sync_style."""
        combo = self.items.get("gfam_%s" % kind)
        if combo is None:
            return
        try:
            i = int(combo.CurrentIndex)
        except Exception:
            _tv_diag.falha('Titulos Virais.on_fam')
            return
        if not (0 <= i < len(FONTS)):
            return
        cur = self.hero_font_idx if kind == "m" else self.small_font_idx
        if i == cur:
            return
        fam, sty = FONTS[i][1]
        if kind == "m":
            self.hero_font_idx = i
        else:
            self.small_font_idx = i
        self._popular_estilos("gest_%s" % kind, fam, sty)
        self.sync_style()

    def sync_style(self):
        """Espelha fonte/cor Principal e Secundária nas duas abas."""
        self._syncing = True
        try:
            for pfx in ("g", "d"):
                for cid, idx in ((pfx + "fmain", self.hero_font_idx),
                                 (pfx + "fsec", self.small_font_idx)):
                    if cid not in self.items:
                        continue
                    try:
                        self.items[cid].Text = FONTS[idx][0]
                    except Exception:
                        _tv_diag.falha('Titulos Virais.sync_style')
                        pass
                
                hm = self.hero_color_rgb is None
                sm = self.small_color_rgb is None
                for i in range(len(COLORS)):
                    try:
                        self.items["%sm_%d" % (pfx, i)].Checked = (hm and i == self.hero_color_idx)
                        self.items["%ss_%d" % (pfx, i)].Checked = (sm and i == self.small_color_idx)
                    except Exception:
                        _tv_diag.falha('Titulos Virais.sync_style')
                        pass
                self._combo_font(pfx + "fmain", *self._fonte_hero())
                self._combo_font(pfx + "fsec", *self._fonte_small())
            
            for cid, idx in (("gfam_m", self.hero_font_idx), ("gfam_s", self.small_font_idx)):
                try:
                    self.items[cid].CurrentIndex = idx
                except Exception:
                    _tv_diag.falha('Titulos Virais.sync_style')
                    pass
            
            for cid, rgb in (("ghex_m", self._cor_hero()), ("ghex_s", self._cor_small())):
                try:
                    self.items[cid].Text = self._rgb2hex(rgb)
                except Exception:
                    _tv_diag.falha('Titulos Virais.sync_style')
                    pass
        finally:
            self._syncing = False
        self.layout.hero_font = self._fonte_hero()
        self.layout.small_font = self._fonte_small()
        self.layout.hero_color = self._cor_hero()
        self.layout.small_color = self._cor_small()
        self._save_prefs()
        self._try(self._gpreview)

    def open_font_picker(self, principal, origem="d"):
        """Abre a lista de fontes DENTRO da própria janela (é mais uma página
        do Stack). Antes era uma janelinha separada — o Bruno não quis, e sem
        moldura o UIManager não entrega: com Popup a lista some ao perder o
        foco e com Dialog+Frameless ela nem vem para a frente.
        A prévia continua real: cada nome é escrito na própria fonte."""
        self._pick_main = principal
        self._pick_origem = origem      
        self._pick_voltar = getattr(self, "tab_atual", 0)
        atual = self.hero_font_idx if principal else self.small_font_idx
        libera = range(len(FONTS)) if principal else FONTS_SEC
        
        
        titulo = "FONTE PRINCIPAL" if principal else "FONTE SECUNDÁRIA"
        self._try(lambda: setattr(self.items["fnt_titulo"], "Text",
                                  SECT_HTML_G % titulo))
        self._try(lambda: setattr(self.items["fnt_combo"], "CurrentIndex", atual))
        self._try(lambda: setattr(self.items["stack"], "CurrentIndex", 3))

    def _voltar_da_fonte(self):
        self._try(lambda: setattr(self.items["stack"], "CurrentIndex",
                                  getattr(self, "_pick_voltar", 0)))

    def _usar_fonte_combo(self):
        try:
            i = int(self.items["fnt_combo"].CurrentIndex)
        except Exception:
            _tv_diag.falha('Titulos Virais._usar_fonte_combo')
            i = 0
        if i < 0 or i >= len(FONTS):
            i = 0
        self.on_pick_font(i)

    def _close_pick(self):
        self._voltar_da_fonte()

    def _anim_salvar(self, entry, st):
        """Grava a receita NO CLIPE: sem isso a animação morre no próximo
        layout (o encaixe reescreve as keys) e ao fechar a janela."""
        try:
            entry["tool"].SetData("Titan.sfx.in", st.get("sfx_in", "auto"))
            entry["tool"].SetData("Titan.sfx.out", st.get("sfx_out", "auto"))
            entry["tool"].SetData(ANIM_KEY, "%s;%s;%s;%s" % (
                ",".join(sorted(st["in"])), st["dir_in"],
                ",".join(sorted(st["out"])), st["dir_out"]))
        except Exception:
            _tv_diag.falha('Titulos Virais._anim_salvar')
            pass

    def _anim_carregar(self, entry, bloco=None, linha=0):
        """Lê a receita gravada no clipe para o estado — SEM renderizar."""
        txt = None
        try:
            txt = entry["tool"].GetData(ANIM_KEY)
        except Exception:
            _tv_diag.falha('Titulos Virais._anim_carregar')
            pass
        st = self.anim.state(entry)
        for side in ("in", "out"):
            try:
                choice = entry["tool"].GetData("Titan.sfx." + side)
                st["sfx_" + side] = choice if choice in _sound_module.CHOICES else "auto"
            except Exception:
                st["sfx_" + side] = "auto"
        if txt:
            try:
                ent, din, sai, dout = str(txt).split(";")
                st["in"] = set(x for x in ent.split(",") if x)
                st["out"] = set(x for x in sai.split(",") if x)
                st["dir_in"], st["dir_out"] = din or "left", dout or "none"
            except Exception:
                _tv_diag.falha('Titulos Virais._anim_carregar')
                txt = None      
        if not txt and bloco is not None and self._quer_anim():
            ef, d = anim_receita(bloco, linha,
                                 getattr(self, "_bloco_linhas", 3))
            st["in"], st["dir_in"] = set(ef), d
            ef2, d2 = ANIM_OUT
            st["out"], st["dir_out"] = set(ef2), d2
            self._anim_salvar(entry, st)
        return st

    def _anim_restaurar(self, entry, bloco=None, linha=0):
        """Reaplica a animação depois de um layout (o encaixe apaga as keys)."""
        st = self._anim_carregar(entry, bloco, linha)
        if not self.anim.has_anim(st):
            return False
        
        
        
        
        if st.get("base_center") is None or st.get("base_size") is None:
            self.anim.state(entry)
        self._try(lambda: self.anim.render(entry))
        return True

    def _quer_anim(self):
        try:
            return bool(self.items["ganim_in"].Checked or
                        self.items["ganim_out"].Checked)
        except Exception:
            _tv_diag.falha('Titulos Virais._quer_anim')
            return False

    def _reaplicar(self):
        """Reaplica o design às linhas sob o playhead. Sem layout escolhido
        nesta sessão, usa o mesmo padrão do gerador (badge / centro)."""
        self.refresh()
        if not self.entries:
            self.items["status"].Text = "Sem linhas sob o playhead"
            return
        lay = getattr(self, "current_layout", None)
        if not lay:
            lay = "badge" if len(self.entries) >= 2 else "center"
        self.on_layout(lay)

    def on_pick_font(self, i):
        fam, sty = FONTS[i][1]
        if getattr(self, "_pick_main", True):
            self.hero_font_idx = i
            self.hero_style = None            
            self._popular_estilos("gest_m", fam, sty)
        else:
            self.small_font_idx = i
            self.small_style = None
            self._popular_estilos("gest_s", fam, sty)
        self._voltar_da_fonte()
        self.sync_style()
        
        
        if getattr(self, "_pick_origem", "d") != "g":
            self._reaplicar()

    def on_font(self, cid, principal):
        self.refresh()   
        try:
            i = int(self.items[cid].CurrentIndex)
        except Exception:
            _tv_diag.falha('Titulos Virais.on_font')
            return
        if not (0 <= i < len(FONTS)):
            return
        if principal:
            self.hero_font_idx = i
        else:
            self.small_font_idx = i
        self.sync_style()
        if getattr(self, "current_layout", None) and self.entries:
            self.on_layout(self.current_layout)

    def on_style_color(self, i, principal, origem="d"):
        self.refresh()   
        if principal:
            self.hero_color_idx = i
            self.hero_color_rgb = None     
        else:
            self.small_color_idx = i
            self.small_color_rgb = None
        self.sync_style()
        if origem != "g":
            self._reaplicar()

    def on_hfont(self, i):
        """compat: escolha de fonte principal por índice."""
        self.hero_font_idx = i
        self.sync_style()

    def on_hcolor(self, i):
        """compat: cor principal por índice."""
        self.hero_color_idx = i
        self.sync_style()

    def _try(self, fn):
        try:
            fn()
        except Exception as ex:
            _tv_diag.falha('Titulos Virais._try')
            log(ex)

    def _mk(self, fn, *args):
        def handler(ev):
            if self._syncing:
                return
            if getattr(self, "_busy", False):
                
                
                log("ocupado — clique ignorado")
                return
            try:
                fn(*args)
            except Exception as ex:
                _tv_diag.falha('Titulos Virais._mk.handler')
                import traceback
                traceback.print_exc()
                self.items["status"].Text = "Erro: %s" % ex
        return handler

    def _salvar_geo(self):
        try:
            g = self.win.GetGeometry()
            v = [g[k] for k in sorted(g.keys())] if hasattr(g, "keys") else list(g)
            if len(v) == 4:
                fusion.SetData("TitulosVirais.winGeo",
                               ",".join(str(int(float(x))) for x in v))
        except Exception:
            _tv_diag.falha('Titulos Virais._salvar_geo')
            pass

    def on_close(self, ev):
        # Resolve dispatches Close while its host-owned window is still alive.
        # The run() cleanup calls Close again after ExitLoop, so make the
        # callback idempotent to avoid re-entering the embedded Qt event loop.
        if getattr(self, "_closing", False) or getattr(self, "_close_handled", False):
            return
        if not getattr(self, "_closable", False):
            log("Close ignorado (janela recém-aberta).")
            return
        self._close_handled = True
        self._salvar_geo()
        self._exit = True
        disp.ExitLoop()

    
    def refresh(self, force=False):
        if getattr(self, "_busy", False) or getattr(self, "_refreshing", False):
            return
        self._refreshing = True
        try:
            self._refresh_current(force)
        finally:
            self._refreshing = False

    def _refresh_current(self, force=False):
        self._poll_update()
        proj, tl = get_timeline()
        if not tl:
            self.entries = []
            self._refresh_identity = None
            self.tree.Clear()
            self.items["status"].Text = "Sem timeline"
            return
        try:
            tc = tl.GetCurrentTimecode()
        except Exception:
            _tv_diag.falha('Titulos Virais._refresh_current')
            tc = None
        
        
        entries = find_textplus_under_playhead(tl)
        identity = (proj.GetUniqueId(), tl.GetUniqueId(), tc,
                    tuple((e["uid"], e["start"], e["end"], e["text"]) for e in entries))
        self.entries = entries
        if not force and identity == getattr(self, "_refresh_identity", None):
            return
        self._refresh_identity = identity
        self.last_tc = tc
        self.aspect = timeline_aspect(tl)
        for entry in self.entries:
            if entry["uid"] not in self.anim.states:
                self._anim_carregar(entry)
        self.current_layout = getattr(self, "current_layout", None)
        self._sync_pos_from_entries()
        self.tree.Clear()
        for i, e in enumerate(self.entries):
            it = self.tree.NewItem()
            it.Text[0] = str(i + 1)
            it.Text[1] = "V%d" % e["track"]
            it.Text[2] = e["text"] or "(vazio)"
            self.tree.AddTopLevelItem(it)
        _tc = (tc or "")[3:] if len(tc or "") > 8 else (tc or "")
        self.items["status"].Text = "%d linhas · %s" % (len(self.entries), _tc)
        self.sync_buttons()
        self._try(self.update_preview)

    def _preview_frame(self, canvas):
        _, timeline = get_timeline()
        aspect = timeline_aspect(timeline) if timeline else 16.0 / 9.0
        aspect = max(0.1, aspect)
        maxw = float(self.gprev_w if canvas == "gpreview" else self.prev_w)
        maxh = float(self.gprev_h if canvas == "gpreview" else self.prev_h)
        width = min(maxw, maxh / aspect)
        height = width * aspect
        dimensions = [int(round(width)), int(round(height))]
        self.items[canvas].MinimumSize = dimensions
        self.items[canvas].MaximumSize = dimensions
        return width, height

    def _preview_label(self, canvas, index):
        cache = getattr(self, "_preview_labels", {})
        key = (canvas, index)
        if key not in cache:
            parent = self.items[canvas]
            ident = "pv_%s_%s" % (canvas, index)
            parent.AddChild(ui.Label({"ID": ident, "Text": "", "TextFormat": "PlainText", "WordWrap": False,
                                     "Alignment": {"AlignHCenter": True, "AlignVCenter": True},
                                     "StyleSheet": "background:transparent;border:0;padding:0;margin:0;"}))
            cache[key] = self.win.GetItems()[ident]
            self._preview_labels = cache
        return cache[key]

    def _preview_font(self, label, family, style, pixels, color="white"):
        family = str(family).replace('"', '').replace("'", "")
        italic = "italic" if any(x in style.lower() for x in ("italic", "oblique")) else "normal"
        weight = "900" if any(x in style.lower() for x in ("black", "heavy")) else "700" if "bold" in style.lower() else "400"
        label.StyleSheet = ("background:transparent;border:0;padding:0;margin:0;color:%s;"
                            "font-family:'%s';font-size:%dpx;font-style:%s;font-weight:%s;"
                            % (color, family, max(1, int(round(pixels))), italic, weight))

    def _preview_metric(self, canvas, text, family, style, pixels, tracking=1.0):
        label = self._preview_label(canvas, "measure")
        self._preview_font(label, family, style, pixels)
        label.Text = text
        label.AdjustSize()
        geo = label.GetGeometry()
        vals = [geo[k] for k in sorted(geo)] if isinstance(geo, dict) else list(geo)
        label.Hide()
        return max(1.0, float(vals[2]) * tracking), max(1.0, float(vals[3]))

    def _draw_preview(self, canvas, rows, width, height):
        
        parent = self.items[canvas]
        parent.Text = ""
        for (name, _), label in getattr(self, "_preview_labels", {}).items():
            if name == canvas:
                label.Hide()
        for i, row in enumerate(rows):
            text, family, style = row["text"], row["font"][0], row["font"][1]
            
            
            pixels = row["size"] * width * 0.7
            color = "rgb(%d,%d,%d)" % tuple(int(round(x * 255)) for x in row["color"])
            tracking = float(row.get("tracking", 1.0))
            natural, line_height = self._preview_metric(canvas, text, family, style, pixels)
            delta = (tracking - 1.0) * natural / max(1, len(text) - 1)
            glyphs = list(text) if abs(tracking - 1.0) > 0.0001 and len(text) > 1 else [text]
            full = natural * tracking if len(glyphs) > 1 else natural
            left = row["x"] * width - full / 2.0
            prefix = ""
            for j, glyph in enumerate(glyphs):
                label = self._preview_label(canvas, "%d_%d" % (i, j))
                self._preview_font(label, family, style, pixels, color)
                label.Text = glyph
                label.AdjustSize()
                geo = label.GetGeometry()
                vals = [geo[k] for k in sorted(geo)] if isinstance(geo, dict) else list(geo)
                w, h = max(1, vals[2]), max(1, vals[3])
                advance = self._preview_metric(canvas, prefix + glyph, family, style, pixels)[0]
                x = left + (advance - w + j * delta if len(glyphs) > 1 else 0)
                label.Geometry = [int(round(x)), int(round((1.0 - row["y"]) * height - h / 2)), int(w), int(h)]
                label.Show()
                prefix += glyph
        self._preview_rows = getattr(self, "_preview_rows", {})
        self._preview_rows[canvas] = rows

    def update_preview(self):
        if not getattr(self, "_preview_ready", False) or self.items.get("preview") is None:
            return
        rows = []
        for entry in self.entries:
            tool = entry["tool"]
            lo, hi = visible_range(entry)
            frame = (lo + hi) // 2
            _, timeline = get_timeline()
            playhead = playhead_frame(timeline) if timeline else None
            if playhead is not None:
                frame = max(lo, min(hi, lo + playhead - int(entry["item"].GetStart())))
            size = float(get_at(tool, "Size", frame) or 0.08)
            cx, cy = to_xy(get_at(tool, "Center", frame))
            
            
            try:
                family, style, offsets = str(tool.GetData("TV_preview_anchor")).split("\n")
                if family == str(tool.GetInput("Font")) and style == str(tool.GetInput("Style")):
                    ox, oy = (float(v) for v in offsets.split(","))
                    cx += ox * size
                    cy += oy * size
            except (AttributeError, TypeError, ValueError):
                _tv_diag.falha('Titulos Virais.update_preview')
                pass
            move = get_move_tool(entry["comp"], tool)
            mx, my = 0.5, 0.5
            if move:
                mx, my = to_xy(get_at(move, "Center", frame))
                cx += mx - 0.5
                cy += my - 0.5
            def channel(name):
                value = tool.GetInput(name)
                return float(value) if value is not None else 1.0
            rows.append({"text": entry["text"], "font": (str(tool.GetInput("Font") or "Arial"),
                         str(tool.GetInput("Style") or "Regular")), "size": size,
                         "x": cx, "y": cy, "color": tuple(channel(c) for c in ("Red1", "Green1", "Blue1")),
                         "tracking": float(tool.GetInput("CharacterSpacing") or 1.0)})
        self._draw_preview("preview", rows, *self._preview_frame("preview"))

    def selected(self):
        """Entradas selecionadas na lista; nenhuma selecionada = todas."""
        sel = []
        try:
            si = self.tree.SelectedItems()
            for k in si:
                it = si[k]
                idx = int(it.Text[0]) - 1
                if 0 <= idx < len(self.entries):
                    sel.append(self.entries[idx])
        except Exception as ex:
            _tv_diag.falha('Titulos Virais.selected')
            log("SelectedItems", ex)
        if not sel:
            sel = list(self.entries)
        return sel

    def sync_buttons(self):
        """Reflete o estado do primeiro clipe selecionado nos botões."""
        sel = self.selected()
        if not sel:
            return
        self._sync_pos_from_entries(sel)
        st = self.anim.state(sel[0])
        I = self.items
        self._syncing = True
        try:
            for side in ("in", "out"):
                choice = st.get("sfx_" + side, "auto")
                I[side + "_sound"].CurrentIndex = _sound_module.CHOICES.index(choice) if choice in _sound_module.CHOICES else 0
                for a in ("slide", "bounce", "flicker", "shake", "blur"):
                    I[side + "_" + a].Checked = a in st[side]
                for d in ("left", "right", "up", "down", "none"):
                    I[side + "_" + d].Checked = (st["dir_" + side] == d)
            for cb in ("mblur",):
                I[cb].Checked = bool(st[cb])
            
            
        finally:
            self._syncing = False

    
    TRACK_MIN, TRACK_MAX, TRACK_DEF = 0.5, 1.5, 0.96

    def tracking(self, sid="gtrackH"):
        """Tracking (0,5 a 1,5) lido do slider (herói por padrão, apoio se
        sid='gtrackA'). O slider guarda 50–150 = 0,50–1,50."""
        try:
            v = float(self.items[sid].Value) / 100.0
        except Exception:
            _tv_diag.falha('Titulos Virais.tracking')
            v = self.TRACK_DEF
        return max(self.TRACK_MIN, min(self.TRACK_MAX, v))

    def _reaplicar_se_tiver(self):
        if getattr(self, "current_layout", None) and self.entries:
            self.on_layout(self.current_layout)

    def on_baixar_update(self):
        url = getattr(self, "_update_link", None)
        if not url:
            return
        updater = getattr(self, "_updater", None)
        if updater is None:
            updater = self._updater = Atualizador(INSTALL_ROOT)
        if updater.arquivo:
            try:
                updater.instalar()
                self.items["up_txt"].Text = "Atualizado! Reabra o Titan Titles Studio."
                self.items["up_btn"].Text = "Concluído"
                self.items["up_btn"].Enabled = False
                if getattr(self, "about_window", None):
                    about = self.about_window.GetItems()
                    about["about_update_status"].Text = "Atualizado. Feche e reabra o Titan Titles Studio."
                    about["about_update_btn"].Text = "Concluído"
                    about["about_update_btn"].Enabled = False
                self._exit = True
                disp.ExitLoop()
            except Exception as erro:
                _tv_diag.falha('Titulos Virais.on_baixar_update')
                self.items["up_txt"].Text = str(erro)
                if getattr(self, "about_window", None):
                    about = self.about_window.GetItems()
                    about["about_update_status"].Text = str(erro)
                    about["about_update_btn"].Text = "Tentar novamente"
                    about["about_update_btn"].Enabled = True
        elif updater.iniciar(url):
            self.items["up_btn"].Enabled = False
            self.items["up_txt"].Text = "Baixando atualização…"
            if getattr(self, "about_window", None):
                about = self.about_window.GetItems()
                about["about_update_btn"].Enabled = False
                about["about_update_status"].Text = "Baixando atualização…"
        else:
            if getattr(self, "about_window", None):
                about = self.about_window.GetItems()
                about["about_update_status"].Text = "Não foi possível iniciar o download. Tente novamente."
                about["about_update_btn"].Text = "Tentar novamente"
                about["about_update_btn"].Enabled = True

    def _poll_update(self):
        self._mostrar_update_resultado()
        import queue
        updater = getattr(self, "_updater", None)
        if updater is None:
            return
        try:
            while True:
                evento = updater.eventos.get_nowait()
                if evento[0] == "progresso":
                    n, total = evento[1:]
                    self.items["up_txt"].Text = ("Baixando atualização… %d%%" % (n * 100 / total)
                                                if total else "Baixando atualização… %.1f MB" % (n / 1048576.0))
                elif evento[0] == "pronto":
                    self.items["up_txt"].Text = "Pronto para instalar. Backup automático."
                    self.items["up_btn"].Text = "Instalar"
                    self.items["up_btn"].Enabled = True
                    if getattr(self, "about_window", None):
                        about = self.about_window.GetItems()
                        about["about_update_status"].Text = "Download concluído. Clique em Instalar."
                        about["about_update_btn"].Text = "Instalar"
                        about["about_update_btn"].Enabled = True
                elif evento[0] == "erro":
                    self.items["up_txt"].Text = evento[1]
                    self.items["up_btn"].Enabled = True
                    if getattr(self, "about_window", None):
                        about = self.about_window.GetItems()
                        about["about_update_status"].Text = evento[1]
                        about["about_update_btn"].Text = "Tentar novamente"
                        about["about_update_btn"].Enabled = True
        except queue.Empty:
            _tv_diag.falha('Titulos Virais._poll_update')
            pass

    def on_about_update(self):
        updater = getattr(self, "_updater", None)
        if self._update_link or (updater and updater.arquivo):
            self.on_baixar_update()
            return
        about = self.about_window.GetItems() if getattr(self, "about_window", None) else None
        if about:
            about["about_update_btn"].Enabled = False
            about["about_update_status"].Text = "Buscando atualizações…"
        self.mostrar_update(force=True, manual=True)

    def mostrar_update(self, force=False, manual=False):
        """Check in a worker; manual checks report current, newer, or offline."""
        import queue
        import threading
        if getattr(self, "_update_check_started", False) and not force:
            return
        self._update_check_started = True
        results = queue.Queue()
        self._update_results = results
        def worker():
            results.put(("manual", checar_atualizacao(detailed=True)) if manual
                        else checar_atualizacao())
        threading.Thread(target=worker, daemon=True).start()

    def _mostrar_update_resultado(self):
        import queue
        results = getattr(self, "_update_results", None)
        if results is None:
            return
        try:
            info = results.get_nowait()
        except queue.Empty:
            return
        manual = isinstance(info, tuple) and len(info) == 2 and info[0] == "manual"
        status = payload = None
        if manual:
            status, payload = info[1]
            about = self.about_window.GetItems() if getattr(self, "about_window", None) else None
            if status == "current":
                if about:
                    about["about_update_status"].Text = "Seu Titan Titles Studio já está atualizado."
                    about["about_update_btn"].Text = "Buscar novamente"
                    about["about_update_btn"].Enabled = True
                return
            if status != "available":
                if about:
                    about["about_update_status"].Text = ("A versão existe, mas o pacote de atualização não está disponível."
                        if status == "unavailable" else "Não foi possível consultar o GitHub. Verifique a internet e tente novamente.")
                    about["about_update_btn"].Text = "Tentar novamente"
                    about["about_update_btn"].Enabled = True
                return
            info = payload
        if not info:
            return
        versao, link, notas = info
        self._update_link = link
        self.items["up_txt"].Text = "%s disponível · GitHub" % versao
        self.items["up_btn"].Text = "Baixar"
        self.items["up_btn"].Enabled = True
        self.items["cx_update"].Hidden = False
        if getattr(self, "about_window", None):
            about = self.about_window.GetItems()
            about["about_update_status"].Text = "%s disponível. Clique em Baixar atualização." % versao
            about["about_update_btn"].Text = "Baixar atualização"
            about["about_update_btn"].Enabled = True
        self._relayout()

    def _relayout(self):
        """O UIManager só refaz as contas quando a janela muda de tamanho —
        mostrar/esconder um grupo sozinho deixa ele flutuando sobre o resto
        (mesma pegadinha da tela de login)."""
        try:
            g = self.win.Geometry
            g = [g[1], g[2], g[3], g[4]] if isinstance(g, dict) else g
            g = [int(v) for v in g]
            self.win.Geometry = [g[0], g[1], g[2], g[3] + 1]
            for _ in range(3):
                disp.StepLoop()
            self.win.Geometry = g
        except Exception as ex:
            _tv_diag.falha('Titulos Virais._relayout')
            log("relayout:", ex)

    def on_gen_auto(self):
        """No automático o plugin sorteia um layout por bloco (menos o Centro)
        e ninguém precisa escolher nada."""
        self.gen_auto = not self.gen_auto
        self.sync_gen_layouts()
        self._save_prefs()

    def on_gen_layout(self, key):
        if key not in dict(LAYOUTS):
            return
        if self.gen_auto:          
            self.gen_auto = False
            self.gen_layouts = []
        """Escolhe de 1 a 3 layouts para o gerador revezar (um por bloco).
        Clicar num quarto tira o mais antigo; nunca fica sem nenhum."""
        sel = list(self.gen_layouts)
        if key in sel:
            if len(sel) > 1:            
                sel.remove(key)
        else:
            sel.append(key)
            if len(sel) > GEN_LAY_MAX:
                sel.pop(0)
        self.gen_layouts = sel
        self.gen_preview_layout = key if key in sel else sel[-1]
        self.sync_gen_layouts()
        self._save_prefs()

    def sync_gen_layouts(self):
        nomes = dict(LAYOUTS)
        self._try(lambda: setattr(self.items["glay_auto"], "Checked", self.gen_auto))
        for k, _ in LAYOUTS:
            self._try(lambda k=k: setattr(self.items["glay_" + k], "Checked",
                                          (not self.gen_auto) and k in self.gen_layouts))
        self._try(self._gpreview)   
        if self.gen_auto:
            self._try(lambda: setattr(self.items["glay_info"], "Text",
                                      "automático · sorteia por bloco"))
            return
        
        n = len(self.gen_layouts)
        if n == 1:
            txt = nomes.get(self.gen_layouts[0], "")
        else:
            txt = "%d layouts · alterna por bloco" % n
        self._try(lambda: setattr(self.items["glay_info"], "Text", txt))

    def on_layout(self, key):
        self.refresh()   
        
        
        for e in self.entries:
            try:
                pan = float(e["item"].GetProperty("Pan") or 0)
                tilt = float(e["item"].GetProperty("Tilt") or 0)
                if abs(pan) > 0.01 or abs(tilt) > 0.01:
                    log("AVISO: clipe V%d tem Position no Inspector (%.0f, %.0f) — "
                        "zere para o layout alinhar" % (e["track"], pan, tilt))
            except Exception:
                _tv_diag.falha('Titulos Virais.on_layout')
                pass
        self.current_layout = key
        self.layout.gap = 1.0                  
        self.layout.scale = 1.0                
        self.layout.width = self.items["width"].Value / 100.0
        self.layout.cx = self.layout.cy = 0.5   
        try:
            self.layout.hero_color = self._cor_hero()
            self.layout.small_color = self._cor_small()
            self.layout.small_font = self._fonte_small()
            self.layout.tracking_hero = self.tracking("gtrackH")
            self.layout.tracking_small = self.tracking("gtrackA")
            self.layout.tracking = self.layout.tracking_hero
        except Exception:
            _tv_diag.falha('Titulos Virais.on_layout')
            pass
        
        hero_idx = None
        try:
            si = self.tree.SelectedItems()
            idxs = [int(si[k].Text[0]) - 1 for k in si]
            if len(idxs) == 1 and 0 <= idxs[0] < len(self.entries):
                hero_idx = idxs[0]
        except Exception:
            _tv_diag.falha('Titulos Virais.on_layout')
            pass
        moves = []
        for entry in self.entries:
            mv = get_move_tool(entry["comp"], entry["tool"])
            moves.append(to_xy(mv.GetInput("Center")) if mv else (0.5, 0.5))
        
        
        
        recipes = []
        try:
            for entry in self.entries:
                state = self.anim.state(entry)
                recipes.append((state, state["in"], state["out"]))
                state["in"], state["out"] = set(), set()
                comp, tool = entry["comp"], entry["tool"]
                comp.Lock()
                try:
                    remove_modifier(tool, "Center")
                    set_point(tool, "Center", *state["base_center"])
                    remove_modifier(tool, "Size")
                    set_val(tool, "Size", state["base_size"])
                finally:
                    comp.Unlock()
            self.layout.apply(self.entries, key, self.aspect, hero_idx)
        finally:
            for state, entrance, exit_effects in recipes:
                state["in"], state["out"] = entrance, exit_effects
            for entry in self.entries:
                self._anim_restaurar(entry)
        for e, move in zip(self.entries, moves):  
            set_move(e, move[0] - 0.5, move[1] - 0.5)
        self.items["status"].Text = "Layout: " + tr(dict(LAYOUTS)[key])
        self._sync_sounds(self.entries)
        self._try(self.update_preview)

    def sync_slider_labels(self):
        """Números ao lado dos sliders (Tamanho/Espaço em % do padrão)."""
        I = self.items
        for sid, lid, fmt, base in (("width", "width_lbl", "%d%%", None),
                                    ("dur", "dur_lbl", "%df", None),
                                    ("dist", "dist_lbl", "%d", None)):
            try:
                v = float(I[sid].Value)
                if base:
                    v = v / base * 100.0
                I[lid].Text = fmt % int(round(v))
            except Exception:
                _tv_diag.falha('Titulos Virais.sync_slider_labels')
                pass

    def on_layout_param(self):
        self.sync_slider_labels()
        
        self._reaplicar()

    def _numero_confirmar(self, sid, factor, callback):
        slider = self.items[sid]
        try:
            texto = self.items[sid + "_lbl"].Text.strip().rstrip("%f").replace(",", ".")
            valor = int(round(float(texto) * factor))
            slider.Value = max(slider.Minimum, min(slider.Maximum, valor))
        except (ValueError, OverflowError):
            _tv_diag.falha('Titulos Virais._numero_confirmar')
            pass
        callback()

    def _ima_posicao(self, sid):
        slider = self.items[sid]
        if slider.SliderDown and abs(float(slider.Value) - 50) <= 2 and slider.Value != 50:
            slider.Value = 50

    def _gsliders(self):
        self._ima_posicao("galt")
        self._ima_posicao("ghor")
        
        for sid, lid, suf in (("galt", "galt_lbl", ""), ("ghor", "ghor_lbl", ""),
                              ("gwidth", "gwidth_lbl", "%")):
            try:
                self.items[lid].Text = str(int(self.items[sid].Value)) + suf
            except Exception:
                _tv_diag.falha('Titulos Virais._gsliders')
                pass
        
        for sid, lid in (("gtrackH", "gtrackH_lbl"), ("gtrackA", "gtrackA_lbl")):
            try:
                self.items[lid].Text = "%.2f" % (float(self.items[sid].Value) / 100.0)
            except Exception:
                _tv_diag.falha('Titulos Virais._gsliders')
                pass
        self._gsliders_ultimo = tuple(int(self.items[sid].Value) for sid in ("galt", "ghor", "gwidth", "gtrackH", "gtrackA"))
        self._try(self._gpreview)

    def _gpreview(self):
        if not getattr(self, "_preview_ready", False) or self.items.get("gpreview") is None:
            return
        app = self
        width, height = self._preview_frame("gpreview")
        
        class PreviewLayout(Layouter):
            def _set_font(self, entry, font=None, trk=None):
                entry["font"] = font or entry.get("font", ("Arial", "Regular"))
                entry["tracking"] = trk if trk is not None else self.tracking
            def _set_color(self, entry, rgb):
                entry["color"] = rgb
            def _set_shadow(self, entry):
                pass
            def _measure_at_size(self, entry, size, aspect):
                family, style = entry["font"]
                w, h = app._preview_metric("gpreview", entry["text"], family, style, 100, entry["tracking"])
                return w * size * 0.7 / 100.0, h * size * 0.7 / (100.0 * aspect)
            def _fit_real(self, entry, target, aspect):
                w, h = self._measure_at_size(entry, 1.0, aspect)
                size = max(self.size_min, min(self.size_max, target / w))
                return size, w * size, h * size
            def _place_dbg(self, entry, x, y, size):
                entry.update(x=x, y=y, size=size)
        lays = getattr(self, "gen_layouts", None) or GEN_LAY_DEF
        chosen = "badge" if getattr(self, "gen_auto", False) else getattr(self, "gen_preview_layout", lays[-1])
        if chosen not in dict(LAYOUTS):
            chosen = lays[-1]
        hero = "PRINCIPAL" if self.items["gcapsH"].Checked else "principal"
        support = "APOIO" if self.items["gcapsA"].Checked else "apoio"
        pos = HERO_POS.get(chosen)
        texts = ([support, support, hero] if chosen == "duo_up" else
                 [hero, support, support] if chosen == "duo_dn" else
                 [support, hero] if pos == "fim" else [hero, support] if pos == "ini" else
                 [support, hero, support])
        rows = [{"text": text, "font": self._fonte_small(), "color": self._cor_small()} for text in texts]
        lay = PreviewLayout(None)
        lay.width = self.items["gwidth"].Value / 100.0
        lay.cx = self.items["ghor"].Value / 100.0
        lay.cy = self.items["galt"].Value / 100.0
        lay.hero_font, lay.small_font = self._fonte_hero(), self._fonte_small()
        lay.hero_color, lay.small_color = self._cor_hero(), self._cor_small()
        lay.tracking_hero, lay.tracking_small = self.tracking("gtrackH"), self.tracking("gtrackA")
        lay.apply(rows, chosen, height / width)
        self._draw_preview("gpreview", rows, width, height)

    def on_pos_center(self):
        self._syncing = True
        try:
            self.items["posx"].Value = 50
            self.items["posy"].Value = 50
        finally:
            self._syncing = False
        self.on_pos()

    def _poll_gsliders(self):
        """Posição do puxador durante o arrasto, mesmo antes de ValueChanged."""
        ids = ("galt", "ghor", "gwidth", "gtrackH", "gtrackA")
        valores = tuple(int(self.items[sid].SliderPosition if self.items[sid].SliderDown
                            else self.items[sid].Value) for sid in ids)
        if valores == getattr(self, "_gsliders_ultimo", None):
            return
        self._syncing = True
        try:
            for sid, valor in zip(ids, valores):
                if self.items[sid].Value != valor:
                    self.items[sid].Value = valor
        finally:
            self._syncing = False
        self._gsliders()

    def _poll_edit_sliders(self):
        ids = ("width", "dur", "dist")
        values = tuple(int(self.items[sid].SliderPosition if self.items[sid].SliderDown
                           else self.items[sid].Value) for sid in ids)
        previous = getattr(self, "_edit_sliders_ultimo", None)
        self._edit_sliders_ultimo = values
        if previous is None or values == previous:
            return
        self._syncing = True
        try:
            for sid, value in zip(ids, values):
                self.items[sid].Value = value
        finally:
            self._syncing = False
        if values[0] != previous[0]:
            self.on_layout_param()
        if values[1:] != previous[1:]:
            self.on_timing()

    def _sync_pos_from_entries(self, entries=None):
        entries = self.entries if entries is None else entries
        if not entries:
            return
        e = entries[0]
        move = get_move_tool(e["comp"], e["tool"])
        cx, cy = to_xy(move.GetInput("Center")) if move else (0.5, 0.5)
        self._syncing = True
        try:
            self.items["posx"].Value = int(round(cx * 100))
            self.items["posy"].Value = int(round(cy * 100))
            self.items["posx_lbl"].Text = "%.2f" % cx
            self.items["posy_lbl"].Text = "%.2f" % cy
            self._pos_ultimo = (int(round(cx * 100)), int(round(cy * 100)))
            self.pos_dx, self.pos_dy = cx - 0.5, cy - 0.5
        finally:
            self._syncing = False

    def _poll_pos(self):
        """Lê os sliders de posição a cada volta do laço (~20x/s)."""
        try:
            v = (int(self.items["posx"].Value), int(self.items["posy"].Value))
        except Exception:
            _tv_diag.falha('Titulos Virais._poll_pos')
            return
        if getattr(self, "_pos_ultimo", None) is None:
            self._pos_ultimo = v
            return
        if v != self._pos_ultimo:
            self._pos_ultimo = v
            self.on_pos()

    def on_pos(self):
        """Move o bloco pelo Transform LD_Move: UMA chamada por linha, sem
        reescrever keyframe nenhum. Reescrever as keys custava ~1s por linha
        (cada key leva ~8ms) — era isso que impedia o arrasto fluido."""
        if getattr(self, "_syncing", False):
            return
        # Atualiza o alvo sem sobrescrever a posição que o usuário acaba de escolher.
        _, timeline = get_timeline()
        changed_target = bool(timeline and timeline.GetCurrentTimecode() != self.last_tc)
        if changed_target:
            self.entries = find_textplus_under_playhead(timeline)
            self.last_tc = timeline.GetCurrentTimecode()
        self._ima_posicao("posx")
        self._ima_posicao("posy")
        try:
            cx = float(self.items["posx"].Value) / 100.0
            cy = float(self.items["posy"].Value) / 100.0
        except Exception:
            _tv_diag.falha('Titulos Virais.on_pos')
            return
        try:
            self.items["posx_lbl"].Text = "%.2f" % cx
            self.items["posy_lbl"].Text = "%.2f" % cy
        except Exception:
            _tv_diag.falha('Titulos Virais.on_pos')
            pass
        self.pos_dx, self.pos_dy = cx - 0.5, cy - 0.5
        self._pos_ultimo = (int(round(cx * 100)), int(round(cy * 100)))
        targets = self.entries if changed_target else self.selected()
        for e in targets:
            set_move(e, self.pos_dx, self.pos_dy)
        self._try(self.update_preview)

    def on_color(self, i):
        self.refresh()   
        r, g, b = COLORS[i][1]
        for e in self.selected():
            tool, comp = e["tool"], e["comp"]
            comp.Lock()
            try:
                set_val(tool, "Red1", r)
                set_val(tool, "Green1", g)
                set_val(tool, "Blue1", b)
            finally:
                comp.Unlock()
        self._try(self.update_preview)

    def on_anim(self, side, a):
        on = self.items[side + "_" + a].Checked
        self.refresh()
        sel = self.selected()
        for e in sel:
            st = self.anim.state(e)
            if on:
                st[side].add(a)
                mapped=self._mapped_sound_for_state(st,side)
                if mapped is not None:st["sfx_"+side]=mapped
            else:
                st[side].discard(a)
            self._anim_salvar(e, st)
            self._try(lambda e=e: self.anim.render(e))
        self._sync_sounds(sel)

    def on_dir(self, side, d):
        self.refresh()   
        for e in self.selected():
            st = self.anim.state(e)
            st["dir_" + side] = d
            self._anim_salvar(e, st)
            if "slide" in st[side]:
                self._try(lambda e=e: self.anim.render(e))
        for dd in ("left", "right", "up", "down", "none"):
            self.items[side + "_" + dd].Checked = (dd == d)
        self._sync_sounds(self.selected())

    def on_flag(self, flag):
        self.refresh()   
        on = self.items[flag].Checked
        selected=self.selected()
        for e in selected:
            st = self.anim.state(e)
            st[flag] = bool(on)
            if flag=="mblur" and on:
                for side in ("in","out"):
                    mapped=self._mapped_sound_for_state(st,side)
                    if mapped is not None:st["sfx_"+side]=mapped
            self._anim_salvar(e,st)
            self.anim.render(e)
        if flag=="mblur":self._sync_sounds(selected)

    def on_timing(self):
        self.sync_slider_labels()
        self.refresh()   
        self.anim.dur = int(self.items["dur"].Value)
        self.anim.dist = self.items["dist"].Value / 100.0
        for e in self.selected():
            if self.anim.has_anim(self.anim.state(e)):
                self._try(lambda e=e: self.anim.render(e))
        self._try(self.update_preview)
        self._sync_sounds(self.selected())

    def on_reset(self):
        self.refresh()   
        for e in self.selected():
            self.anim.reset(e)
            self._anim_salvar(e, self.anim.state(e))
        self.sync_buttons()
        self._sync_sounds(self.selected())

    def on_debug(self):
        sel = self.selected()
        if not sel:
            log("Nenhum Text+ sob o playhead.")
            return
        tool = sel[0]["tool"]
        log("Inputs do Text+ '%s':" % sel[0]["text"])
        try:
            lst = tool.GetInputList()
            names = sorted(str(k) for k in lst)
            for n in names:
                print("   ", n)
        except Exception as ex:
            _tv_diag.falha('Titulos Virais.on_debug')
            log("GetInputList falhou:", ex)
        log("Center =", tool.GetInput("Center"), " Size =", tool.GetInput("Size"))

    
    
    def _progresso(self, frac, texto=None, largura=780):
        """Barra + texto. Bombeia o laço de eventos: sem isso a janela não
        repinta durante o trabalho e o usuário acha que travou."""
        try:
            f = max(0.0, min(1.0, float(frac)))
            
            
            w = max(1, int(largura * f))
            self.items["gbar"].Text = (
                "<table cellspacing='0' cellpadding='0' border='0'><tr>"
                "<td width='%d' bgcolor='%s'>&nbsp;</td>"
                "<td width='%d'>&nbsp;</td></tr></table>"
                % (w, ACCENT, max(1, largura - w)))
        except Exception:
            _tv_diag.falha('Titulos Virais._progresso')
            pass
        if texto is not None:
            try:
                self.items["gstatus"].Text = texto
            except Exception:
                _tv_diag.falha('Titulos Virais._progresso')
                pass

    def _passo_ui(self):
        """Deixa a janela respirar no meio de uma tarefa longa (download)."""
        for _ in range(2):
            try:
                disp.StepLoop()
            except Exception:
                _tv_diag.falha('Titulos Virais._passo_ui')
                break

    def _cta_ocupado(self, txt="APLICANDO…  NÃO MEXA NA TIMELINE"):
        try:
            self.items["generate"].Text = txt
            self.items["generate"].StyleSheet = CTA_BUSY_CSS
        except Exception:
            _tv_diag.falha('Titulos Virais._cta_ocupado')
            pass

    def _cta_normal(self):
        try:
            self.items["generate"].Text = "GERAR LEGENDAS"
            self.items["generate"].StyleSheet = CTA_CSS
        except Exception:
            _tv_diag.falha('Titulos Virais._cta_normal')
            pass

    def _gstatus(self, txt):
        try:
            self.items["gstatus"].Text = txt
        except Exception:
            _tv_diag.falha('Titulos Virais._gstatus')
            pass
        log(txt)

    def on_generate(self):
        if getattr(self, "_busy", False):
            return
        if not garantir_acesso():
            self._gstatus(texto_acesso("Corrija o acesso para gerar. Seu projeto não foi alterado.", "Corrige el acceso para generar. Tu proyecto no se ha modificado."))
            return
        try:
            return self._on_generate_impl()
        except OSError as erro:
            import errno
            if erro.errno in (errno.EACCES, errno.EPERM, errno.EROFS):
                _tv_diag.falha('resolve.geracao.permissao', erro, arquivo=erro.filename)
                self._gstatus(texto_acesso("Acesso negado ao gerar. Clique em Corrigir acesso. Arquivo: ", "Acceso denegado al generar. Pulsa Corregir acceso. Archivo: ") + str(erro.filename or ''))
                garantir_acesso()
            else:
                _tv_diag.falha('resolve.geracao.erro', erro)
                self._gstatus("Falha na geração: %s" % erro)
        except Exception as erro:
            _tv_diag.falha('resolve.geracao.erro', erro)
            self._gstatus("Falha na geração: %s" % erro)
        finally:
            self._busy = False
            self._cta_normal()

    @_tv_diag.operacao("resolve.geracao")
    def _on_generate_impl(self):
        if not self.confirmar_cores():
            return
        estado = licenca_estado() if LICENCA_ATIVA else {"ok": True}
        if not estado.get("ok"):
            self._gstatus(estado.get("erro") or "A sessão foi encerrada. Abra o plugin para entrar novamente.")
            self._exit = estado.get("motivo") != "permissao"
            return
        import json as _json
        import subprocess
        import tempfile
        import time as _time

        lays = list(self.gen_layouts)
        auto = bool(getattr(self, "gen_auto", False))
        if not auto and (not lays or len(lays) > GEN_LAY_MAX or len(set(lays)) != len(lays) or any(k not in HERO_POS for k in lays)):
            self._gstatus("Escolha de 1 a 3 layouts válidos.")
            return

        proj, tl = get_timeline()
        if not tl:
            self._gstatus("Sem timeline.")
            return
        fps = float(tl.GetSetting("timelineFrameRate") or 24)
        try:
            intervalo = intervalo_geracao(tl)
        except Exception as ex:
            _tv_diag.falha('Titulos Virais.on_generate')
            log("intervalo I/O:", ex)
            self._gstatus("Não consegui ler os limites I/O da timeline.")
            return
        aspect = timeline_aspect(tl)
        mp = proj.GetMediaPool()
        I = self.items
        
        
        max_chars = LINHA_CHARS_REF
        
        max_lines = max(LAY_LINHAS.get(k, 3)
                        for k in (LAY_AUTO if getattr(self, "gen_auto", False)
                                  else (self.gen_layouts or GEN_LAY_DEF)))
        caps_h = bool(I["gcapsH"].Checked)   
        caps_a = bool(I["gcapsA"].Checked)   
        keep_punct = bool(I["gpunct"].Checked)

        
        
        
        import io as _io
        lang = ("auto", "pt", "en", "es", "de", "fr", "it")[
            int(I["glang"].CurrentIndex or 0)]
        
        _definir_idioma(lang if lang != "auto" else IDIOMA)
        
        
        self._busy = True
        self._cta_ocupado("GERANDO…  NÃO MEXA NA TIMELINE")
        self._progresso(0.05, "Exportando o áudio da timeline…")

        def _aviso_render(pct):
            if pct >= 0:
                self._progresso(0.05 + 0.10 * pct / 100.0,
                                "Exportando o áudio pelo Resolve… %d%%" % pct)
            self._passo_ui()

        wav48 = _sound_module.export_without_sfx(tl, lambda: render_audio_timeline(proj, tl, _aviso_render, intervalo[:2] if intervalo[2] else None))
        if not wav48:
            self._busy = False
            self._cta_normal()
            self._gstatus("Não consegui extrair o áudio da timeline.")
            return

        self._progresso(0.15, "Convertendo o áudio…")
        tmp = os.path.dirname(wav48)
        wav = os.path.join(tmp, "tv_fala16k.wav")
        try:
            wav_para_16k_mono(wav48, wav)
        except Exception as ex:
            _tv_diag.falha('Titulos Virais.on_generate')
            self._busy = False
            self._cta_normal()
            self._gstatus("Não consegui converter o áudio.")
            log("conversão do wav:", ex)
            return

        self._progresso(0.22, "Transcrevendo a fala…")
        base = os.path.join(tmp, "tv_fala")

        def _roda_whisper(extra):
            """Run Whisper without freezing Resolve's embedded UI while it decodes."""
            import time as _whisper_time
            command = [WHISPER_BIN, "-m", WHISPER_MODEL, "-f", wav,
                       "-l", lang, "-ml", "1", "-sow", "-of", base] + extra
            started = _whisper_time.monotonic()
            with tempfile.TemporaryFile() as stderr_file:
                process = subprocess.Popen(command, stdout=subprocess.DEVNULL,
                                           stderr=stderr_file, **_sem_janela())
                shown = -1
                while process.poll() is None:
                    elapsed = int(_whisper_time.monotonic() - started)
                    if elapsed != shown:
                        self._progresso(0.22, "Transcrevendo a fala… %ds" % elapsed)
                        shown = elapsed
                    try:
                        disp.StepLoop()
                    except Exception:
                        _tv_diag.falha('Titulos Virais.whisper.StepLoop')
                    _whisper_time.sleep(0.15)
                stderr_file.seek(0)
                detail = stderr_file.read().decode('utf-8', 'replace')
            has_json = os.path.exists(base + '.json')
            _tv_diag.evento('whisper.resultado', retorno=process.returncode,
                            resultado_json_existe=has_json,
                            duracao_segundos=round(_whisper_time.monotonic()-started, 1),
                            modelo_bytes=os.path.getsize(WHISPER_MODEL) if os.path.exists(WHISPER_MODEL) else 0)
            if process.returncode != 0 or not has_json:
                _tv_diag.evento('whisper.falha', executavel=WHISPER_BIN, modelo=WHISPER_MODEL, entrada=wav, retorno=process.returncode, resultado_json_existe=has_json, detalhe_motor='\n'.join(l for l in detail.splitlines() if any(p in l.lower() for p in ('error', 'failed', 'cannot', 'denied', 'not found', 'unsupported')))[:3000])
            return process.returncode == 0 and has_json
        try:
            
            
            
            if not _roda_whisper(["-nfa", "-dtw", "small", "-ojf"]):
                _roda_whisper(["-oj"])
        except Exception as ex:
            _tv_diag.falha('Titulos Virais.on_generate')
            self._busy = False
            self._cta_normal()
            self._gstatus("Não consegui rodar o Whisper. Reinstale o plugin.")
            log("whisper não executou:", ex)
            return

        words = []
        if os.path.exists(base + ".json"):
            
            
            f0 = intervalo[0]
            desloca = f0 / fps * 1000.0
            data = _json.load(_io.open(base + ".json", encoding="utf-8"))
            segs = data.get("transcription", [])
            tem_token = any(seg.get("tokens") for seg in segs)
            
            
            if tem_token:                      
                for seg in segs:
                    for tk in seg.get("tokens", []):
                        txt = tk.get("text", "")
                        if not txt.strip() or txt.startswith("[_"):
                            continue
                        td = tk.get("t_dtw")
                        ms = (td * 10) if (td is not None and td >= 0)                            else (tk.get("offsets") or {}).get("from", 0)
                        a = desloca + ms
                        if words and not txt[:1].isspace():
                            words[-1]["t"] += txt.strip()
                            words[-1]["b"] = a
                            continue
                        words.append({"t": txt.strip(), "a": a, "b": a})
                for i in range(len(words) - 1):    
                    words[i]["b"] = max(words[i]["a"], words[i + 1]["a"])
            else:                              
                for seg in segs:
                    txt = seg.get("text", "")
                    off = seg.get("offsets", {})
                    if not txt.strip():
                        continue
                    fim = desloca + off.get("to", 0)
                    if words and not txt[:1].isspace():
                        words[-1]["t"] += txt.strip()
                        words[-1]["b"] = fim
                        continue
                    words.append({"t": txt.strip(),
                                  "a": desloca + off.get("from", 0),
                                  "b": fim})
        else:
            log("whisper não gerou json")
        for f in (wav48, wav, base + ".json"):
            try:
                os.remove(f)
            except Exception:
                _tv_diag.falha('Titulos Virais.on_generate')
                pass
        try:
            os.rmdir(os.path.dirname(wav48))
        except Exception:
            _tv_diag.falha('Titulos Virais.on_generate')
            pass

        words = [w for w in words if any(c.isalnum() for c in w["t"])]
        words.sort(key=lambda w: w["a"])
        uniq = []
        for w in words:   
            if uniq and w["t"] == uniq[-1]["t"] and abs(w["a"] - uniq[-1]["a"]) < 200:
                continue
            uniq.append(w)
        words = palavras_no_intervalo(uniq, intervalo[0], intervalo[1], fps)
        _tv_diag.evento('resolve.geracao.transcricao', palavras_brutas=len(uniq),
                        palavras_no_intervalo=len(words), idioma=lang)
        if not words:
            self._busy = False
            self._cta_normal()
            self._gstatus("Nenhuma fala reconhecida no áudio da timeline.")
            return

        
        
        words = normalizar_palavras(words, lang if lang != "auto" else IDIOMA)
        planos = planejar_blocos(words, LAY_AUTO if auto else lays, _hero_score)
        blocks = [p["palavras"] for p in planos]
        _tv_diag.evento('resolve.geracao.blocos', blocos=len(blocks),
                        motor=WHISPER_BIN, modelo=WHISPER_MODEL)
        if not blocks:
            self._busy = False
            self._cta_normal()
            self._gstatus("Não há trechos compatíveis com os layouts selecionados.")
            return

        def split_lines(ws, teto):
            """[(texto, inicio_ms da 1ª palavra)] — o início alimenta a escadinha.
            `teto` vem do layout do bloco: 2 linhas num layout de 2, 3 num de 3."""
            max_lines = teto
            
            
            
            total = sum(len(w["t"]) + 1 for w in ws) - 1
            limite = max(max_chars, int((total + teto - 1) // teto))
            lines = []
            line, line_a = "", None
            for w in ws:
                t = w["t"]   
                if not keep_punct:
                    t = t.strip(".,;:!?")
                cand = (line + " " + t).strip()
                if line and len(cand) > limite and len(lines) < max_lines - 1:
                    lines.append((line, line_a))
                    line, line_a = t, w["a"]
                else:
                    if not line:
                        line_a = w["a"]
                    line = cand
            if line:
                lines.append((line, line_a))
            return lines[:max_lines]

        def _texto(ws_):
            out = []
            for w in ws_:
                t = w["t"]   
                if not keep_punct:
                    t = t.strip(".,;:!?")
                out.append(t)
            return " ".join(out).strip()

        def _aplica_caps(ents, hi):
            """Caixa alta por papel: a linha `hi` (herói) usa caps_h; as demais,
            caps_a. hi=None (layout Centro) trata todas como apoio."""
            for j, e in enumerate(ents):
                quer = caps_h if (hi is not None and j == hi) else caps_a
                novo = e["text"].upper() if quer else e["text"]
                if novo != e["text"]:
                    e["text"] = novo
                    self._try(lambda e=e, novo=novo: set_val(e["tool"], "StyledText", novo))

        def quebrar_com_heroi(ws, teto, pos, hp=1):
            """Quebra o bloco deixando o herói com `hp` palavras (1 ou 2).
            `pos` diz onde o herói fica: 'ini', 'fim' ou 'meio'."""
            n = len(ws)
            if n <= 1 or teto <= 1:
                return [(_texto(ws), ws[0]["a"])] if ws else []
            hp = max(1, min(hp, HERO_MAX_PALAVRAS, n - (teto - 1)))
            if pos == "ini":
                grupos = [ws[:hp]] + _reparte(ws[hp:], teto - 1)
            elif pos == "fim":
                grupos = _reparte(ws[:n - hp], teto - 1) + [ws[n - hp:]]
            else:                     
                resto = n - hp
                corte = (resto + 1) // 2
                grupos = [ws[:corte], ws[corte:corte + hp], ws[corte + hp:]]
            grupos = [g for g in grupos if g]
            return [(_texto(g), g[0]["a"]) for g in grupos]

        def _reparte(ws, partes):
            """Divide as palavras em `partes` grupos do tamanho mais parecido."""
            if partes <= 1 or len(ws) <= 1:
                return [ws] if ws else []
            fatia = len(ws) / float(partes)
            saida, ini = [], 0
            for i in range(partes):
                fim = len(ws) if i == partes - 1 else int(round((i + 1) * fatia))
                saida.append(ws[ini:fim])
                ini = fim
            return [g for g in saida if g]

        def _indice_heroi(linhas, pos):
            n = len(linhas)
            if not n or pos is None:
                return None
            return 0 if pos == "ini" else (n - 1 if pos == "fim" else n // 2)

        def _avalia(linhas, pos):
            """(herói só de ligação?, herói curto?, linha comprida?) — nessa
            ordem de prioridade. Herói só de ligação é o pior: é o 'e por' que
            não merece destaque."""
            hi = _indice_heroi(linhas, pos)
            if hi is None:
                return (False, False, False)
            heroi = linhas[hi][0]
            palavras = heroi.split()
            outras = [t for i, (t, _a) in enumerate(linhas) if i != hi]
            so_ligacao = bool(palavras) and all(_classe_heroi(w) == 0 for w in palavras)
            return (so_ligacao,
                    len(heroi) < HERO_MIN_CHARS,
                    bool(outras) and max(len(t) for t in outras) > LINHA_LONGA)

        def _prioridade_heroi(linhas, pos):
            hi = _indice_heroi(linhas, pos)
            if hi is None:
                return 1
            return max((_classe_heroi(w) for w in linhas[hi][0].split()), default=0)

        def linhas_do_bloco(ws, lay):
            """ARRANJO GUIADO POR CONTEÚDO (regra do Bruno; portado 1:1 do
            Premiere). O herói é a MELHOR unidade de conteúdo do bloco (nunca
            ligação/artigo; uma palavra com cinco letras ou mais). O que vem ANTES
            dele vira a linha de cima; o que vem DEPOIS vira a de baixo. O
            layout só decide o TETO de linhas e o estilo — não a palavra do
            herói. Devolve (linhas, layout, hi):
              hi = índice (0-based) da linha do herói; None = sem herói (frase
              vira linha única em cor secundária)."""
            pos = HERO_POS.get(lay)
            if pos is None:                       
                return split_lines(ws, LAY_LINHAS.get(lay, 3)), lay, None
            arr = plano_modelo([w["t"] for w in ws], lay, _hero_score)
            grupos = [[ws[i] for i in g] for g in arr['grupos']]
            return [(_texto(g), g[0]["a"]) for g in grupos], lay, arr['hi']

        def ms2f(ms):
            return int(round(ms / 1000.0 * fps))

        

        
        tpl = [None]

        def find_tpl(folder):
            for c in folder.GetClipList() or []:
                if c.GetName() == TEMPLATE_NAME:
                    tpl[0] = c
            for sub in folder.GetSubFolderList() or []:
                find_tpl(sub)

        find_tpl(mp.GetRootFolder())
        if tpl[0] is None and TEMPLATE_DRB and os.path.isfile(TEMPLATE_DRB):
            try:
                if not mp.ImportFolderFromFile(TEMPLATE_DRB):
                    log("O Resolve recusou a importação do template de legenda.")
            except Exception as erro:
                _tv_diag.falha("Titan.template.import", erro)
                log("Falha ao importar Basic Template:", erro)
            find_tpl(mp.GetRootFolder())
        if tpl[0] is None:
            self._busy = False
            self._cta_normal()
            self._gstatus("Não consegui carregar o template de legenda. Reinicie o Resolve e tente novamente.")
            return
        tpl_fps = float(tpl[0].GetClipProperty("FPS") or fps)

        
        for t in range(2, int(tl.GetTrackCount("video")) + 1):
            olds = [x for x in tl.GetItemListInTrack("video", t) or []
                    if str(x.GetClipColor() or "") == GEN_CLIP_COLOR
                    and int(x.GetStart()) < intervalo[1] and int(x.GetEnd()) > intervalo[0]]
            if olds:
                self._sfx.remove_titles(tl, [str(x.GetUniqueId()) for x in olds])
                tl.DeleteClips(olds)

        
        
        def _track_ok(t):
            if t > int(tl.GetTrackCount("video")):
                return True
            return not any(int(item.GetStart()) < intervalo[1] and int(item.GetEnd()) > intervalo[0]
                           for item in tl.GetItemListInTrack("video", t) or [])
        base = 2
        while not all(_track_ok(t) for t in range(base, base + max_lines)):
            base += 1
            if base > 24:
                self._busy = False
                self._cta_normal()
                self._gstatus("Sem faixas de vídeo livres para gerar.")
                return
        while int(tl.GetTrackCount("video")) < base + max_lines - 1:
            tl.AddTrack("video")
        if base > 2:
            log("Faixas V2+ ocupadas — gerando nas V%d–V%d"
                % (base, base + max_lines - 1))

        
        self.layout.gap = 1.0
        self.layout.scale = 1.0
        self.layout.width = I["gwidth"].Value / 100.0   
        self.layout.cx = self.layout.cy = 0.5
        self.layout.tracking_hero = self.tracking("gtrackH")
        self.layout.tracking_small = self.tracking("gtrackA")
        self.layout.tracking = self.layout.tracking_hero   
        
        gen_dx = I["ghor"].Value / 100.0 - 0.5
        
        
        
        gen_dy = I["galt"].Value / 100.0 - 0.5
        self.layout.hero_font = self._fonte_hero()
        self.layout.small_font = self._fonte_small()
        self.layout.hero_color = self._cor_hero()
        self.layout.small_color = self._cor_small()

        anim_in = bool(I["ganim_in"].Checked)
        anim_out = bool(I["ganim_out"].Checked)
        


        ultimo_lay = [None]

        def layout_do_bloco(i):
            return planos[i]['layout']

        made = 0
        skipped = 0
        generated_entries = []
        for bi, blk in enumerate(blocks):
            tl_f0 = max(intervalo[0], ms2f(blk[0]["a"]))
            f1 = (ms2f(blocks[bi + 1][0]["a"]) if bi + 1 < len(blocks)
                  else ms2f(blk[-1]["b"] + GEN_PAD_MS))
            f1 = min(intervalo[1], f1, ms2f(blk[-1]["b"] + 300))
            if f1 <= tl_f0:
                continue
            dur = f1 - tl_f0             
            f_end = tl_f0 + dur
            lay = layout_do_bloco(bi)
            lines, lay, hi = linhas_do_bloco(blk, lay)
            entries = []
            hi_entry = None       
            
            
            lead = int(self.anim.dur) if anim_in else 0
            floor = tl_f0
            for j, (txt, a_ms) in enumerate(lines):
                lf0 = tl_f0
                if j > 0 and a_ms is not None:
                    
                    lf0 = max(floor, min(ms2f(a_ms) - lead, f_end - 6))
                dur_j = max(1, f_end - lf0)
                source_frames = int(dur_j * tpl_fps / fps)
                if source_frames < 1:
                    skipped += 1
                    continue
                items = mp.AppendToTimeline([{
                    "mediaPoolItem": tpl[0], "startFrame": 0,
                    "endFrame": source_frames - 1,
                    "recordFrame": lf0, "trackIndex": base + j}])
                it = items[0] if items else None
                comp = tool = None
                for _try in range(4):
                    try:
                        comp = it.GetFusionCompByIndex(1) if it else None
                        tool = comp.FindToolByID("TextPlus") if comp else None
                    except Exception:
                        _tv_diag.falha('Titulos Virais.on_generate')
                        tool = None
                    if tool is not None:
                        break
                    _time.sleep(0.25)
                if tool is None:
                    skipped += 1
                    log("bloco %d linha %d NÃO inserida (faixa V%d @f%d)"
                        % (bi + 1, j + 1, base + j, lf0))
                    continue
                try:
                    it.SetClipColor(GEN_CLIP_COLOR)
                except Exception:
                    _tv_diag.falha('Titulos Virais.on_generate')
                    pass
                set_val(tool, "StyledText", txt)
                
                set_val(tool, "Enabled2", 0)
                set_val(tool, "Enabled4", 0)
                st_, en_ = int(it.GetStart()), int(it.GetEnd())
                if j == 0:
                    floor = st_        
                if hi is not None and j == hi:
                    hi_entry = len(entries)   
                entries.append({"item": it, "track": base + j, "comp": comp,
                                "tool": tool, "text": txt, "start": st_,
                                "end": en_, "uid": _uid(it, 2 + j, st_)})
            if len(entries) >= 2:
                
                _aplica_caps(entries, hi_entry)   
                self.layout.apply(entries, lay, aspect, hero_idx=hi_entry)
            elif len(entries) == 1:
                
                
                eh_hero = (hi_entry == 0)
                _aplica_caps(entries, 0 if eh_hero else None)
                self.layout.apply(entries, "center", aspect,
                                  hero_idx=(0 if eh_hero else None))
            
            if gen_dx or gen_dy:
                for en2 in entries:
                    self._try(lambda en2=en2: set_move(en2, gen_dx, gen_dy))
            if anim_in or anim_out:
                for j2, en2 in enumerate(entries):
                    st2 = self.anim.state(en2)
                    if anim_in:
                        efeitos, d = anim_receita(bi, j2, len(entries))
                        st2["in"] = set(efeitos)
                        st2["dir_in"] = d
                        mapped=self._mapped_sound_for_state(st2,"in")
                        if mapped is not None:st2["sfx_in"]=mapped
                    if anim_out:
                        efeitos, d = ANIM_OUT
                        st2["out"] = set(efeitos)
                        st2["dir_out"] = d
                        mapped=self._mapped_sound_for_state(st2,"out")
                        if mapped is not None:st2["sfx_out"]=mapped
                    self._anim_salvar(en2, st2)
                    self._try(lambda en2=en2: self.anim.render(en2))
            generated_entries.extend(entries)
            made += 1
            self._progresso(0.30 + 0.70 * made / float(len(blocks)),
                            "Gerando… %d/%d blocos" % (made, len(blocks)))
        try:
            last_tc = "%.1fs" % (blocks[-1][-1]["b"] / 1000.0)
        except Exception:
            _tv_diag.falha('Titulos Virais.on_generate')
            last_tc = "?"
        log("geração: %d palavras, %d blocos, última fala em %s"
            % (len(words), len(blocks), last_tc))
        _tv_diag.evento('resolve.geracao.concluida', palavras=len(words),
                        blocos=len(blocks), titulos_criados=made, linhas_puladas=skipped)
        self._busy = False
        self._cta_normal()
        if skipped:
            self._progresso(1.0, "Pronto: %d blocos (%d linhas puladas)."
                            % (made, skipped))
        else:
            self._progresso(1.0, "Pronto: %d blocos de legenda gerados." % made)
        self._sync_sounds(generated_entries)
        self.refresh(force=True)
        self._progresso(0.0)

    def run(self):
        self.win.Show()
        
        for _m in ("Raise", "ActivateWindow"):
            try:
                getattr(self.win, _m)()
            except Exception:
                _tv_diag.falha('Titulos Virais.run')
                pass
        _recuperar_janela("%s %s" % (APP_NAME, APP_VERSION), _tv_diag)
        log("janela %s aberta." % WIN_ID)
        self._exit = False
        self._closable = False
        if getattr(disp, "StepLoop", None):
            import time as _t
            last = 0.0
            aberto = _t.time()
            subiu = False
            checou = False
            ultima_licenca = _t.time()
            consulta_licenca = None
            estado_licenca = []
            while not self._exit:
                if LICENCA_ATIVA and estado_licenca:
                    estado = estado_licenca.pop()
                    if not estado.get("ok"):
                        self._gstatus(estado.get("erro") or "A sessão foi encerrada. Abra o plugin para entrar novamente.")
                        if estado.get("motivo") != "permissao":
                            self._exit = True
                            break
                if LICENCA_ATIVA and _t.time() - ultima_licenca >= 60 and (consulta_licenca is None or not consulta_licenca.is_alive()):
                    import threading
                    ultima_licenca = _t.time()
                    consulta_licenca = threading.Thread(target=lambda: estado_licenca.append(licenca_estado()), daemon=True)
                    consulta_licenca.start()
                self._poll_update()
                if not self._closable and _t.time() - aberto > 1.0:
                    self._closable = True
                if not checou and _t.time() - aberto > 1.2:
                    
                    
                    checou = True
                    self.mostrar_update()
                if not subiu and _t.time() - aberto > 0.4:
                    _recuperar_janela("%s %s" % (APP_NAME, APP_VERSION), _tv_diag)
                    subiu = True          
                    for _m in ("Show", "Raise", "ActivateWindow"):
                        try:
                            getattr(self.win, _m)()
                        except Exception:
                            _tv_diag.falha('Titulos Virais.run')
                            pass
                try:
                    disp.StepLoop()
                except Exception as ex:
                    
                    
                    
                    
                    _tv_diag.falha('Titulos Virais.run')
                    log("Auto-refresh indisponível (%s) — use o botão ↻ "
                        "(reinicie o Resolve para restaurar)." % ex)
                    return
                _t.sleep(0.03)
                
                
                
                if not getattr(self, "_busy", False):
                    self._try(self._poll_edit_sliders)
                    self._try(self._poll_gsliders)
                    self._try(self._poll_pos)
                now = _t.time()
                if now - last >= 0.6:
                    last = now
                    self._try(self.refresh)
                    if int(now) % 3 == 0:
                        self._try(self._salvar_geo)
        else:
            self._closable = True
            disp.RunLoop()
        self._closing = True
        self._close_about()
        self.win.Hide()
        try:
            self.win.Close()
        except Exception:
            _tv_diag.falha('Titulos Virais.run')
            pass


def run_app():
    while True:
        application = App()
        application.run()
        if not getattr(application, "_restart_language", False):
            break


def garantir_acesso():
    return True
def _old_acesso():
    falhas = problemas_acesso()
    if not falhas:
        return True
    wid = 'TV_Acesso_' + str(id(falhas))
    win = disp.AddWindow({"ID": wid, "WindowTitle": APP_NAME,
        "Geometry": [440, 220, 520, 300], "StyleSheet": STYLE,
        "WindowFlags": {"Window": True, "WindowStaysOnTopHint": True}}, [
        ui.VGroup({"Spacing": 14, "Margin": 22}, [
            ui.Label({"Text": texto_acesso("Precisamos liberar o acesso", "Necesitamos habilitar el acceso"), "StyleSheet": "font-size:20px;font-weight:bold;color:#38bdf8;", "Weight": 0}),
            ui.Label({"Text": texto_acesso("O plugin não consegue usar suas pastas de trabalho. Clique abaixo e autorize a solicitação do sistema. Não é necessário usar o Terminal.", "El plugin no puede usar sus carpetas de trabajo. Pulsa abajo y autoriza la solicitud del sistema. No necesitas usar Terminal."), "WordWrap": True, "Weight": 0}),
            ui.Label({"ID": "ac_detalhe", "Text": falhas[0]['arquivo'], "WordWrap": True}),
            ui.HGroup({"Weight": 0}, [
                ui.Button({"ID": "ac_fechar", "Text": texto_acesso("Agora não", "Ahora no")}),
                ui.Button({"ID": "ac_reparar", "Text": texto_acesso("Corrigir acesso", "Corregir acceso")}),
                ui.Button({"ID": "ac_verificar", "Text": texto_acesso("Verificar novamente", "Volver a comprobar")})])])])
    items = win.GetItems()
    state = {'done': False, 'ok': False}
    def finish(ev=None):
        state['done'] = True
        if not getattr(disp, 'StepLoop', None): disp.ExitLoop()
    def check(ev=None):
        current = problemas_acesso()
        if not current:
            state['ok'] = True; finish()
        else:
            items['ac_detalhe'].Text = texto_acesso("Ainda sem acesso: ", "Todavía sin acceso: ") + current[0]['arquivo']
    def repair(ev=None):
        items['ac_reparar'].Enabled = False
        try:
            ok, message = corrigir_permissao()
            items['ac_detalhe'].Text = message
            if ok: check()
        finally:
            items['ac_reparar'].Enabled = True
    win.On[wid].Close = finish
    win.On.ac_fechar.Clicked = finish
    win.On.ac_reparar.Clicked = repair
    win.On.ac_verificar.Clicked = check
    win.Show()
    try:
        if getattr(disp, 'StepLoop', None):
            import time
            while not state['done']:
                disp.StepLoop(); time.sleep(0.03)
        else: disp.RunLoop()
    finally:
        win.Hide(); win.Close()
    return state['ok']


if garantir_acesso():
    _lic = licenca_estado() if LICENCA_ATIVA else {"ok": True, "motivo": "trava_desligada"}
    if not _lic["ok"]:
        log("licença: %s" % _lic.get("motivo"))
        if not Login(_lic).run():
            log("Ativação não concluída — o plugin não vai abrir.")
        else:
            run_app()
    else:
        if _lic.get("aviso"):
            log(_lic["aviso"])
        run_app()
