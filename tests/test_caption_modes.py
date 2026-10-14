import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[1]
TREE=ast.parse((ROOT/'src/Titan Titles Studio.py').read_text(encoding='utf-8'))
APP=next(n for n in TREE.body if isinstance(n,ast.ClassDef) and n.name=='App')

def functions(names,methods=False):
    body=APP.body if methods else TREE.body
    ns={'HERO_POS':{'center':None,'badge':'meio'}}
    nodes=[n for n in body if isinstance(n,ast.FunctionDef) and n.name in names]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<caption-mode>','exec'),ns)
    return ns

class CaptionModes(unittest.TestCase):
    def plans(self):
        return [{'layout':'badge','palavras':[{'t':word,'a':i*2000+j*400,'b':i*2000+j*400+350}
                 for j,word in enumerate(('o','projeto','cresce'))]} for i in range(10)]
    def test_common_dynamic_and_mixed_preserve_all_timed_words(self):
        ns=functions({'caption_mode_plan'})
        score=lambda words:10 if len(words[0])>=5 else -1
        plans=self.plans()
        for mode in ('common','dynamic','mixed'):
            result=ns['caption_mode_plan'](plans,mode,score)
            self.assertEqual([w for p in result for w in p['palavras']],[w for p in plans for w in p['palavras']])
            dynamic=[i for i,p in enumerate(result) if p['dynamic']]
            self.assertEqual(dynamic,[] if mode=='common' else list(range(10)) if mode=='dynamic' else [2,5,8])
    def test_filler_words_do_not_become_highlights(self):
        ns=functions({'caption_mode_plan'})
        plan={'layout':'center','palavras':[{'t':'e','a':0,'b':500}]}
        result=ns['caption_mode_plan']([plan],'dynamic',lambda words:-1)
        self.assertFalse(result[0]['dynamic'])
    def test_wrapping_never_loses_or_reorders_words(self):
        ns=functions({'common_caption_text'})
        words='Uma legenda comum permanece estável e legível.'.split()
        self.assertEqual(ns['common_caption_text'](words,15).split(),words)
    def test_plain_style_has_fixed_size_and_no_animation(self):
        ns=functions({'_style_common_caption'},methods=True)
        state={'in':{'slide'},'out':{'blur'},'mblur':True};fonts=[];colors=[];rendered=[]
        app=SimpleNamespace(anim=SimpleNamespace(state=lambda e:state,render=lambda e:rendered.append(dict(state))),
            items={'gcommon_size':SimpleNamespace(Value=75),'ghor':SimpleNamespace(Value=50),'galt':SimpleNamespace(Value=80)},
            layout=SimpleNamespace(_set_font=lambda e,f,t:fonts.append(f),_set_color=lambda e,c:colors.append(c),_set_shadow=lambda e:None),
            _fonte_hero=lambda:('Arial','Bold'),_fonte_small=lambda:('Arial','Regular'),
            _cor_hero=lambda:(1,1,1),_cor_small=lambda:(.8,.8,.8),tracking=lambda key:1,_anim_salvar=lambda *args:None)
        ns['_style_common_caption'](app,{'text':'Uma frase curta'},'common')
        self.assertEqual(state['base_size'],.075);self.assertEqual(state['base_center'],(.5,.8))
        self.assertFalse(state['in'] or state['out'] or state['mblur'])
        self.assertEqual(state['role'],'common');self.assertEqual(fonts[-1],('Arial','Bold'))
        ns['_style_common_caption'](app,{'text':'Uma frase maior com outro número de palavras'},'mixed')
        self.assertEqual(state['base_size'],.075);self.assertEqual(fonts[-1],('Arial','Regular'))
    def test_only_primary_word_is_animated(self):
        ns=functions({'_animate_caption_entry'},methods=True)
        for role in ('highlight','support','common'):
            state={'role':role}
            app=SimpleNamespace(anim=SimpleNamespace(state=lambda e:state,render=lambda e:None),_anim_salvar=lambda *args:None)
            ns['_animate_caption_entry'](app,{},0,30,True,True)
            self.assertEqual(state['in'],{'slide'} if role=='highlight' else set())
            self.assertEqual(state['out'],{'blur'} if role=='highlight' else set())
            self.assertEqual(state['duration'],9);self.assertEqual(state['distance'],.025)
            self.assertEqual(state['sfx_out'],'none')
    def test_legacy_primary_is_inferred_per_block_and_explicit_common_is_preserved(self):
        ns=functions({'_caption_roles'},methods=True)
        entries=[{'uid':str(i),'end':100 if i<3 else 200} for i in range(4)]
        states={'0':{'base_size':.04},'1':{'base_size':.09},'2':{'base_size':.05},'3':{'base_size':.10,'role':'common'}}
        app=SimpleNamespace(_anim_carregar=lambda e:states[e['uid']],_anim_salvar=lambda *args:None)
        ns['_caption_roles'](app,entries)
        self.assertEqual([states[str(i)]['role'] for i in range(4)],['support','highlight','support','common'])
    def test_animation_duration_uses_composition_fps_instead_of_bin_template_fps(self):
        ns=functions({'_animate_caption_entry'},methods=True)
        state={'role':'highlight'}
        entry={'comp':SimpleNamespace(GetPrefs=lambda key:24)}
        app=SimpleNamespace(anim=SimpleNamespace(state=lambda e:state,render=lambda e:None),_anim_salvar=lambda *args:None)
        ns['_animate_caption_entry'](app,entry,0,30,True,True)
        self.assertEqual(state['duration'],7);self.assertEqual(state['animation_fps'],24)

if __name__=='__main__':unittest.main()
