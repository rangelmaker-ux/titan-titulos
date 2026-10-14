import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'src'/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
locale=load('titan_locale')
sfx=load('titan_sfx')

class Features(unittest.TestCase):
    def tearDown(self):locale.configure('pt-BR')
    def test_locales_and_dynamic_messages(self):
        for language,caption,progress in (('pt-BR','LEGENDAS','Pronto: 12 blocos de legenda gerados.'),('en','CAPTIONS','Done: 12 caption blocks generated.'),('es','SUBTÍTULOS','Listo: 12 bloques de subtítulos generados.')):
            locale.configure(language)
            self.assertEqual(locale.translate('LEGENDAS'),caption)
            self.assertEqual(locale.translate('Pronto: 12 blocos de legenda gerados.'),progress)
            self.assertEqual(locale.translate('<span>LEGENDAS</span>'),'<span>'+caption+'</span>')
            self.assertEqual(locale.translate('Arial'),'Arial')
            self.assertEqual(locale.translate('RangelMaker_'),'RangelMaker_')
        self.assertEqual(locale.configure('unknown'),'pt-BR')
    def test_preview_and_font_content_not_translated(self):
        locale.configure('en')
        preview=SimpleNamespace(Text='')
        proxy=locale.WidgetProxy(preview,'preview');proxy.Text='<span>Texto</span>'
        self.assertEqual(preview.Text,'<span>Texto</span>')
        raw=SimpleNamespace(Text='');proxy=locale.WidgetProxy(raw,'status');proxy.Text='Sem timeline'
        self.assertEqual(raw.Text,'No timeline')
    def test_bulk_position_then_local_edit(self):
        source=ast.parse((ROOT/'src/Titan Titles Studio.py').read_text(encoding='utf-8'))
        app=next(n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='App')
        nodes=[n for n in app.body if isinstance(n,ast.FunctionDef) and n.name in ('on_pos','on_apply_position_all')]
        titles=[{'uid':str(i),'position':(.5,.5)} for i in range(3)]
        timeline=SimpleNamespace(GetCurrentTimecode=lambda:'01:00:00:00')
        def move(entry,dx,dy):entry['position']=(.5+dx,.5+dy);return True
        ns={'get_timeline':lambda:(object(),timeline),'find_textplus_under_playhead':lambda tl,all_titles=False:titles if all_titles else titles[:1], 'set_move':move}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<test>','exec'),ns)
        instance=SimpleNamespace(_busy=False,_syncing=False,last_tc='01:00:00:00',entries=titles[:1],items={'posx':SimpleNamespace(Value=80),'posy':SimpleNamespace(Value=20),'posx_lbl':SimpleNamespace(Text=''),'posy_lbl':SimpleNamespace(Text=''),'status':SimpleNamespace(Text=''),'pos_all_status':SimpleNamespace(Text='')},refresh=lambda **kw:None,selected=lambda:titles[:1],_ima_posicao=lambda sid:None,_try=lambda fn:fn(),update_preview=lambda:None)
        ns['on_apply_position_all'](instance)
        self.assertTrue(all(t['position']==(.8,.2) for t in titles))
        instance.items['posx'].Value=60;instance.items['posy'].Value=40
        ns['on_pos'](instance)
        self.assertEqual(titles[0]['position'],(.6,.4))
        self.assertEqual(titles[1]['position'],(.8,.2));self.assertEqual(titles[2]['position'],(.8,.2))
    def test_sound_mapping_apply_reaches_all_matching_timeline_titles(self):
        source=ast.parse((ROOT/'src/Titan Titles Studio.py').read_text(encoding='utf-8'))
        app=next(n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='App')
        node=next(n for n in app.body if isinstance(n,ast.FunctionDef) and n.name=='on_apply_sfx_map')
        titles=[{'uid':'flicker-a'},{'uid':'flicker-b'},{'uid':'slide'}]
        states={'flicker-a':{'in':{'flicker'},'out':set(),'sfx_in':'auto','sfx_out':'auto'},
                'flicker-b':{'in':set(),'out':{'flicker'},'sfx_in':'auto','sfx_out':'auto'},
                'slide':{'in':{'slide'},'out':set(),'sfx_in':'auto','sfx_out':'auto'}}
        applied=[];saved=[];sync=[]
        ns={'_sound_module':sfx,'fusion':SimpleNamespace(SetData=lambda *args:saved.append(args)),
            'get_timeline':lambda:(object(),object()),'find_textplus_under_playhead':lambda tl,all_titles=False:titles,
            'tr':locale.translate}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<sound-map>','exec'),ns)
        instance=SimpleNamespace(_busy=False,items={'gsfx':SimpleNamespace(Checked=False),'asfx':SimpleNamespace(Checked=False)},sfx_map_items={'sfx_map_flicker':SimpleNamespace(CurrentIndex=sfx.CHOICES.index('shake')),
            'sfx_map_status':SimpleNamespace(Text='')},sfx_map_window=object(),refresh=lambda **kw:None,
            _anim_carregar=lambda entry:states[entry['uid']],_anim_salvar=lambda entry,state:saved.append(entry['uid']),
            _sync_sounds=lambda entries:sync.extend(entries),sync_buttons=lambda:None,_gstatus=lambda text:None)
        ns['on_apply_sfx_map'](instance,'flicker')
        self.assertEqual(states['flicker-a']['sfx_in'],'auto')
        self.assertEqual(states['flicker-b']['sfx_out'],'auto')
        self.assertIn(('TitanTitlesStudio.sfxMap.flicker','shake'),saved)
        self.assertEqual(states['slide']['sfx_in'],'auto')
        self.assertEqual([entry['uid'] for entry in sync],['flicker-a','flicker-b'])
        self.assertTrue(instance.sfx_enabled)
        for key,_ in sfx.ANIMATION_SOUNDS:
            instance.sfx_map_items['sfx_map_'+key]=SimpleNamespace(CurrentIndex=0)
        sync.clear()
        ns['on_apply_sfx_map'](instance,'all')
        self.assertEqual([entry['uid'] for entry in sync],['flicker-a','flicker-b','slide'])
        for key,_ in sfx.ANIMATION_SOUNDS:self.assertIn(('TitanTitlesStudio.sfxMap.'+key,'auto'),saved)
        instance._sync_sounds=lambda entries:False
        ns['on_apply_sfx_map'](instance,'all')
        self.assertEqual(instance.sfx_map_items['sfx_map_status'].Text,'Não foi possível aplicar os sons. Veja os detalhes na janela principal.')
    def test_legacy_visible_animation_is_recovered_without_textplus_metadata(self):
        source=ast.parse((ROOT/'src/Titan Titles Studio.py').read_text(encoding='utf-8'))
        app=next(n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='App')
        nodes=[n for n in app.body if isinstance(n,ast.FunctionDef) and n.name in ('_anim_carregar','_anim_detectar')]
        def input(name,frame=0):
            if name=='Center':return (.5-.15*max(0,1-frame/20),.5)
            if name=='Size':return .08
            if name=='Opacity1':return frame%2 if frame<20 else 1
            if name=='MotionBlur':return 1
            return 0
        tool=SimpleNamespace(GetData=lambda key:None,GetInput=input)
        entry={'uid':'reopened','tool':tool,'comp':object(),'item':SimpleNamespace(GetMarkers=lambda:{})}
        state={'in':set(),'out':set(),'mblur':False};saved=[]
        ns={'ANIM_KEY':'TV_anim','_sound_module':sfx,'visible_range':lambda e:(0,59),
            'get_blur_tool':lambda *args:None,'get_at':lambda t,n,f:t.GetInput(n,f),'to_xy':lambda v:v}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<legacy-animation>','exec'),ns)
        instance=SimpleNamespace(anim=SimpleNamespace(dur=20,state=lambda e:state),
            _anim_salvar=lambda e,st:saved.append(dict(st)))
        instance._anim_detectar=lambda e,st:ns['_anim_detectar'](instance,e,st)
        recovered=ns['_anim_carregar'](instance,entry)
        self.assertEqual(recovered['in'],{'slide','flicker'});self.assertTrue(recovered['mblur'])
        self.assertTrue(saved)
    def test_about_links_and_clean_main_header(self):
        source=ast.parse((ROOT/'src/Titan Titles Studio.py').read_text(encoding='utf-8'))
        app=next(n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='App')
        build=next(n for n in app.body if isinstance(n,ast.FunctionDef) and n.name=='build')
        strings=[n.value for n in ast.walk(build) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
        self.assertFalse(any('rangelmaker_' in s.lower() for s in strings))
        about=next(n for n in app.body if isinstance(n,ast.FunctionDef) and n.name=='on_about')
        strings=[n.value for n in ast.walk(about) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
        for url in ('https://www.instagram.com/RangelMaker_/','https://www.instagram.com/oWilder.cine/','https://t.me/+y2SoJmZgRTwyOTI5'):
            self.assertIn(url,strings)
    def test_language_change_persists_and_restarts(self):
        source=ast.parse((ROOT/'src/Titan Titles Studio.py').read_text(encoding='utf-8'))
        app=next(n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='App')
        node=next(n for n in app.body if isinstance(n,ast.FunctionDef) and n.name=='on_ui_language')
        saved={};exits=[]
        ns={'UI_LANGUAGE':'pt-BR','_locale':locale,'fusion':SimpleNamespace(SetData=lambda k,v:saved.update({k:v})),'disp':SimpleNamespace(ExitLoop=lambda:exits.append(True))}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<test>','exec'),ns)
        app=SimpleNamespace(_syncing=False,_busy=False,items={'ui_language':SimpleNamespace(CurrentIndex=1)},_save_prefs=lambda:None,_close_about=lambda:None)
        ns['on_ui_language'](app)
        self.assertEqual(saved['TitanTitlesStudio.uiLanguage'],'en')
        self.assertTrue(app._restart_language);self.assertTrue(app._exit);self.assertEqual(exits,[True])

if __name__=='__main__':unittest.main()
