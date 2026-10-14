"""Titan Titles Studio for FilmCraft. Native editable graphics over loopback RPC."""
from __future__ import annotations
import audioop
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import uuid
import wave

VERSION = '1.1.0'
TICKS = 254016000000
PORT = 19876
ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]/'src'))
DATA = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'TitanFilmCraft'
ANIMATIONS = {'slide': 'Slide', 'bounce': 'Bounce', 'flicker': 'Flicker',
              'shake': 'Shake', 'blur': 'Blur', 'mblur': 'Motion Blur'}
SOUNDS = dict(zip(ANIMATIONS, ('whoosh', 'bounce', 'glitch', 'shake', 'airy', 'motionblur')))
TITLE = re.compile(r'^TitanFC\[([a-z]+)/(-?\d+)\]@([0-9.]+)(?::([0-9.]+))? ')
MODEL_SHA = '1be3a9b2063867b937e64e2ec7483364a79917e157fa98c5d94b5c1fffea987b'
STOP = set('a o as os um uma de da do das dos e ou que para por com em no na nos nas se ao eu voce você ele ela isso isto the a an and or to of in on is it you we i for with el la los las un una de y o en que por para con'.split())

def ticks(seconds):
    return round(float(seconds) * TICKS)

def filmcraft_path():
    path = Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'FilmCraft/filmcraft.exe'
    if not path.is_file():
        raise RuntimeError('FilmCraft não encontrado. Instale o FilmCraft antes do Titan.')
    return path

class Bridge:
    def __init__(self, port=PORT):
        self.port = int(port)

    def call(self, method, params=None, timeout=120):
        request = {'id': uuid.uuid4().hex, 'method': method, 'params': params or {}}
        try:sock=socket.create_connection(('127.0.0.1', self.port), timeout=5)
        except OSError as error:
            raise RuntimeError('Conexão indisponível. Salve e feche o FilmCraft e use Abrir FilmCraft com Titan.') from error
        with sock:
            sock.settimeout(timeout)
            sock.sendall((json.dumps(request, ensure_ascii=False) + '\n').encode())
            with sock.makefile('rb') as stream:
                line = stream.readline(32 * 1024 * 1024)
        if not line.endswith(b'\n'):
            raise RuntimeError('Resposta incompleta do FilmCraft.')
        answer = json.loads(line)
        if answer.get('id') != request['id'] or not answer.get('ok'):
            raise RuntimeError(str(answer.get('error', 'Resposta inválida do FilmCraft.')))
        return answer.get('result')

    def execute(self, command, **params):
        return self.call('engine.execute', {'command': command, 'params': params}, timeout=3600)

def parse_srt(text):
    blocks = []
    pattern = re.compile(r'(\d{2,}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2,}):(\d{2}):(\d{2})[,.](\d{3})')
    for part in re.split(r'\n\s*\n', text.replace('\r', '').lstrip('\ufeff').strip()):
        match = pattern.search(part)
        if not match:
            continue
        v = list(map(int, match.groups()))
        start = v[0]*3600+v[1]*60+v[2]+v[3]/1000
        end = v[4]*3600+v[5]*60+v[6]+v[7]/1000
        caption = re.sub(r'<[^>]+>', '', part[match.end():]).strip().replace('\n', ' ')
        if caption and end > start:
            blocks.append({'start': start, 'end': end, 'text': caption})
    if not blocks:
        raise ValueError('O arquivo não contém legendas SRT válidas.')
    return sorted(blocks, key=lambda b: b['start'])

def split_words(words):
    """Keep actual word timestamps; short groups, split on a pause or punctuation."""
    blocks, group = [], []
    for word in words:
        if group and (len(group) >= 6 or len(' '.join(w['text'] for w in group)) + len(word['text']) > 42
                      or word['start'] - group[-1]['end'] > .6):
            blocks.append(group); group = []
        group.append(word)
        if re.search(r'[.!?]$', word['text']):
            blocks.append(group); group = []
    if group:
        blocks.append(group)
    return [{'text': ' '.join(w['text'] for w in g), 'start': g[0]['start'],
             'end': max(g[-1]['end'], g[0]['start']+.1), 'words': g} for g in blocks]

def highlight(block):
    text = block['text']
    explicit = re.search(r'\[([^\[\]]+)\]', text)
    clean = text.replace('[', '').replace(']', '')
    words = clean.split()
    if explicit:
        start = len(text[:explicit.start()].split())
        count = len(explicit[1].split())
    else:
        candidates = [(len(re.sub(r'\W', '', w)), i) for i, w in enumerate(words)
                      if w.strip('.,!?;:').lower() not in STOP and len(re.sub(r'\W', '', w)) >= 5]
        if not candidates:
            return None
        _, start = max(candidates, key=lambda x: (x[0], -x[1])); count = 1
    if block.get('words') and start < len(block['words']):
        at = block['words'][start]['start']
    else:
        at = block['start'] + (block['end']-block['start'])*start/max(1, len(words))
    return (' '.join(words[:start]), ' '.join(words[start:start+count]),
            ' '.join(words[start+count:]), at)

def pcm16(source, destination):
    with wave.open(str(source), 'rb') as inp:
        channels, width, rate = inp.getnchannels(), inp.getsampwidth(), inp.getframerate()
        raw = inp.readframes(inp.getnframes())
    if channels not in (1, 2):
        raise ValueError('Exporte uma faixa mono ou estéreo para transcrever.')
    if width == 1:
        raw = audioop.bias(raw, 1, -128)
    raw = audioop.lin2lin(raw, width, 2)
    if channels == 2:
        raw = audioop.tomono(raw, 2, .5, .5)
    raw, _ = audioop.ratecv(raw, 2, 1, rate, 16000, None)
    with wave.open(str(destination), 'wb') as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(16000); out.writeframes(raw)

def get_model(progress):
    candidates = [DATA/'motor/ggml-small.bin', DATA.parent/'TitulosVirais/motor/ggml-small.bin']
    for model in candidates:
        if model.is_file() and model.stat().st_size == 487601967:
            # Verify even a shared model before handing it to the native parser.
            progress('Conferindo modelo de transcrição…')
            with model.open('rb') as f:
                if hashlib.file_digest(f, 'sha256').hexdigest() == MODEL_SHA:
                    return model
    model = candidates[0]; model.parent.mkdir(parents=True, exist_ok=True)
    partial = model.with_suffix('.download')
    request = urllib.request.Request('https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin', headers={'User-Agent': 'TitanFilmCraft/'+VERSION})
    digest = hashlib.sha256(); count = 0
    try:
        with urllib.request.urlopen(request, timeout=60) as response, partial.open('wb') as out:
            while chunk := response.read(1024*1024):
                out.write(chunk); digest.update(chunk); count += len(chunk)
                progress('Baixando modelo: %d / 488 MB' % (count//1000000))
        if digest.hexdigest() != MODEL_SHA:
            raise ValueError('O modelo baixado não passou na verificação SHA256.')
        partial.replace(model)
    finally:
        partial.unlink(missing_ok=True)
    return model

def transcribe(bridge, language, progress):
    sequence = bridge.execute('sequence.inspect')
    if not sequence.get('duration'):
        raise ValueError('A sequência está vazia.')
    if not any(t['items'] and not t.get('muted') and t.get('enabled', True) for t in sequence['audio']):
        raise ValueError('Não há faixa de áudio ativa para transcrever.')
    model = get_model(progress)
    engine = ROOT/'motor/whisper-cli.exe'
    if not engine.is_file() and not getattr(sys,'frozen',False):
        engine=DATA.parent/'TitulosVirais/motor/whisper-cli.exe'
    if not engine.is_file():
        raise RuntimeError('Motor de transcrição ausente. Reinstale o Titan para FilmCraft.')
    DATA.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='transcricao-', dir=DATA) as directory:
        raw, wav = Path(directory)/'timeline.wav', Path(directory)/'speech.wav'
        progress('Exportando áudio da sequência…')
        result = bridge.execute('file.exportMedia', path=str(raw), format='wav', range='entire', wait=True)
        if result.get('offlineMedia'):
            raise ValueError('A sequência contém mídia offline. Reconecte os arquivos antes de gerar.')
        pcm16(raw, wav)
        progress('Transcrevendo áudio localmente…')
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        process = subprocess.run([str(engine), '-m', str(model), '-f', str(wav), '-l', language,
                                  '-ojf', '-of', str(Path(directory)/'result'), '-ml', '1', '-sow', '-np'],
                                 capture_output=True, creationflags=flags, timeout=3600)
        output = Path(directory)/'result.json'
        if process.returncode or not output.is_file():
            raise RuntimeError('Falha na transcrição: '+process.stderr.decode('utf-8', 'replace')[-1200:])
        result = json.loads(output.read_text(encoding='utf-8'))
        words = []
        for segment in result.get('transcription', []):
            text = segment.get('text', '').strip()
            times = segment.get('offsets', {})
            if text and not text.startswith('[') and times.get('to', 0) > times.get('from', 0):
                words.append({'text': text, 'start': times['from']/1000, 'end': times['to']/1000})
        if not words:
            raise ValueError('Nenhuma fala encontrada no áudio ativo.')
        # Guard against switching the editor to another sequence during transcription.
        if bridge.execute('sequence.inspect')['id'] != sequence['id']:
            raise ValueError('A sequência ativa mudou. Volte à sequência transcrita e tente novamente.')
        return split_words(words)

def fit_sound(source, destination, seconds, gain):
    with wave.open(str(source), 'rb') as inp:
        channels, width, rate = inp.getnchannels(), inp.getsampwidth(), inp.getframerate()
        raw = inp.readframes(inp.getnframes())
    if width != 2 or channels != 2:
        raise ValueError('Efeito sonoro deve ser WAV estéreo PCM16.')
    length = max(1, round(seconds*rate)); raw = raw[:length*4].ljust(length*4, b'\0')
    from array import array
    samples = array('h'); samples.frombytes(raw)
    for i in range(length):
        fade = max(0, min(1, i/max(1,rate*.006), (length-1-i)/max(1,rate*.04)))
        for c in (0, 1):
            samples[i*2+c] = round(samples[i*2+c]*gain*fade)
    with wave.open(str(destination), 'wb') as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate); out.writeframes(samples.tobytes())

class Titan:
    def __init__(self, bridge, progress=lambda message: None):
        self.bridge, self.progress = bridge, progress

    def command(self, command, **params):
        return self.bridge.execute(command, **params)

    def key(self, clip, effect, param, at, value):
        self.command('effects.setParam', clip=clip, effect=effect, param=param, time=at,
                     value=value, keyframe=True)

    def clear(self, clips):
        if not clips:return
        previous=self.command('state.inspect').get('linked_selection',True)
        try:
            self.command('sequence.linkedSelection',on=False)
            self.command('edit.clear',clips=clips)
        finally:self.command('sequence.linkedSelection',on=previous)

    def animate(self, clip, layer, animation, start, end, fps):
        layers = self.command('graphics.list', clip=clip)['layers']
        entry = next(x for x in layers if x['layer'] == layer)
        effect = entry['effectIndex']; x, y = entry['position']
        span = min(ticks(.3), max(ticks(1/fps), (end-start)//2))
        points = [(0, 0), (1, 100)]
        if animation == 'flicker':
            points = [(0,0),(.15,100),(.3,15),(.5,100),(.65,45),(1,100)]
        for fraction, value in points:
            self.key(clip, effect, 'opacity', start+round(span*fraction), value)
        if animation == 'slide':
            for f, pos in [(0,[x-40,y]), (1,[x,y])]:
                self.key(clip,effect,'position',start+round(span*f),pos)
        elif animation == 'bounce':
            for f, scale in [(0,75),(.65,108),(1,100)]:
                self.key(clip,effect,'scale',start+round(span*f),scale)
        elif animation == 'shake':
            for f, dx in [(0,-12),(.2,10),(.4,-7),(.65,4),(1,0)]:
                self.key(clip,effect,'position',start+round(span*f),[x+dx,y])
        elif animation in ('blur','mblur'):
            # One highlighted layer per graphic clip, so native blur won't affect the support.
            blur = 'gaussian_blur' if animation == 'blur' else 'directional_blur'
            self.command('effects.apply', clips=[clip], effect=blur)
            param = 'blurriness' if animation == 'blur' else 'length'
            self.key(clip,blur,param,start,22 if animation=='blur' else 35)
            self.key(clip,blur,param,start+span,0)

    def track(self, kind, name, sequence):
        # Reuse our empty lane; never overwrite earlier Titan graphics or user clips.
        existing = next((t for t in sequence[kind] if t['name']==name and not t['items'] and not t['locked']), None)
        if existing:
            return existing['id'], sequence[kind].index(existing)
        self.command('sequence.addTracks', video=1 if kind=='video' else 0, audio=1 if kind=='audio' else 0)
        updated = self.command('sequence.inspect')
        track = next(t for t in updated[kind] if t['id'] not in {x['id'] for x in sequence[kind]})
        self.command('timeline.setTrack', track=track['id'], name=name)
        return track['id'], updated[kind].index(track)

    def generate(self, blocks, mode='mixed', animation='slide', font='Arial', style='Bold',
                 size=80, color='#ffffff', accent='#00b7ff', y=.8, gain=.35, sounds=None,
                 x=.5,support_font=None,support_style=None):
        if mode not in ('common','dynamic','mixed') or animation not in ANIMATIONS:
            raise ValueError('Modo ou animação inválidos.')
        if not blocks:
            raise ValueError('Carregue uma legenda ou faça uma transcrição primeiro.')
        blocks = sorted(blocks, key=lambda b:b['start'])
        if any(b['start'] < 0 or b['end'] <= b['start'] for b in blocks):
            raise ValueError('Tempos de legenda inválidos.')
        if any(b['end'] > blocks[i+1]['start']+.001 for i,b in enumerate(blocks[:-1])):
            raise ValueError('Há legendas sobrepostas. Corrija os tempos antes de gerar.')
        sequence = self.command('sequence.inspect'); sequence_id = sequence['id']
        settings = sequence['settings']; fps = settings['frame_rate']['num']/settings['frame_rate']['den']
        # Round shared boundaries once. Independently rounding the start and
        # duration can extend one clip a frame into the next ("V4 is not free").
        frame_ticks=TICKS*settings['frame_rate']['den']/settings['frame_rate']['num']
        def snap(seconds):return round(round(float(seconds)*fps)*frame_ticks)
        boundaries=[(snap(block['start']),snap(block['end'])) for block in blocks]
        for index,(start,end) in enumerate(boundaries):
            if index+1<len(boundaries):end=min(end,boundaries[index+1][0])
            if end<=start:raise ValueError('Uma legenda tem duração inferior a um quadro. Ajuste seus tempos.')
            boundaries[index]=(start,end)
        w,h = settings['width'], settings['height']; size=float(size)*h/1080; base_y=float(y)*h
        _, support_track = self.track('video', 'Titan • Legendas', sequence)
        sequence = self.command('sequence.inspect')
        _, hero_track = self.track('video', 'Titan • Destaques', sequence)
        generated, sounds_created, last_dynamic, last_sound = [], [], -math.inf, -math.inf
        audio_track = None
        try:
            for n, block in enumerate(blocks):
                if self.command('sequence.inspect')['id'] != sequence_id:
                    raise ValueError('A sequência ativa mudou durante a geração.')
                self.progress('Criando legenda %d de %d…' % (n+1,len(blocks)))
                a,b = boundaries[n]; hero = highlight(block)
                dynamic = hero is not None and mode != 'common' and (mode=='dynamic' or n%3==2 and block['start']-last_dynamic>=3)
                clean=block['text'].replace('[','').replace(']','')
                if not dynamic:
                    clip = self.text(clean,a,b,support_track,[w*x,base_y],font,style,size,accent,w*.85)
                    generated.append(clip)
                    self.command('clip.rename',clip=clip,name='TitanFC[none/-1]@%.3f:%.3f %s'%(y,x,clean))
                    continue
                before,word,after,at = hero
                support_clip=None
                for text, line_y in ((before,base_y-size*1.1),(after,base_y+size*1.1)):
                    if text:
                        clip=self.text(text,a,b,support_track,[w*x,line_y],support_font or font,support_style or style,size*.7,color,w*.85,existing=support_clip)
                        if support_clip is None:
                            generated.append(clip);support_clip=clip
                        self.command('clip.rename',clip=clip,name='TitanFC[support/-1]@%.3f:%.3f %s'%(y,x,' '.join((before,after))))
                # Highlight starts at its own spoken timestamp, never at every word.
                at=max(a,min(snap(at),b-round(frame_ticks)))
                clip=self.text(word,at,b,hero_track,[w*x,base_y],font,style,size*1.2,accent,w*.85)
                generated.append(clip)
                self.command('clip.rename',clip=clip,name='TitanFC[%s/0]@%.3f:%.3f %s'%(animation,y,x,word))
                self.animate(clip,0,animation,at,b,fps);last_dynamic=block['start']
                effect=(sounds or {}).get(animation,SOUNDS[animation])
                if gain>0 and effect!='none' and at/TICKS-last_sound>=2:
                    if audio_track is None:
                        audio_track,_=self.track('audio','Titan • Sons',self.command('sequence.inspect'))
                    sound=self.sound(clip,effect,at,min(.3,(b-at)/TICKS),gain,audio_track)
                    sounds_created.append(sound);last_sound=at/TICKS
            return {'titles':len(generated),'sounds':len(sounds_created)}
        except Exception:
            # Undo only clips created by this operation, not earlier titles or dialogue.
            if self.command('sequence.inspect')['id']==sequence_id:
                self.clear(generated+sounds_created)
            raise

    def text(self,text,start,end,track,position,font,style,size,color,max_width,existing=None):
        # Wrap long lines using native paragraph text; its origin is the box corner.
        position=[position[0]-max_width/2, position[1]-size]
        params=dict(text=text,time=start,seconds=(end-start)/TICKS,
                    track=track,position=position,box=[max_width,0],font=font,fontStyle=style,size=size)
        if existing is not None:params['clip']=existing
        else:params['newClip']=True
        result=self.command('graphics.newText',**params)
        clip=result['clip']
        try:
            self.command('graphics.set',clip=clip,layer=result['layer'],props={'align':'center','fill_color':color,
                         'shadow':True,'shadow_opacity':65,'shadow_blur':8,'shadow_distance':3})
        except Exception:
            if existing is None:self.clear([clip])
            raise
        return clip

    def sound(self,hero,effect,start,seconds,gain,track):
        if effect not in SOUNDS.values():
            raise ValueError('Efeito sonoro desconhecido.')
        directory=DATA/'sounds';directory.mkdir(parents=True,exist_ok=True)
        name='%s-%s.wav'%(effect,hashlib.sha256(('%s:%s:%.5f'%(effect,seconds,gain)).encode()).hexdigest()[:16])
        path=directory/name
        if not path.is_file():
            fit_sound(ROOT/'sfx'/('%s.wav'%effect),path,seconds,gain)
        imported=self.command('file.import',paths=[str(path)])
        if imported.get('errors') or not imported.get('items'):
            raise ValueError('Não foi possível importar o efeito sonoro: '+str(imported))
        result=self.command('timeline.place',item=imported['items'][0],track=track,time=start,
                            duration=ticks(seconds),video=False,audio=True)
        clip=result['clips'][0]
        try:
            self.command('clip.rename',clip=clip,name='TitanSFX[%s/%s]'%(hero,effect))
            self.command('clip.link',clips=[hero,clip])
        except Exception:
            self.clear([clip]);raise
        return clip

    def apply_sounds(self, mappings, gain):
        sequence=self.command('sequence.inspect');settings=sequence['settings']
        fps=settings['frame_rate']['num']/settings['frame_rate']['den']
        heroes=[]
        for track in sequence['video']:
            for clip in track['items']:
                match=TITLE.match(clip['name'])
                if match and match[1] in ANIMATIONS:
                    heroes.append((clip,match[1]))
        if not heroes:
            raise ValueError('Não há destaques animados do Titan nesta sequência.')
        owned=[c['clip'] for t in sequence['audio'] for c in t['items'] if re.match(r'^TitanSFX\[\d+/[a-z]+\]$',c['name'])]
        # Explicit IDs keep linked selection from deleting a linked title.
        track,_=self.track('audio','Titan • Sons',self.command('sequence.inspect'))
        last=-math.inf;created=[]
        try:
            for clip,animation in sorted(heroes,key=lambda x:x[0]['start']):
                effect=mappings.get(animation,SOUNDS[animation]);start=clip['start']
                if effect=='none' or gain<=0 or start/TICKS-last<2:
                    continue
                seconds=min(.3,clip['duration']/TICKS)
                created.append(self.sound(clip['clip'],effect,start,max(1/fps,seconds),gain,track))
                last=start/TICKS
        except Exception:
            if created:
                self.clear(created)
            raise
        if owned:
            self.clear(owned)
        current=self.command('sequence.inspect')
        for lane in current['audio']:
            if lane['name']=='Titan • Sons' and not lane['items']:
                self.command('sequence.deleteTrack',track=lane['id'])
        return len(created)

    def position(self,y,all_titles=False,x=.5):
        sequence=self.command('sequence.inspect');selected=set(sequence['selection']);count=0
        for track in sequence['video']:
            for clip in track['items']:
                match=TITLE.match(clip['name'])
                if match and (all_titles or clip['clip'] in selected):
                    # Overall Motion is static; layer entrance keyframes remain intact.
                    h=sequence['settings']['height'];w=sequence['settings']['width'];baseline=float(match[3]);baseline_x=float(match[4] or .5)
                    self.command('effects.setParam',clip=clip['clip'],effect='motion',param='position',
                                 value=[w/2+(float(x)-baseline_x)*w,h/2+(float(y)-baseline)*h])
                    count+=1
        if not count:
            raise ValueError('Selecione um título do Titan na timeline.')
        return count

    def style_titles(self,font,style,color,accent,support_font,support_style,all_titles=False):
        sequence=self.command('sequence.inspect');selected=set(sequence['selection']);count=0
        for track in sequence['video']:
            for clip in track['items']:
                match=TITLE.match(clip['name'])
                if not match or not (all_titles or clip['clip'] in selected):continue
                hero=match[1]!='support'
                for layer in self.command('graphics.list',clip=clip['clip'])['layers']:
                    self.command('graphics.set',clip=clip['clip'],layer=layer['layer'],props={
                        'font':font if hero else support_font,'font_style':style if hero else support_style,
                        'fill_color':accent if hero else color})
                count+=1
        if not count:raise ValueError('Selecione um título do Titan na timeline.')
        return count

def main():
    from titan_ui import App
    App().run()

if __name__=='__main__':
    if '--self-test' in sys.argv:
        path=Path(sys.argv[sys.argv.index('--self-test')+1])
        assets=[ROOT/'motor/whisper-cli.exe',ROOT/'icons/titan_word.png']+[ROOT/'sfx'/('%s.wav'%s) for s in SOUNDS.values()]
        if not all(p.is_file() for p in assets):raise RuntimeError('Missing bundled assets')
        from titan_ui import App
        app=App();app.root.withdraw();app.root.update();app.root.destroy()
        from installer import install,uninstall
        path.write_text(json.dumps({'version':VERSION,'assets':len(assets),'ui':True,'ok':True}),encoding='utf-8')
    elif '--install' in sys.argv or getattr(sys,'frozen',False) and Path(sys.executable).stem.startswith('Instalar'):
        from installer import main as install_main
        install_main()
    else:
        main()
