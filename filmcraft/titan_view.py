"""Resolve-style three-step interface for the FilmCraft adapter."""
import tkinter as tk
from tkinter import ttk, font as tkfont
from titan_filmcraft import ROOT, VERSION, ANIMATIONS, SOUNDS

BG='#131316';CARD='#19191e';FG='#f0f2f7';MUTED='#90909c';ACCENT='#38bdf8'

LABELS={
 'pt':['LEGENDAS','TÍTULOS','ANIMAÇÕES','TRANSCRIÇÃO','IDIOMA DO ÁUDIO','MODO DE TRANSCRIÇÃO','Alta (recomendado)',
       'GERAR LEGENDAS','PRÉVIA','AJUSTES','FONTE E COR','Principal','Apoio','CONFIGURAÇÕES','Sons por animação…',
       'Editar texto e tempos…','Importar SRT','Conexão FilmCraft','Posição X','Posição Y','Tamanho','ENTRADA',
       'Efeitos sonoros','Aplicar fonte ao selecionado','Aplicar fonte a todos'],
 'en':['CAPTIONS','TITLES','ANIMATIONS','TRANSCRIPTION','AUDIO LANGUAGE','TRANSCRIPTION MODE','High (recommended)',
       'GENERATE CAPTIONS','PREVIEW','ADJUSTMENTS','FONT & COLOR','Primary','Support','SETTINGS','Sounds by animation…',
       'Edit text and timing…','Import SRT','FilmCraft connection','Position X','Position Y','Size','ENTRANCE',
       'Sound effects','Style selected title','Style all titles'],
 'es':['SUBTÍTULOS','TÍTULOS','ANIMACIONES','TRANSCRIPCIÓN','IDIOMA DEL AUDIO','MODO DE TRANSCRIPCIÓN','Alta (recomendada)',
       'GENERAR SUBTÍTULOS','VISTA PREVIA','AJUSTES','FUENTE Y COLOR','Principal','Apoyo','CONFIGURACIÓN','Sonidos por animación…',
       'Editar texto y tiempos…','Importar SRT','Conexión FilmCraft','Posición X','Posición Y','Tamaño','ENTRADA',
       'Efectos de sonido','Fuente del seleccionado','Fuente de todos']}

def build(app):
    for child in app.root.winfo_children():child.destroy()
    app.root.configure(bg=BG);app.root.title(app.tr('title')+' '+VERSION);app.buttons=[]
    labels=LABELS[app.lang];style=ttk.Style(app.root)
    style.configure('.',background=BG,foreground=FG,font=('Segoe UI',10))
    style.configure('TFrame',background=BG);style.configure('TLabel',background=BG,foreground=FG)
    style.configure('Muted.TLabel',foreground=MUTED)
    style.configure('TButton',background='#22242c',foreground=FG,padding=(10,6),borderwidth=1,
                    bordercolor='#35353d',lightcolor='#35353d',darkcolor='#35353d',relief='flat')
    style.map('TButton',background=[('active','#303745')])
    style.configure('Primary.TButton',background='#007dff',foreground='white',font=('Segoe UI',11,'bold'))
    style.configure('Nav.TButton',background='#111622',foreground=MUTED,padding=8,font=('Segoe UI',11,'bold'))
    style.configure('Active.Nav.TButton',background='#172554',foreground=ACCENT)
    style.configure('TCombobox',fieldbackground='#232329',foreground=FG,background='#232329',arrowcolor=FG,
                    bordercolor='#3a3a40',lightcolor='#3a3a40',darkcolor='#3a3a40',padding=5)
    style.map('TCombobox',fieldbackground=[('readonly','#232329')],foreground=[('readonly',FG)])
    style.configure('TEntry',fieldbackground='#232329',foreground=FG,bordercolor='#3a3a40',lightcolor='#3a3a40',darkcolor='#3a3a40')
    style.configure('Horizontal.TScale',background=BG,troughcolor='#26262d',bordercolor='#26262d',
                    lightcolor='#38bdf8',darkcolor='#38bdf8',sliderrelief='flat',sliderlength=16)
    style.configure('Horizontal.TProgressbar',troughcolor='#26262d',background='#38bdf8',bordercolor='#26262d',lightcolor='#38bdf8',darkcolor='#38bdf8')
    style.configure('TCheckbutton',background=BG,foreground=FG)
    outer=ttk.Frame(app.root,padding=20);outer.pack(fill='both',expand=True)
    header=ttk.Frame(outer);header.pack(fill='x',pady=(0,8))
    try:
        from PIL import Image,ImageTk
        image=Image.open(ROOT/'icons/titan_word.png').convert('RGBA').resize((185,38),Image.Resampling.LANCZOS)
        app.logo=ImageTk.PhotoImage(image);ttk.Label(header,image=app.logo).pack(side='left')
    except (OSError,ImportError):ttk.Label(header,text='TITAN TITLES',font=('Segoe UI',17,'bold')).pack(side='left')
    app.button(header,'about',app.about).pack(side='right')
    app.language=ttk.Combobox(header,values=['Português BR','English','Español'],state='readonly',width=14)
    app.language.current(['pt','en','es'].index(app.lang));app.language.pack(side='right',padx=8)
    app.language.bind('<<ComboboxSelected>>',app.change_language)
    connection=ttk.Frame(outer);connection.pack(fill='x',pady=(0,10))
    app.button(connection,'launch',app.launch).pack(side='left')
    app.button(connection,'connect',lambda:app.work(app.connect)).pack(side='left',padx=6)
    ttk.Label(connection,text='FilmCraft • '+VERSION,style='Muted.TLabel').pack(side='right')
    tk.Frame(outer,height=2,bg=ACCENT).pack(fill='x',pady=(0,10))
    nav=ttk.Frame(outer);nav.pack(fill='x')
    content=ttk.Frame(outer);content.pack(fill='both',expand=True,pady=(14,0))
    content.rowconfigure(0,weight=1);content.columnconfigure(0,weight=1)
    app.pages=[ttk.Frame(content) for _ in range(3)];app.nav_buttons=[]
    for page in app.pages:page.grid(row=0,column=0,sticky='nsew')
    def select(index):
        app.pages[index].tkraise();app.active_page=index
        for i,b in enumerate(app.nav_buttons):b.configure(style='Active.Nav.TButton' if i==index else 'Nav.TButton')
    for i,label in enumerate(labels[:3]):
        nav.columnconfigure(i,weight=1)
        b=ttk.Button(nav,text='%d  %s'%(i+1,label),style='Nav.TButton',command=lambda i=i:select(i))
        b.grid(row=0,column=i,sticky='ew',padx=(0,6));app.nav_buttons.append(b)
    def section(parent,label):
        row=ttk.Frame(parent);row.pack(fill='x',pady=(6,5))
        tk.Frame(row,width=3,height=14,bg=ACCENT).pack(side='left',padx=(0,8))
        ttk.Label(row,text=label,font=('Segoe UI',10,'bold')).pack(side='left')
    def slider(parent,label,var,low,high):
        row=ttk.Frame(parent);row.pack(fill='x',pady=5)
        ttk.Label(row,text=label,width=11).pack(side='left')
        ttk.Scale(row,from_=low,to=high,variable=var,command=lambda _:preview()).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Entry(row,textvariable=var,width=7).pack(side='right')
    app.font_var=tk.StringVar(value=app.settings.get('font','Arial'))
    app.style_var=tk.StringVar(value=app.settings.get('style','Bold'))
    app.support_font_var=tk.StringVar(value=app.settings.get('support_font',app.font_var.get()))
    app.support_style_var=tk.StringVar(value=app.settings.get('support_style',app.style_var.get()))
    app.size=tk.DoubleVar(value=float(app.settings.get('size',80)))
    app.y=tk.DoubleVar(value=float(app.settings.get('position',80)))
    app.x=tk.DoubleVar(value=float(app.settings.get('position_x',50)))
    app.gain=tk.DoubleVar(value=float(app.settings.get('gain',35)))
    app.color=app.settings.get('color','#ffffff');app.accent=app.settings.get('accent','#00b7ff')
    app.mapping={k:tk.StringVar(value=app.settings.get('sounds',{}).get(k,SOUNDS[k])) for k in ANIMATIONS}
    app.sounds_on=tk.BooleanVar(value=app.settings.get('sounds_on',True))
    captions,titles,animations=app.pages
    section(captions,labels[3])
    transcription=ttk.Frame(captions);transcription.pack(fill='x')
    for col in range(3):transcription.columnconfigure(col,weight=1)
    ttk.Label(transcription,text=labels[4],style='Muted.TLabel').grid(row=0,column=0,sticky='w',pady=(0,4))
    ttk.Label(transcription,text=labels[5],style='Muted.TLabel').grid(row=0,column=1,sticky='w',pady=(0,4))
    app.speech=ttk.Combobox(transcription,values=['Português BR','English','Español'],state='readonly',width=19)
    app.speech.current(0);app.speech.grid(row=1,column=0,sticky='ew',padx=(0,10))
    ttk.Combobox(transcription,values=[labels[6]],state='readonly',width=20).grid(row=1,column=1,sticky='ew',padx=(0,10))
    transcription.winfo_children()[-1].current(0)
    b=ttk.Button(transcription,text=labels[7],style='Primary.TButton',command=app.generate_flow)
    b.grid(row=1,column=2,sticky='ew');app.buttons.append(b)
    ttk.Label(captions,text={'pt':'Deixe ativas apenas as faixas de voz. Silencie músicas e efeitos na timeline.',
                            'en':'Keep voice tracks active. Mute music and sound effects on the timeline.',
                            'es':'Deja activas las pistas de voz. Silencia música y efectos en la timeline.'}[app.lang],
              style='Muted.TLabel',wraplength=750).pack(anchor='w',pady=(8,0))
    app.progress=ttk.Progressbar(captions,mode='indeterminate');app.progress.pack(fill='x',pady=8)
    middle=ttk.Frame(captions);middle.pack(fill='x',pady=8)
    left=ttk.Frame(middle);left.pack(side='left',fill='both',expand=True)
    right=ttk.Frame(middle);right.pack(side='left',fill='both',expand=True,padx=(20,0))
    section(left,labels[8]);section(right,labels[9])
    app.preview=tk.Canvas(left,width=320,height=165,bg='#0e0e11',highlightbackground='#292932',highlightthickness=1)
    app.preview.pack(fill='x')
    slider(right,labels[20],app.size,20,160);slider(right,labels[18],app.x,5,95);slider(right,labels[19],app.y,20,90)
    section(captions,labels[10])
    def fontrow(parent,label,family,stylevar,which):
        row=ttk.Frame(parent);row.pack(fill='x',pady=3)
        ttk.Label(row,text=label,width=10).pack(side='left')
        fonts=ttk.Combobox(row,textvariable=family,values=sorted(set(tkfont.families())),width=25)
        fonts.pack(side='left',fill='x',expand=True,padx=6)
        styles=ttk.Combobox(row,textvariable=stylevar,values=['Regular','Bold','Italic','Bold Italic'],width=13)
        styles.pack(side='left',padx=6)
        palette=ttk.Frame(parent);palette.pack(fill='x',pady=(0,4))
        ttk.Label(palette,text='',width=10).pack(side='left')
        for color in ['#ffffff','#38bdf8','#2563eb','#00d9eb','#ffda19','#16df7c','#ad55ff','#ff3899','#ff4444']:
            def choose(color=color):
                setattr(app,which,color);app.refresh_preview()
            tk.Button(palette,bg=color,activebackground=color,width=2,relief='flat',borderwidth=0,
                      command=choose).pack(side='left',padx=3)
        ttk.Button(palette,text='HEX…',command=lambda:app.pick_color(which)).pack(side='left',padx=6)
        if label==labels[11]:app.font,app.font_style=fonts,styles
    fontrow(captions,labels[11],app.font_var,app.style_var,'accent')
    fontrow(captions,labels[12],app.support_font_var,app.support_style_var,'color')
    section(captions,labels[13])
    row=ttk.Frame(captions);row.pack(fill='x',pady=4)
    ttk.Label(row,text=app.tr('mode'),width=17).pack(side='left')
    app.mode=ttk.Combobox(row,values=[app.tr(k) for k in ('common','dynamic','mixed')],state='readonly',width=18)
    app.mode.current(app.settings.get('mode',2));app.mode.pack(side='left',padx=6)
    ttk.Checkbutton(row,text=labels[22],variable=app.sounds_on).pack(side='left',padx=10)
    row=ttk.Frame(captions);row.pack(fill='x',pady=10)
    app.button(row,'srt',app.import_srt).pack(side='left')
    ttk.Button(row,text=labels[15],command=app.edit_times).pack(side='left',padx=6)
    app.count_label=ttk.Label(row,text='',style='Muted.TLabel');app.count_label.pack(side='right')
    # Preserve the timing editor model without imposing a large table on the main view.
    app.text=tk.Text(captions);app.fill_text()
    section(titles,labels[10]);fontrow(titles,labels[11],app.font_var,app.style_var,'accent')
    fontrow(titles,labels[12],app.support_font_var,app.support_style_var,'color')
    row=ttk.Frame(titles);row.pack(fill='x',pady=10)
    for all_titles,label in [(False,labels[23]),(True,labels[24])]:
        b=ttk.Button(row,text=label,command=lambda all_titles=all_titles:app.apply_style(all_titles));b.pack(side='left',padx=4);app.buttons.append(b)
    section(titles,labels[9]);slider(titles,labels[18],app.x,5,95);slider(titles,labels[19],app.y,20,90)
    row=ttk.Frame(titles);row.pack(fill='x',pady=12)
    app.button(row,'selected',lambda:app.apply_position(False)).pack(side='left')
    app.button(row,'all',lambda:app.apply_position(True),True).pack(side='left',padx=8)
    section(animations,labels[21])
    app.animation=ttk.Combobox(animations,values=list(ANIMATIONS.values()),state='readonly')
    app.animation.current(app.settings.get('animation',0))
    tiles=ttk.Frame(animations);tiles.pack(fill='x',pady=12)
    app.animation_tiles=[]
    def animate_choice(i):
        app.animation.current(i)
        for n,b in enumerate(app.animation_tiles):b.configure(style='Active.Nav.TButton' if i==n else 'Nav.TButton')
        preview()
    for i,(key,name) in enumerate(ANIMATIONS.items()):
        tiles.columnconfigure(i%3,weight=1)
        b=ttk.Button(tiles,text=name,command=lambda i=i:animate_choice(i));b.grid(row=i//3,column=i%3,sticky='ew',padx=5,pady=6)
        app.animation_tiles.append(b)
    b=ttk.Button(animations,text=labels[14],command=lambda:sound_dialog(app,labels));b.pack(fill='x',pady=12);app.buttons.append(b)
    section(animations,labels[9]);slider(animations,app.tr('volume'),app.gain,0,100)
    ttk.Checkbutton(animations,text=labels[22],variable=app.sounds_on).pack(anchor='w',pady=8)
    ttk.Label(animations,text={'pt':'A animação escolhida será usada nos novos destaques. O som entra somente no destaque, com intervalo mínimo de 2 segundos.',
                              'en':'The chosen animation is used for new highlights. Sounds play only on highlights, at least 2 seconds apart.',
                              'es':'La animación se usa en nuevos destacados. Sonidos solo en destacados, separados por al menos 2 segundos.'}[app.lang],
              style='Muted.TLabel',wraplength=740).pack(anchor='w',pady=8)
    app.status=tk.StringVar(value=app.tr('ready'));ttk.Label(outer,textvariable=app.status,style='Muted.TLabel',wraplength=750).pack(fill='x',pady=(8,0))
    def preview():
        if not hasattr(app,'preview'):return
        canvas=app.preview;canvas.delete('all')
        width=max(320,canvas.winfo_width());height=165
        try:x=float(app.x.get())/100*width;y=min(150,float(app.y.get())/100*height)
        except (ValueError,tk.TclError):return
        canvas.create_line(width/2,0,width/2,height,fill='#202028',dash=(3,6))
        try:
            family=app.font_var.get();size=max(14,min(36,float(app.size.get())*.28))
            canvas.create_text(x,y-36,text=labels[12],fill=app.color,font=(app.support_font_var.get(),12),width=width-20)
            canvas.create_text(x,y,text=labels[11].upper(),fill=app.accent,font=(family,int(size),'bold'),width=width-20)
        except (tk.TclError,ValueError):pass
    app.refresh_preview=preview
    for variable in (app.font_var,app.support_font_var):variable.trace_add('write',lambda *_:preview())
    app.mode.bind('<<ComboboxSelected>>',lambda _:preview())
    animate_choice(app.animation.current());select(getattr(app,'active_page',0));app.root.after_idle(preview)

def sound_dialog(app,labels):
    window=tk.Toplevel(app.root);window.title(labels[14]);window.configure(bg=BG);window.geometry('540x470')
    card=ttk.Frame(window,padding=22);card.pack(fill='both',expand=True)
    for row,(key,label) in enumerate(ANIMATIONS.items()):
        ttk.Label(card,text=label).grid(row=row,column=0,sticky='w',pady=10,padx=(0,20))
        box=ttk.Combobox(card,textvariable=app.mapping[key],values=list(SOUNDS.values())+['none'],state='readonly',width=24)
        box.grid(row=row,column=1,sticky='ew')
    button=ttk.Button(card,text=app.tr('apply'),style='Primary.TButton',command=app.apply_sounds)
    button.grid(row=6,column=0,columnspan=2,sticky='ew',pady=16);app.buttons.append(button)
    def close():
        if button in app.buttons:app.buttons.remove(button)
        app.save();window.destroy()
    window.protocol('WM_DELETE_WINDOW',close)
