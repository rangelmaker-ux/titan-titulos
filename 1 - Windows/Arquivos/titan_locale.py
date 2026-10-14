"""Interface-only localization. Never translates transcript text or font names."""
import re

LANGUAGES=('pt-BR','en','es')
LANGUAGE_NAMES=('Português (Brasil)','English','Español')
LANG='pt-BR'
# Portuguese source | English | Spanish
ROWS='''
Efeito sonoro|Sound effect|Efecto sonoro
Automático|Automatic|Automático
Sem som|No sound|Sin sonido
Impacto — Bounce|Impact — Bounce|Impacto — Bounce
Cliques — Shake|Clicks — Shake|Clics — Shake
Ar — Blur|Air — Blur|Aire — Blur
LEGENDAS|CAPTIONS|SUBTÍTULOS
TÍTULOS|TITLES|TÍTULOS
ANIMAÇÕES|ANIMATIONS|ANIMACIONES
TRANSCRIÇÃO|TRANSCRIPTION|TRANSCRIPCIÓN
IDIOMA DO ÁUDIO|AUDIO LANGUAGE|IDIOMA DEL AUDIO
MODO DE TRANSCRIÇÃO|TRANSCRIPTION MODE|MODO DE TRANSCRIPCIÓN
GERAR LEGENDAS|GENERATE CAPTIONS|GENERAR SUBTÍTULOS
COMPOSIÇÃO|COMPOSITION|COMPOSICIÓN
CONFIGURAÇÕES|SETTINGS|CONFIGURACIÓN
FONTE E COR|FONT AND COLOR|FUENTE Y COLOR
FONTE PRINCIPAL|MAIN FONT|FUENTE PRINCIPAL
FONTE SECUNDÁRIA|SUPPORTING FONT|FUENTE SECUNDARIA
Branco|White|Blanco
Azul Metálico|Metallic Blue|Azul Metálico
Azul Cobalto|Cobalt Blue|Azul Cobalto
Ciano Elétrico|Electric Cyan|Cian Eléctrico
Amarelo Ouro|Gold Yellow|Amarillo Oro
Verde Neon|Neon Green|Verde Neón
Roxo Titânio|Titanium Purple|Púrpura Titanio
Rosa Choque|Hot Pink|Rosa Fuerte
Vermelho|Red|Rojo
Central 3|Center 3|Central 3
Central ↑|Center ↑|Central ↑
Central ↓|Center ↓|Central ↓
Duplo ↑|Double ↑|Doble ↑
Duplo ↓|Double ↓|Doble ↓
Centro|Center|Centro
automático · sorteia por bloco|automatic · random per block|automático · aleatorio por bloque
%d layouts · alterna por bloco|%d layouts · alternates per block|%d diseños · alterna por bloque
Layout: %s|Layout: %s|Diseño: %s
AJUSTES|ADJUSTMENTS|AJUSTES
ENTRADA E SAÍDA|IN AND OUT|ENTRADA Y SALIDA
ENTRADA|IN|ENTRADA
SAÍDA|OUT|SALIDA
PRÉVIA|PREVIEW|VISTA PREVIA
LINHAS SOB O PLAYHEAD|LINES AT PLAYHEAD|LÍNEAS BAJO EL CABEZAL
LAYOUT|LAYOUT|DISEÑO
AUTO|AUTO|AUTO
Principal|Main|Principal
Apoio|Supporting|Apoyo
Secundárias|Supporting|Secundarias
Tamanho|Size|Tamaño
Posição X|Position X|Posición X
Posição Y|Position Y|Posición Y
Horizontal|Horizontal|Horizontal
Vertical|Vertical|Vertical
Altura|Height|Altura
Largura|Width|Ancho
Duração|Duration|Duración
Distância|Distance|Distancia
Espaçamento|Spacing|Espaciado
Faixa|Track|Pista
Texto|Text|Texto
centro|center|centro
Todas|All|Todas
Nenhuma|None|Ninguna
Slide|Slide|Deslizamiento
Bounce|Bounce|Rebote
Flicker|Flicker|Parpadeo
Shake|Shake|Temblor
Blur|Blur|Desenfoque
Motion Blur|Motion Blur|Desenfoque de movimiento
Debug|Diagnostics|Diagnóstico
Aplicar posição a todos|Apply position to all|Aplicar posición a todos
Aplica X e Y a todos os Text+ desta timeline. Alterações seguintes continuam locais.|Apply X and Y to every Text+ on this timeline. Later edits remain local.|Aplica X e Y a todos los Text+ de esta línea de tiempo. Los cambios posteriores siguen siendo locales.
Posição aplicada a %d títulos.|Position applied to %d titles.|Posición aplicada a %d títulos.
Nenhum título Text+ encontrado.|No Text+ titles found.|No se encontraron títulos Text+.
Não foi possível aplicar a posição a %d títulos.|Could not apply position to %d titles.|No se pudo aplicar la posición a %d títulos.
Idioma da interface|Interface language|Idioma de la interfaz
About|About|Acerca de
Sobre o Titan Titles Studio|About Titan Titles Studio|Acerca de Titan Titles Studio
Direitos de criação: RangelMaker_|Created by: RangelMaker_|Derechos de creación: RangelMaker_
Todos os direitos reservados.|All rights reserved.|Todos los derechos reservados.
Comunidade no Telegram|Telegram community|Comunidad en Telegram
Fechar|Close|Cerrar
Efeitos sonoros|Sound effects|Efectos de sonido
Whoosh na entrada; saída mais baixa; glitch no flicker. Usa faixas de áudio próprias.|Whoosh on entry; quieter exit; glitch for flicker. Uses dedicated audio tracks.|Whoosh al entrar; salida más baja; glitch para parpadeo. Usa pistas de audio propias.
Efeitos sonoros ativados.|Sound effects enabled.|Efectos de sonido activados.
Efeitos sonoros desativados. Sons existentes permanecem até reaplicar a animação.|Sound effects disabled. Existing sounds remain until animation is reapplied.|Efectos desactivados. Los sonidos existentes permanecen hasta volver a aplicar la animación.
Não foi possível sincronizar os efeitos sonoros. Confira as faixas de áudio.|Could not sync sound effects. Check the audio tracks.|No se pudieron sincronizar los efectos. Revisa las pistas de audio.
Falha nos efeitos sonoros|Sound effects failed|Fallo en los efectos de sonido
Os sons não puderam ser gerados. Os títulos foram preservados.|Sounds could not be generated. Your titles were preserved.|No se pudieron generar los sonidos. Los títulos se conservaron.
Sem direção|No direction|Sin dirección
Limpar animação|Clear animation|Borrar animación
Usar fonte|Use font|Usar fuente
Escolha um estilo para aplicar às linhas sob o playhead.|Choose a style for the lines at the playhead.|Elige un estilo para las líneas bajo el cabezal.
aplica só no bloco sob o playhead|applies only to the current block|se aplica solo al bloque actual
Entrada desacelera, saída acelera. Só nas linhas selecionadas.|Entry slows down, exit speeds up. Selected lines only.|La entrada desacelera y la salida acelera. Solo líneas seleccionadas.
Reler os Text+ sob o playhead|Refresh Text+ at the playhead|Actualizar Text+ bajo el cabezal
Sem seleção = todas · 1 = principal|No selection = all · 1 = main|Sin selección = todas · 1 = principal
Deixa o plugin sortear um layout por bloco|Choose a random layout for each block|Elige un diseño aleatorio para cada bloque
Deixe ativas apenas as faixas de voz. Silencie músicas e efeitos na timeline.|Keep only voice tracks active. Mute music and effects on the timeline.|Mantén activas solo las pistas de voz. Silencia música y efectos en la línea de tiempo.
Animar entrada|Animate entry|Animar entrada
Animar saída|Animate exit|Animar salida
Animação de entrada variada por linha e por bloco|Vary entry animation by line and block|Varía la animación de entrada por línea y bloque
Animação de saída (blur + opacidade)|Exit animation (blur + opacity)|Animación de salida (desenfoque + opacidad)
Usar pontuação|Use punctuation|Usar puntuación
Manter a pontuação da fala|Keep speech punctuation|Mantener la puntuación del habla
Caixa alta principal|Uppercase main text|Principal en mayúsculas
Caixa alta apoio|Uppercase supporting text|Apoyo en mayúsculas
Texto principal em CAIXA ALTA|Main text in UPPERCASE|Texto principal en MAYÚSCULAS
Linhas de apoio em CAIXA ALTA|Supporting lines in UPPERCASE|Líneas de apoyo en MAYÚSCULAS
Código da cor, ex: #38bdf8|Color code, e.g. #38bdf8|Código de color, ej.: #38bdf8
Cor inválida: use #RRGGBB ou #RGB.|Invalid color: use #RRGGBB or #RGB.|Color no válido: usa #RRGGBB o #RGB.
‹ voltar|‹ back|‹ volver
Automático|Automatic|Automático
Português|Portuguese|Portugués
Alta (recomendado)|High (recommended)|Alta (recomendada)
Sem timeline|No timeline|Sin línea de tiempo
Sem timeline.|No timeline.|Sin línea de tiempo.
Sem linhas sob o playhead|No lines at the playhead|Sin líneas bajo el cabezal
%d linhas · %s|%d lines · %s|%d líneas · %s
%s disponível · GitHub|%s available · GitHub|%s disponible · GitHub
Baixar|Download|Descargar
Instalar|Install|Instalar
Concluído|Done|Listo
Baixando atualização…|Downloading update…|Descargando actualización…
Baixando atualização… %d%%|Downloading update… %d%%|Descargando actualización… %d%%
Baixando atualização… %.1f MB|Downloading update… %.1f MB|Descargando actualización… %.1f MB
Pronto para instalar. Backup automático.|Ready to install. Automatic backup.|Listo para instalar. Copia de seguridad automática.
Atualizado! Reabra o Titan Titles Studio.|Updated! Reopen Titan Titles Studio.|¡Actualizado! Vuelve a abrir Titan Titles Studio.
Abrir logs|Open logs|Abrir registros
Abrir registros|Open logs|Abrir registros
Corrigir acesso|Fix access|Corregir acceso
sair|sign out|salir
saindo…|signing out…|saliendo…
conta desconectada|signed out|cuenta desconectada
Você saiu da conta. Feche e abra o plugin para entrar de novo.|You signed out. Reopen the plugin to sign in again.|Has cerrado sesión. Vuelve a abrir el plugin para entrar.
Conferindo…|Checking…|Comprobando…
Convertendo o áudio…|Converting audio…|Convirtiendo audio…
Exportando o áudio da timeline…|Exporting timeline audio…|Exportando audio de la línea de tiempo…
Exportando o áudio pelo Resolve… %d%%|Exporting audio with Resolve… %d%%|Exportando audio con Resolve… %d%%
Transcrevendo a fala…|Transcribing speech…|Transcribiendo el habla…
Gerando… %d/%d blocos|Generating… %d/%d blocks|Generando… %d/%d bloques
Pronto: %d blocos (%d linhas puladas).|Done: %d blocks (%d lines skipped).|Listo: %d bloques (%d líneas omitidas).
Pronto: %d blocos de legenda gerados.|Done: %d caption blocks generated.|Listo: %d bloques de subtítulos generados.
Erro: %s|Error: %s|Error: %s
Escolha de 1 a 3 layouts válidos.|Choose 1 to 3 valid layouts.|Elige de 1 a 3 diseños válidos.
Nenhuma fala reconhecida no áudio da timeline.|No speech detected in timeline audio.|No se detectó habla en el audio de la línea de tiempo.
Não consegui converter o áudio.|Could not convert audio.|No se pudo convertir el audio.
Não consegui extrair o áudio da timeline.|Could not extract timeline audio.|No se pudo extraer el audio de la línea de tiempo.
Não consegui ler os limites I/O da timeline.|Could not read timeline in/out points.|No se pudieron leer los puntos de entrada y salida.
Não consegui rodar o Whisper. Reinstale o plugin.|Could not run Whisper. Reinstall the plugin.|No se pudo ejecutar Whisper. Reinstala el plugin.
Não há trechos compatíveis com os layouts selecionados.|No segments match the selected layouts.|No hay segmentos compatibles con los diseños seleccionados.
Sem faixas de vídeo livres para gerar.|No free video tracks available.|No hay pistas de video libres.
Template de legenda não encontrado.|Caption template not found.|No se encontró la plantilla de subtítulos.
E-MAIL DA COMPRA|PURCHASE EMAIL|EMAIL DE COMPRA
SENHA|PASSWORD|CONTRASEÑA
ENTRAR|SIGN IN|ENTRAR
CÓDIGO QUE CHEGOU NO E-MAIL|CODE SENT TO YOUR EMAIL|CÓDIGO RECIBIDO POR EMAIL
Use o e-mail da compra. No primeiro acesso, deixe a senha em branco.|Use your purchase email. Leave the password empty on first access.|Usa el email de compra. En el primer acceso deja la contraseña vacía.
esqueci minha senha|forgot password|olvidé mi contraseña
sua senha|your password|tu contraseña
NÃO, CANCELAR|NO, CANCEL|NO, CANCELAR
'''
TABLE={}
for row in ROWS.strip().splitlines():
    source,en,es=row.split('|')
    TABLE[source]={'en':en,'es':es}

def configure(language):
    global LANG
    LANG=language if language in LANGUAGES else 'pt-BR'
    return LANG

def translate(text):
    if not isinstance(text,str) or LANG=='pt-BR':return text
    if text.strip()!=text and text.strip():
        start=len(text)-len(text.lstrip());end=len(text.rstrip())
        return text[:start]+translate(text[start:end])+text[end:]
    if text in TABLE:return TABLE[text][LANG]
    if '<' in text and '>' in text:
        return re.sub(r'(?<=>)[^<>]+(?=<)',lambda m:translate(m.group(0)),text)
    for template,targets in TABLE.items():
        if '%' not in template:continue
        tokens=re.findall(r'%(?:\.\d+)?[sdf]|%%',template)
        pattern=re.escape(template)
        for token in tokens:
            pattern=pattern.replace(re.escape(token),'%' if token=='%%' else '(.+?)',1)
        match=re.fullmatch(pattern,text)
        if match:
            groups=iter(match.groups())
            return re.sub(r'%(?:\.\d+)?[sdf]|%%',lambda m:'%' if m.group(0)=='%%' else next(groups),targets[LANG])
    return text

class UIProxy:
    def __init__(self,raw):self.raw=raw
    def __getattr__(self,name):
        target=getattr(self.raw,name)
        if not callable(target):return target
        def call(*args,**kwargs):
            args=list(args)
            if args and isinstance(args[0],dict):
                props=dict(args[0])
                for key in ('Text','ToolTip','PlaceholderText'):
                    if key in props:props[key]=translate(props[key])
                args[0]=props
            return target(*args,**kwargs)
        return call

class WidgetProxy:
    def __init__(self,raw,identity):
        object.__setattr__(self,'raw',raw);object.__setattr__(self,'identity',identity)
    def __getattr__(self,name):
        value=getattr(self.raw,name)
        if name=='AddItem' and self.identity in ('gmodel',):
            return lambda text:value(translate(text))
        return value
    def __setattr__(self,name,value):
        if name in ('Text','ToolTip') and self.identity not in ('gpreview','preview') and not self.identity.startswith(('gfam','gest','ghex')):
            value=translate(value)
        setattr(self.raw,name,value)

def wrap_items(items):
    return {key:WidgetProxy(value,key) for key,value in items.items()}
