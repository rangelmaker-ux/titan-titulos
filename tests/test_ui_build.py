"""Build the real UI definition with a host simulator; no Resolve project writes."""
import ast
from collections import defaultdict
import importlib.util
import math
import os
from pathlib import Path
import random
import sys
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('locale_ui_test',ROOT/'src/titan_locale.py')
locale=importlib.util.module_from_spec(spec);spec.loader.exec_module(locale)

class Events:
    def __getattr__(self,name):
        event=Events();setattr(self,name,event);return event
class Widget:
    def __init__(self,props=None):
        self.Text='';self.ToolTip='';self.CurrentIndex=0;self.Value=0;self.Checked=False
        self.SliderPosition=0;self.SliderDown=False;self.items=[];self.ColumnWidth={};self.On=Events()
        for key,value in (props or {}).items():setattr(self,key,value)
    @property
    def CurrentText(self):return self.items[self.CurrentIndex] if self.items else ''
    def AddItem(self,text):self.items.append(text)
    def Clear(self):self.items=[]
    def NewItem(self):return SimpleNamespace(Text=defaultdict(str))
    def SetHeaderItem(self,item):self.header=item
    def AddTopLevelItem(self,item):pass
    def SelectedItems(self):return {}
class UI:
    def __init__(self):self.widgets={};self.all=[]
    def __getattr__(self,name):
        def make(props=None,*children):
            widget=Widget(props if isinstance(props,dict) else {})
            self.all.append(widget)
            if hasattr(widget,'ID'):self.widgets[widget.ID]=widget
            return widget
        return make
class Dispatcher:
    def __init__(self,ui):self.ui=ui
    def AddWindow(self,props,children):
        widget=Widget(props);widget.GetItems=lambda:self.ui.widgets;return widget

class Build(unittest.TestCase):
    def test_real_build_has_translated_controls_and_all_new_buttons(self):
        tree=ast.parse((ROOT/'src/Titan Titles Studio.py').read_text(encoding='utf-8'))
        for language,caption in (('pt-BR','LEGENDAS'),('en','CAPTIONS'),('es','SUBTÍTULOS')):
            with self.subTest(language=language):
                locale.configure(language);raw=UI()
                ns={'os':os,'sys':sys,'math':math,'random':random,'ui':locale.UIProxy(raw),'disp':Dispatcher(raw),
                    'fusion':SimpleNamespace(GetData=lambda key:None,SetData=lambda *args:None),
                    'UI_LANGUAGE':language,'_locale':locale,'tr':locale.translate,
                    '_tv_diag':SimpleNamespace(falha=lambda *args,**kw:None,evento=lambda *args,**kw:None,operacao=lambda *args,**kw:lambda fn:fn),
                    'ICON_URL':str(ROOT/'src/icons'),'SCRIPT_DIR':str(ROOT/'src')}
                # Safe static globals only; functions/classes are compiled but not
                # module bootstrap, native imports, file IO or startup expressions.
                for node in tree.body:
                    if isinstance(node,ast.Assign) and not any(isinstance(n,ast.Call) for n in ast.walk(node.value)):
                        try:exec(compile(ast.Module(body=[node],type_ignores=[]),'<constants>','exec'),ns)
                        except (NameError,TypeError,KeyError,AttributeError):pass
                    elif isinstance(node,(ast.FunctionDef,ast.ClassDef)):
                        exec(compile(ast.Module(body=[node],type_ignores=[]),'<declarations>','exec'),ns)
                    elif isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='STYLE':
                        try:exec(compile(ast.Module(body=[node],type_ignores=[]),'<style>','exec'),ns)
                        except NameError:pass
                ns.update({'icon':lambda name:None,'get_timeline':lambda:(None,None),
                           'FONTS':[('Arial',('Arial','Regular')),('Arial Bold',('Arial','Bold'))],
                           'HERO_FONTS':[],'FONTS_SEC':[0,1],'FONT_MAIN_DEF':1,'FONT_SEC_DEF':0})
                instance=ns['App'].__new__(ns['App'])
                instance._busy=False;instance.anim=ns['Animator']();instance.layout=ns['Layouter'](instance.anim)
                instance.entries=[];instance.gen_layouts=['badge'];instance.gen_auto=True
                instance.build()
                self.assertEqual(raw.widgets['tab_0'].Text.strip(),caption)
                for name in ('pos_all','ui_language','about','gsfx','asfx'):
                    self.assertIn(name,raw.widgets)
                self.assertEqual(raw.widgets['ui_language'].CurrentIndex,locale.LANGUAGES.index(language))
                self.assertTrue(raw.widgets['gsfx'].Checked)
                self.assertTrue(raw.widgets['asfx'].Checked)
                self.assertEqual(instance.win.WindowTitle,'Titan Titles Studio v3.3.0')
        locale.configure('pt-BR')

if __name__=='__main__':unittest.main()
