"""Run against the actual FilmCraft CLI on an isolated temporary project."""
import json
import random
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import titan_filmcraft as fc

CLI=Path(os.environ.get('ProgramFiles','C:/Program Files'))/'FilmCraft/filmcraft-cli.exe'

class Headless:
    def __init__(self,path):
        self.path=path;self.serial=0
        self.process=subprocess.Popen([str(CLI),'mcp'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                                      text=True,encoding='utf-8')
        self.rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'Titan Test','version':'1'}})
    def rpc(self,method,params):
        self.serial+=1
        self.process.stdin.write(json.dumps({'jsonrpc':'2.0','id':self.serial,'method':method,'params':params},ensure_ascii=False)+'\n')
        self.process.stdin.flush();result=json.loads(self.process.stdout.readline())
        if 'error' in result:raise RuntimeError(str(result['error']))
        return result['result']
    def execute(self,command,**params):
        result=self.rpc('tools/call',{'name':'command_run','arguments':{'id':command,'params':params}})
        if result.get('isError'):raise RuntimeError(str(result))
        content=result.get('structuredContent')
        if content is None:content=json.loads(result['content'][0]['text'])
        return content
    def close(self):
        self.process.terminate();self.process.wait();self.process.stdin.close();self.process.stdout.close()

@unittest.skipUnless(CLI.is_file(),'FilmCraft CLI required')
class Native(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'test.fcproj'
        self.old_root,self.old_data=fc.ROOT,fc.DATA
        fc.ROOT=Path(__file__).parents[1]/'src';fc.DATA=Path(self.tmp.name)/'data'
        self.bridge=Headless(self.path);self.bridge.execute('file.newProject',name='Titan isolated test')
        self.bridge.execute('file.newSequence',name='test',fps=24,video=1,audio=1)
        self.titan=fc.Titan(self.bridge)
    def tearDown(self):
        self.bridge.close();fc.ROOT,fc.DATA=self.old_root,self.old_data;self.tmp.cleanup()
    def test_six_animations_sounds_reapply_and_position(self):
        blocks=[{'start':i*3,'end':i*3+2.5,'text':'Um [destaque] para todos'} for i in range(6)]
        for animation,block in zip(fc.ANIMATIONS,blocks):
            result=self.titan.generate([block],mode='dynamic',animation=animation)
            self.assertEqual(result,{'titles':2,'sounds':1})
        sequence=self.bridge.execute('sequence.inspect')
        heroes=[c for t in sequence['video'] for c in t['items'] if fc.TITLE.match(c['name'])[1] in fc.ANIMATIONS]
        sounds=[c for t in sequence['audio'] for c in t['items']]
        self.assertEqual(len(heroes),6);self.assertEqual(len(sounds),6)
        for hero,sound in zip(sorted(heroes,key=lambda c:c['start']),sorted(sounds,key=lambda c:c['start'])):
            self.assertEqual(hero['start'],sound['start']);self.assertEqual(hero['link'],sound['link'])
            self.assertLessEqual(sound['duration']/fc.TICKS,.35)
        # Both static support layers coexist, instead of one overwriting the other.
        supports=[c for t in sequence['video'] for c in t['items'] if fc.TITLE.match(c['name'])[1]=='support']
        self.assertEqual(len(supports),6)
        for support in supports:self.assertEqual(len(self.bridge.execute('graphics.list',clip=support['clip'])['layers']),2)
        self.assertEqual(self.titan.apply_sounds({k:'glitch' for k in fc.ANIMATIONS},.2),6)
        self.assertEqual(self.titan.apply_sounds({k:'glitch' for k in fc.ANIMATIONS},.2),6)
        sequence=self.bridge.execute('sequence.inspect')
        self.assertEqual(sum(len(t['items']) for t in sequence['audio']),6)
        self.assertEqual(sum(len(t['items']) for t in sequence['video']),12)
        self.assertEqual(len([t for t in sequence['audio'] if t['name']=='Titan • Sons']),1)
        self.assertTrue(self.bridge.execute('state.inspect')['linked_selection'])
        self.assertEqual(self.titan.position(.7,True),12)
        self.bridge.execute('timeline.select',clips=[heroes[0]['clip']],add=False,toggle=False)
        self.assertEqual(self.titan.position(.6),1)
        image=Path(self.tmp.name)/'frame.png'
        self.bridge.execute('file.saveAs',path=str(self.path))
        subprocess.run([str(CLI),'--project',str(self.path),'render','--seconds','1.3','--out',str(image)],check=True,capture_output=True)
        self.assertGreater(image.stat().st_size,1000)
    def test_common_and_mixed(self):
        blocks=[{'start':i*3,'end':i*3+2.5,'text':'Um [destaque] para todos'} for i in range(3)]
        self.assertEqual(self.titan.generate(blocks,mode='common'),{'titles':3,'sounds':0})
        self.assertEqual(self.titan.generate(blocks,mode='mixed'),{'titles':4,'sounds':1})
    def test_user_audio_survives_sound_replacement(self):
        imported=self.bridge.execute('file.import',paths=[str(fc.ROOT/'sfx/whoosh.wav')])
        user=self.bridge.execute('timeline.place',item=imported['items'][0],track='A1',seconds=0,video=False,audio=True)['clips'][0]
        self.titan.generate([{'start':1,'end':4,'text':'[Titan]'}],mode='dynamic')
        self.titan.apply_sounds({k:'none' for k in fc.ANIMATIONS},0)
        sequence=self.bridge.execute('sequence.inspect')
        self.assertEqual([c['clip'] for t in sequence['audio'] for c in t['items']],[user])
        self.assertEqual(sum(len(t['items']) for t in sequence['video']),1)

    def test_fractional_rate_sound_alignment(self):
        self.bridge.execute('file.newSequence',name='Fractional',fps=29.97,video=1,audio=1)
        self.titan.generate([{'start':.413,'end':3.127,'text':'antes [destaque] depois'}],mode='dynamic')
        sequence=self.bridge.execute('sequence.inspect')
        hero=next(c for t in sequence['video'] for c in t['items'] if fc.TITLE.match(c['name'])[1]=='slide')
        sound=next(c for t in sequence['audio'] for c in t['items'])
        self.assertEqual(hero['start'],sound['start'])

    def test_failure_removes_only_new_clips(self):
        self.titan.generate([{'start':0,'end':2,'text':'Original'}],mode='common')
        sequence=self.bridge.execute('sequence.inspect')
        original=[c['clip'] for t in sequence['video'] for c in t['items']]
        with self.assertRaises(ValueError):
            self.titan.generate([{'start':3,'end':6,'text':'[Falha]'}],mode='dynamic',sounds={'slide':'unknown'})
        sequence=self.bridge.execute('sequence.inspect')
        self.assertEqual([c['clip'] for t in sequence['video'] for c in t['items']],original)
        self.assertFalse(any(t['items'] for t in sequence['audio']))

    def test_adjacent_fractional_word_boundaries_and_repeated_generation(self):
        for rate in (24,29.97,60):
            self.bridge.execute('file.newSequence',name='Adjacent',fps=rate,video=3,audio=3)
            blocks=[{'start':.19,'end':2.85,'text':'Create beautiful titles.'},
                    {'start':2.85,'end':6.12,'text':'Highlight important words.'},
                    {'start':6.12,'end':9.23,'text':'Keep sound effects subtle.'}]
            for mode in ('common','dynamic','mixed'):
                for repeat in range(2):self.titan.generate(blocks,mode=mode,gain=0)
            for lane in self.bridge.execute('sequence.inspect')['video']:
                clips=sorted(lane['items'],key=lambda c:c['start'])
                for first,second in zip(clips,clips[1:]):self.assertLessEqual(first['end'],second['start'])

    def test_occupied_v4_regression(self):
        # This exact seed reproduces "V4 is not free here" on 1.0.0.
        self.bridge.execute('file.newSequence',name='V4 regression',fps=24,video=3,audio=3)
        rng=random.Random(15);cursor=.013;blocks=[]
        for i in range(70):
            end=cursor+rng.uniform(.2,1.3)
            blocks.append({'start':cursor,'end':end,'text':'teste de limites'});cursor=end
        self.assertEqual(self.titan.generate(blocks,mode='common',gain=0)['titles'],70)

    def test_separate_fonts_and_horizontal_position(self):
        self.titan.generate([{'start':0,'end':3,'text':'antes [destaque] depois'}],mode='dynamic',x=.4,
                            font='Arial',support_font='Courier New',gain=0)
        sequence=self.bridge.execute('sequence.inspect')
        clips=[c for t in sequence['video'] for c in t['items']]
        self.assertEqual(self.titan.position(.7,True,x=.6),2)
        self.assertEqual(self.titan.style_titles('Georgia','Bold','#ffffff','#38bdf8','Arial','Regular',True),2)
        for clip in clips:
            updated=next(c for t in self.bridge.execute('sequence.inspect')['video'] for c in t['items'] if c['clip']==clip['clip'])
            motion=next(e for e in updated['effects'] if e['effect']=='motion')
            self.assertIn('1344.0',motion['params']['position']['value'])
            hero=fc.TITLE.match(clip['name'])[1]=='slide'
            for effect in [e for e in updated['effects'] if e['effect']=='graphic_text']:
                self.assertIn('Georgia' if hero else 'Arial',effect['params']['font']['value'])
                if hero:self.assertGreater(effect['params']['opacity']['keyframes'],0)

class Planning(unittest.TestCase):
    def test_srt_preserves_text(self):
        blocks=fc.parse_srt('1\n00:00:01,000 --> 00:00:03,000\nOlá [mundo]!\n')
        self.assertEqual(blocks[0]['start'],1);self.assertEqual(fc.highlight(blocks[0])[1],'mundo!')
    def test_actual_word_time(self):
        words=[{'text':'um','start':0,'end':.2},{'text':'destaque','start':1.2,'end':1.8}]
        self.assertEqual(fc.highlight(fc.split_words(words)[1])[3],1.2)

if __name__=='__main__':unittest.main(verbosity=2)
