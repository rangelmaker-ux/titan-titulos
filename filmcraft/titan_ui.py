"""Desktop UI. Native editor calls always run off the Tk event loop."""
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, font as tkfont
import webbrowser
from titan_filmcraft import (Titan, Bridge, VERSION, DATA, ROOT, PORT, ANIMATIONS,
                             SOUNDS, filmcraft_path, parse_srt, transcribe)

BG='#10151e'; PANEL='#192230'; BLUE='#009fff'; FG='#eef4ff'; MUTED='#9aaac0'
STRINGS={
 'pt':dict(title='Titan Titles Studio • FilmCraft',connect='Conectar',launch='Abrir FilmCraft com Titan',
          generate='GERAR TÍTULOS',transcribe='Transcrever sequência',srt='Importar SRT',
          common='Comum',dynamic='Dinâmica',mixed='Mista',mode='Tipo de legenda',animation='Animação dos destaques',
          font='Fonte',style='Estilo',size='Tamanho',position='Posição vertical (%)',color='Cor do texto',accent='Cor do destaque',
          sound='Efeitos sonoros',apply='Aplicar sons aos destaques existentes',volume='Volume dos sons (%)',
          selected='Aplicar posição ao selecionado',all='Aplicar posição a todos',about='About',ready='Pronto para conectar.',
          hint='Importe um SRT ou transcreva a sequência. Use [palavra] para escolher o destaque manualmente.',
          speech='Idioma da fala',timing='Tempos: início | fim | texto (segundos)',load='Carregar tempos editados'),
 'en':dict(title='Titan Titles Studio • FilmCraft',connect='Connect',launch='Open FilmCraft with Titan',
          generate='GENERATE TITLES',transcribe='Transcribe sequence',srt='Import SRT',
          common='Common',dynamic='Dynamic',mixed='Mixed',mode='Caption mode',animation='Highlight animation',
          font='Font',style='Style',size='Size',position='Vertical position (%)',color='Text color',accent='Highlight color',
          sound='Sound effects',apply='Apply sounds to existing highlights',volume='Sound volume (%)',
          selected='Position selected title',all='Position all titles',about='About',ready='Ready to connect.',
          hint='Import an SRT or transcribe the sequence. Use [word] to choose a highlight manually.',
          speech='Speech language',timing='Times: start | end | text (seconds)',load='Load edited times'),
 'es':dict(title='Titan Titles Studio • FilmCraft',connect='Conectar',launch='Abrir FilmCraft con Titan',
          generate='GENERAR TÍTULOS',transcribe='Transcribir secuencia',srt='Importar SRT',
          common='Común',dynamic='Dinámica',mixed='Mixta',mode='Tipo de subtítulo',animation='Animación del destacado',
          font='Fuente',style='Estilo',size='Tamaño',position='Posición vertical (%)',color='Color del texto',accent='Color destacado',
          sound='Efectos de sonido',apply='Aplicar sonidos a destacados existentes',volume='Volumen del sonido (%)',
          selected='Posición del seleccionado',all='Posición de todos',about='About',ready='Listo para conectar.',
          hint='Importa SRT o transcribe la secuencia. Usa [palabra] para elegir el destacado manualmente.',
          speech='Idioma del audio',timing='Tiempos: inicio | fin | texto (segundos)',load='Cargar tiempos editados')}

class App:
    def __init__(self):
        self.root=tk.Tk(); self.root.geometry('940x870'); self.root.minsize(880,760)
        self.root.configure(bg=BG)
        self.events=queue.Queue(); self.busy=False;self.blocks=[];self.sequence_id=None
        self.settings=self.read_settings();self.lang=self.settings.get('language','pt')
        if self.lang not in STRINGS:self.lang='pt'
        self.bridge=Bridge();self.titan=Titan(self.bridge,self.notify)
        style=ttk.Style(self.root);style.theme_use('clam')
        style.configure('.',background=PANEL,foreground=FG,font=('Segoe UI',10))
        style.configure('TFrame',background=BG);style.configure('Card.TFrame',background=PANEL)
        style.configure('TLabel',background=BG,foreground=FG)
        style.configure('Muted.TLabel',foreground=MUTED)
        style.configure('TButton',background='#26364b',foreground=FG,padding=(12,8),borderwidth=0)
        style.map('TButton',background=[('active','#37516f'),('disabled','#25303e')])
        style.configure('Primary.TButton',background=BLUE,foreground='white',font=('Segoe UI',11,'bold'))
        style.map('Primary.TButton',background=[('active','#0088dd')])
        style.configure('TCombobox',fieldbackground='#26364b',background='#26364b',foreground=FG,arrowcolor=FG)
        style.map('TCombobox',fieldbackground=[('readonly','#26364b')],foreground=[('readonly',FG)])
        style.configure('TEntry',fieldbackground='#26364b',foreground=FG)
        style.configure('TNotebook',background=BG,borderwidth=0)
        style.configure('TNotebook.Tab',padding=(20,10),background=PANEL)
        style.map('TNotebook.Tab',background=[('selected','#006fba')])
        self.build();self.root.after(100,self.poll)
        self.root.protocol('WM_DELETE_WINDOW',self.close)

    def read_settings(self):
        try:return json.loads((DATA/'settings.json').read_text(encoding='utf-8'))
        except (OSError,ValueError):return {}

    def save(self):
        if not hasattr(self,'font'):return
        data={'language':self.lang,'font':self.font.get(),'style':self.font_style.get(),
              'mode':self.mode.current(),'animation':self.animation.current(),'size':self.size.get(),
              'position':self.y.get(),'gain':self.gain.get(),'color':self.color,'accent':self.accent,
              'sounds':{k:v.get() for k,v in self.mapping.items()}}
        DATA.mkdir(parents=True,exist_ok=True)
        (DATA/'settings.json').write_text(json.dumps(data),encoding='utf-8');self.settings=data

    def tr(self,key):return STRINGS[self.lang][key]

    def button(self,parent,key,command,primary=False):
        b=ttk.Button(parent,text=self.tr(key),command=command,style='Primary.TButton' if primary else 'TButton')
        self.buttons.append(b);return b

    def build(self):
        for child in self.root.winfo_children():child.destroy()
        self.root.title(self.tr('title')+' '+VERSION);self.buttons=[]
        outer=ttk.Frame(self.root,padding=22);outer.pack(fill='both',expand=True)
        header=ttk.Frame(outer);header.pack(fill='x')
        try:
            from PIL import Image,ImageTk
            image=Image.open(ROOT/'icons/titan_word.png').convert('RGBA');image.thumbnail((270,75))
            self.logo=ImageTk.PhotoImage(image);ttk.Label(header,image=self.logo).pack(side='left')
        except (OSError,ImportError):ttk.Label(header,text='TITAN TITLES STUDIO',font=('Segoe UI',19,'bold')).pack(side='left')
        ttk.Label(header,text='FilmCraft  •  '+VERSION,style='Muted.TLabel').pack(side='left',padx=20)
        self.language=ttk.Combobox(header,values=['Português BR','English','Español'],state='readonly',width=15)
        self.language.current(['pt','en','es'].index(self.lang));self.language.pack(side='right')
        self.language.bind('<<ComboboxSelected>>',self.change_language)
        connection=ttk.Frame(outer);connection.pack(fill='x',pady=14)
        self.button(connection,'launch',self.launch).pack(side='left')
        self.button(connection,'connect',lambda:self.work(self.connect)).pack(side='left',padx=8)
        self.button(connection,'about',self.about).pack(side='right')
        tabs=ttk.Notebook(outer);tabs.pack(fill='both',expand=True)
        captions=ttk.Frame(tabs,padding=18);audio=ttk.Frame(tabs,padding=18)
        tabs.add(captions,text={'pt':'LEGENDAS E TÍTULOS','en':'CAPTIONS & TITLES','es':'SUBTÍTULOS Y TÍTULOS'}[self.lang])
        tabs.add(audio,text=self.tr('sound').upper())
        grid=ttk.Frame(captions);grid.pack(fill='x');grid.columnconfigure((0,1,2),weight=1)
        def field(label,column,row,widget):
            ttk.Label(grid,text=self.tr(label),style='Muted.TLabel').grid(column=column,row=row*2,sticky='w',pady=(10,4))
            widget.grid(column=column,row=row*2+1,sticky='ew',padx=(0,12))
            return widget
        self.mode=field('mode',0,0,ttk.Combobox(grid,values=[self.tr(x) for x in ('common','dynamic','mixed')],state='readonly'))
        self.mode.current(self.settings.get('mode',2))
        self.animation=field('animation',1,0,ttk.Combobox(grid,values=list(ANIMATIONS.values()),state='readonly'))
        self.animation.current(self.settings.get('animation',0))
        self.speech=field('speech',2,0,ttk.Combobox(grid,values=['Português BR','English','Español'],state='readonly'));self.speech.current(0)
        self.font=field('font',0,1,ttk.Combobox(grid,values=sorted(set(tkfont.families()))));self.font.set(self.settings.get('font','Arial'))
        self.font_style=field('style',1,1,ttk.Combobox(grid,values=['Regular','Bold','Italic','Bold Italic']));self.font_style.set(self.settings.get('style','Bold'))
        self.size=field('size',2,1,ttk.Spinbox(grid,from_=20,to=200));self.size.set(self.settings.get('size',80))
        self.y=field('position',0,2,ttk.Spinbox(grid,from_=20,to=90));self.y.set(self.settings.get('position',80))
        self.color=self.settings.get('color','#ffffff');self.accent=self.settings.get('accent','#00b7ff')
        field('color',1,2,ttk.Button(grid,text=self.color,command=lambda:self.pick_color('color')))
        field('accent',2,2,ttk.Button(grid,text=self.accent,command=lambda:self.pick_color('accent')))
        actions=ttk.Frame(captions);actions.pack(fill='x',pady=(18,8))
        self.button(actions,'srt',self.import_srt).pack(side='left')
        self.button(actions,'transcribe',self.start_transcription).pack(side='left',padx=8)
        ttk.Label(captions,text=self.tr('hint'),wraplength=830,style='Muted.TLabel').pack(anchor='w',pady=6)
        ttk.Label(captions,text=self.tr('timing'),style='Muted.TLabel').pack(anchor='w',pady=5)
        self.text=tk.Text(captions,height=9,bg='#0d131c',fg=FG,insertbackground=FG,relief='flat',padx=10,pady=10,wrap='word',font=('Consolas',10))
        self.text.pack(fill='both',expand=True)
        self.fill_text()
        bottom=ttk.Frame(captions);bottom.pack(fill='x',pady=10)
        self.button(bottom,'load',self.load_edited).pack(side='left')
        self.button(bottom,'generate',self.generate,True).pack(side='right')
        positions=ttk.Frame(captions);positions.pack(fill='x')
        self.button(positions,'selected',lambda:self.apply_position(False)).pack(side='left')
        self.button(positions,'all',lambda:self.apply_position(True)).pack(side='left',padx=8)
        self.mapping={}
        for row,(key,label) in enumerate(ANIMATIONS.items()):
            ttk.Label(audio,text=label,font=('Segoe UI',12,'bold')).grid(column=0,row=row,sticky='w',pady=12,padx=(0,30))
            box=ttk.Combobox(audio,values=list(SOUNDS.values())+['none'],state='readonly',width=30)
            box.set(self.settings.get('sounds',{}).get(key,SOUNDS[key]));box.grid(column=1,row=row,sticky='ew');self.mapping[key]=box
        ttk.Label(audio,text=self.tr('volume'),style='Muted.TLabel').grid(column=0,row=6,pady=15,sticky='w')
        self.gain=ttk.Spinbox(audio,from_=0,to=100,width=10);self.gain.set(self.settings.get('gain',35));self.gain.grid(column=1,row=6,sticky='w')
        self.button(audio,'apply',self.apply_sounds,True).grid(column=0,row=7,columnspan=2,sticky='ew',pady=15)
        self.status=tk.StringVar(value=self.tr('ready'));ttk.Label(outer,textvariable=self.status,wraplength=870,style='Muted.TLabel').pack(fill='x',pady=(14,0))
        self.progress=ttk.Progressbar(outer,mode='indeterminate');self.progress.pack(fill='x',pady=(8,0))

    def change_language(self,event):
        if self.busy:return
        new=['pt','en','es'][self.language.current()];self.save();self.lang=new;self.settings['language']=new
        (DATA/'settings.json').write_text(json.dumps(self.settings),encoding='utf-8');self.rebuild()

    def rebuild(self):
        draft=self.text.get('1.0','end-1c')
        self.build();self.text.delete('1.0','end');self.text.insert('1.0',draft)

    def pick_color(self,attribute):
        result=colorchooser.askcolor(getattr(self,attribute),parent=self.root)[1]
        if result:setattr(self,attribute,result);self.save();self.rebuild()

    def notify(self,message):self.events.put(('status',message))

    def work(self,function,success=None):
        if self.busy:return
        self.busy=True;self.progress.start(15)
        for button in self.buttons:button.state(['disabled'])
        self.language.state(['disabled'])
        def job():
            try:self.events.put(('done',(function(),success)))
            except Exception as error:self.events.put(('error',str(error)))
        threading.Thread(target=job,daemon=True).start()

    def poll(self):
        while not self.events.empty():
            kind,value=self.events.get()
            if kind=='status':self.status.set(value);continue
            self.busy=False;self.progress.stop()
            for button in self.buttons:button.state(['!disabled'])
            self.language.state(['!disabled','readonly'])
            if kind=='error':
                self.status.set(value);messagebox.showerror('Titan',value,parent=self.root)
            else:
                result,success=value
                if success:success(result)
                else:self.status.set(str(result))
        self.root.after(100,self.poll)

    def connect(self):
        sequence=self.bridge.execute('sequence.inspect');self.sequence_id=sequence['id']
        return 'FilmCraft conectado • '+sequence['name']

    def launch(self):
        def job():
            try:return self.connect()
            except (OSError,RuntimeError):pass
            # FilmCraft's currently open instance is never killed or replaced.
            process=subprocess.run(['tasklist','/FI','IMAGENAME eq filmcraft.exe','/FO','CSV','/NH'],capture_output=True,
                                   creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if b'filmcraft.exe' in process.stdout.lower():
                raise RuntimeError('Salve e feche o FilmCraft aberto. Depois clique em Abrir FilmCraft com Titan. Isso habilita a conexão local.')
            subprocess.Popen([str(filmcraft_path()),'--control',str(PORT)])
            for _ in range(60):
                time.sleep(.5)
                try:return self.connect()
                except (OSError,RuntimeError):pass
            raise RuntimeError('O FilmCraft abriu, mas não respondeu à conexão local.')
        self.work(job)

    def fill_text(self):
        self.text.delete('1.0','end')
        for block in self.blocks:self.text.insert('end','%.3f | %.3f | %s\n'%(block['start'],block['end'],block['text']))

    def import_srt(self):
        path=filedialog.askopenfilename(filetypes=[('SRT','*.srt')],parent=self.root)
        if not path:return
        try:
            sequence=self.bridge.execute('sequence.inspect');self.sequence_id=sequence['id']
            self.blocks=parse_srt(Path(path).read_text(encoding='utf-8-sig'));self.fill_text()
            self.status.set('%d legendas carregadas'%len(self.blocks))
        except Exception as error:messagebox.showerror('Titan',str(error),parent=self.root)

    def load_edited(self):
        try:
            lines=self.text.get('1.0','end').strip().splitlines();blocks=[]
            for line in lines:
                if not line.strip():continue
                a,b,text=line.split('|',2);a=float(a.strip().replace(',','.'));b=float(b.strip().replace(',','.'))
                if a<0 or b<=a or not text.strip():raise ValueError('Tempos ou texto inválidos: '+line)
                original=next((x for x in self.blocks if x['start']==a and x['end']==b and x['text']==text.strip()),None)
                blocks.append(original or {'start':a,'end':b,'text':text.strip()})
            if not blocks:raise ValueError('Digite pelo menos uma legenda.')
            self.blocks=blocks;self.status.set('%d legendas prontas'%len(blocks));return True
        except Exception as error:messagebox.showerror('Titan',str(error),parent=self.root);return False

    def start_transcription(self):
        if not messagebox.askokcancel('Titan','Deixe ativas apenas as faixas de voz no FilmCraft. Música e efeitos também entram na transcrição.\n\nNa primeira vez, pode ser necessário baixar o modelo de 488 MB.',parent=self.root):return
        language=['pt','en','es'][self.speech.current()]
        def job():
            sequence=self.bridge.execute('sequence.inspect');self.sequence_id=sequence['id']
            return transcribe(self.bridge,language,self.notify)
        def loaded(blocks):self.blocks=blocks;self.fill_text();self.status.set('%d legendas transcritas'%len(blocks))
        self.work(job,loaded)

    def check_sequence(self):
        sequence=self.bridge.execute('sequence.inspect')
        if self.sequence_id is not None and sequence['id']!=self.sequence_id:
            raise ValueError('A sequência mudou. Importe ou transcreva novamente na sequência desejada.')
        self.sequence_id=sequence['id']

    def generate(self):
        if not self.load_edited():return
        try:
            self.save();size=float(self.size.get());y=float(self.y.get())/100;gain=float(self.gain.get())/100
            if not 20<=size<=200 or not .2<=y<=.9 or not 0<=gain<=1:raise ValueError('Confira tamanho, posição e volume.')
        except ValueError as e:messagebox.showerror('Titan',str(e),parent=self.root);return
        params=dict(mode=['common','dynamic','mixed'][self.mode.current()],animation=list(ANIMATIONS)[self.animation.current()],
                    font=self.font.get(),style=self.font_style.get(),size=size,y=y,gain=gain,
                    color=self.color,accent=self.accent,sounds={k:v.get() for k,v in self.mapping.items()})
        blocks=list(self.blocks)
        def job():self.check_sequence();return self.titan.generate(blocks,**params)
        self.work(job,lambda r:self.status.set('%d títulos • %d sons sincronizados'%(r['titles'],r['sounds'])))

    def apply_sounds(self):
        try:gain=float(self.gain.get())/100
        except ValueError:return
        if not 0<=gain<=1:return
        mappings={k:v.get() for k,v in self.mapping.items()};self.save()
        self.work(lambda:self.titan.apply_sounds(mappings,gain),lambda n:self.status.set('%d sons aplicados'%n))

    def apply_position(self,all_titles):
        try:y=float(self.y.get())/100
        except ValueError:return
        if not .2<=y<=.9:return
        self.work(lambda:self.titan.position(y,all_titles),lambda n:self.status.set('%d títulos ajustados'%n))

    def about(self):
        window=tk.Toplevel(self.root);window.title('About • Titan');window.configure(bg=BG);window.geometry('480x460')
        card=ttk.Frame(window,padding=24);card.pack(fill='both',expand=True)
        ttk.Label(card,text='TITAN TITLES STUDIO',font=('Segoe UI',18,'bold')).pack(anchor='w')
        ttk.Label(card,text='FilmCraft • '+VERSION,style='Muted.TLabel').pack(anchor='w',pady=8)
        ttk.Label(card,text='Criação e direitos: RangelMaker_',font=('Segoe UI',11)).pack(anchor='w',pady=10)
        for label,url in [('@RangelMaker_','https://www.instagram.com/rangelmaker_/'),('@oWilder.cine','https://www.instagram.com/owilder.cine/'),
                          ('Comunidade Telegram','https://t.me/+y2SoJmZgRTwyOTI5')]:
            ttk.Button(card,text=label,command=lambda url=url:webbrowser.open(url)).pack(fill='x',pady=4)
        ttk.Button(card,text='Buscar atualizações',command=self.check_updates).pack(fill='x',pady=4)
        ttk.Button(card,text='Licenças',command=lambda:os.startfile(str(ROOT/'licenses'))).pack(fill='x',pady=4)

    def check_updates(self):
        def check():
            import urllib.request
            request=urllib.request.Request('https://api.github.com/repos/rangelmaker-ux/titan-titulos/releases?per_page=100',
                                           headers={'User-Agent':'TitanFilmCraft/'+VERSION})
            with urllib.request.urlopen(request,timeout=30) as response:releases=json.load(response)
            releases=[r for r in releases if r['tag_name'].startswith('filmcraft-v') and not r['draft'] and not r['prerelease']]
            if not releases:raise ValueError('Nenhuma versão FilmCraft publicada ainda.')
            return max(releases,key=lambda r:tuple(int(n) for n in r['tag_name'][len('filmcraft-v'):].split('.')))
        def show(release):
            latest=release['tag_name'][len('filmcraft-v'):]
            if tuple(map(int,latest.split('.')))<=tuple(map(int,VERSION.split('.'))):
                self.status.set('Titan para FilmCraft está atualizado • '+VERSION);return
            if messagebox.askyesno('Titan','Nova versão '+latest+'. Abrir o download do instalador?',parent=self.root):
                asset=next((a for a in release['assets'] if a['name'].startswith('Instalar-Titan-FilmCraft-') and a['name'].endswith('.exe')),None)
                webbrowser.open(asset['browser_download_url'] if asset else release['html_url'])
        self.work(check,show)

    def close(self):
        if self.busy:
            messagebox.showinfo('Titan','Aguarde a operação terminar antes de fechar.',parent=self.root);return
        self.save();self.root.destroy()

    def run(self):self.root.mainloop()
