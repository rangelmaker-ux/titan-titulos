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
