import importlib.util
import math
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import wave
from array import array

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('titan_sfx',ROOT/'src/titan_sfx.py')
sfx=importlib.util.module_from_spec(spec);spec.loader.exec_module(sfx)

class Clip:
    def __init__(self,start,end):self.start=start;self.end=end;self.markers={};self.name='';self.path=''
    def GetStart(self):return self.start
    def GetEnd(self):return self.end
    def GetMarkers(self):return self.markers
    def AddMarker(self,frame,color,name,note,duration,data):self.markers[frame]={'customData':data};return True
    def SetName(self,name):self.name=name;return True
    def GetClipProperty(self,key):return self.path if key=='File Path' else '24'

class Timeline:
    def __init__(self):self.tracks={1:[Clip(0,1000)]};self.names={1:'Voice'}
    def GetTrackCount(self,kind):return len(self.tracks)
    def GetItemListInTrack(self,kind,index):return self.tracks[index]
    def GetTrackName(self,kind,index):return self.names[index]
    def GetSetting(self,key):return '24'
    def AddTrack(self,*args):self.tracks[len(self.tracks)+1]=[];return True
    def SetTrackName(self,kind,index,name):self.names[index]=name;return True
    def DeleteClips(self,clips,ripple):
        for track in self.tracks.values():
            track[:]=[c for c in track if c not in clips]
        return True
    def DeleteTrack(self,kind,index):self.tracks.pop(index);return True

class Pool:
    def __init__(self,timeline):
        self.timeline=timeline;self.clips=[];self.folders=[];self.current=self;self.fail=False
    def GetRootFolder(self):return self
    def GetSubFolderList(self):return self.folders
    def GetClipList(self):return self.clips
    def GetName(self):return 'Titan Sound Effects'
    def AddSubFolder(self,*args):self.folders.append(self);return self
    def GetCurrentFolder(self):return self.current
    def SetCurrentFolder(self,folder):self.current=folder;return True
    def ImportMedia(self,paths):
        clip=Clip(0,0);clip.path=paths[0];self.clips.append(clip);return [clip]
    def AppendToTimeline(self,infos):
        if self.fail:return []
        info=infos[0];self.last=info
        clip=Clip(info['recordFrame'],info['recordFrame']+info['endFrame']+1)
        self.timeline.tracks[info['trackIndex']].append(clip);return [clip]

class Sounds(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT);self.addCleanup(self.temp.cleanup)
        self.cache=Path(self.temp.name)
    def test_events_use_animation_windows_and_glitch_priority(self):
        entry={'uid':'title','item':Clip(100,160)}
        events=sfx.plan_events([entry],lambda e:{'in':{'slide','flicker'},'out':{'blur'}},20)
        self.assertEqual([(e['start'],e['frames'],e['effect']) for e in events],[(100,21,'glitch'),(139,21,'airy')])
        self.assertEqual(events[1]['gain'],.5)
    def test_audio_exact_length_and_quieter_exit(self):
        paths=[]
        for gain in (1,.5):
            path=self.cache/(str(gain)+'.wav');sfx.fit_audio(ROOT/'src/sfx/whoosh.wav',path,21,29.97,gain);paths.append(path)
        amplitudes=[]
        for path in paths:
            with wave.open(str(path),'rb') as w:
                self.assertEqual(w.getnframes(),round(21*48000/29.97));self.assertEqual(w.getnchannels(),2)
                samples=array('h');samples.frombytes(w.readframes(w.getnframes()));amplitudes.append(max(abs(x) for x in samples))
        self.assertAlmostEqual(amplitudes[1]/amplitudes[0],.5,places=3)
    def fixture(self):
        timeline=Timeline();pool=Pool(timeline);project=SimpleNamespace(GetMediaPool=lambda:pool,GetUniqueId=lambda:'project')
        service=sfx.SoundEffects(ROOT/'src');service.cache=self.cache
        entry={'uid':'title','item':Clip(100,160)}
        return timeline,pool,project,service,entry
    def test_reapply_replaces_owned_sounds_preserves_voice(self):
        timeline,pool,project,service,entry=self.fixture();voice=timeline.tracks[1][0]
        state=lambda e:{'in':{'slide'},'out':{'blur'}}
        for _ in range(3):self.assertEqual(service.sync(project,timeline,[entry],state,20),2)
        allclips=[c for clips in timeline.tracks.values() for c in clips]
        self.assertEqual(len(allclips),3);self.assertIn(voice,allclips)
        self.assertEqual(len(pool.clips),2)
        self.assertEqual(pool.last['mediaType'],2)
        service.sync(project,timeline,[entry],state,20,False)
        self.assertEqual([c for clips in timeline.tracks.values() for c in clips],[voice])
    def test_insertion_failure_preserves_existing_audio(self):
        timeline,pool,project,service,entry=self.fixture();state=lambda e:{'in':{'slide'}}
        service.sync(project,timeline,[entry],state,20)
        old=[c for clips in timeline.tracks.values() for c in clips]
        pool.fail=True
        with self.assertRaises(RuntimeError):service.sync(project,timeline,[entry],state,21)
        self.assertEqual([c for clips in timeline.tracks.values() for c in clips],old)
    def test_transcription_restores_track_states_on_error(self):
        timeline,pool,project,service,entry=self.fixture()
        service.sync(project,timeline,[entry],lambda e:{'in':{'slide'}},20)
        flags={t:True for t in timeline.tracks}
        timeline.GetIsTrackEnabled=lambda kind,t:flags[t]
        def enable(kind,t,value):flags[t]=value;return True
        timeline.SetTrackEnable=enable
        def export():
            self.assertTrue(flags[1]);self.assertFalse(flags[2])
            raise OSError('export failed')
        with self.assertRaises(OSError):sfx.export_without_sfx(timeline,export)
        self.assertTrue(all(flags.values()))

if __name__=='__main__':unittest.main()
