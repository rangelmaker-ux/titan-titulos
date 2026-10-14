"""Frame-aligned audio clips, owned markers, isolated lanes and stable media files."""
from array import array
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import wave

PREFIX='TitanSFX:'
CHOICES=('auto','whoosh','bounce','glitch','shake','airy','motionblur','none')
LABELS=('Automático','Slide — Whoosh','Bounce — Impacto','Flicker — Glitch','Shake — Cliques','Blur — Ar','Motion Blur — Névoa','Sem som')
EFFECTS={'flicker':'glitch','shake':'shake','bounce':'bounce','slide':'whoosh','blur':'airy','mblur':'motionblur'}
ANIMATION_SOUNDS=(('slide','Slide'),('bounce','Bounce'),('flicker','Flicker'),
                  ('shake','Shake'),('blur','Blur'),('mblur','Motion Blur'))

def values(collection):
    return list(collection.values()) if hasattr(collection,'values') else list(collection or [])

def effect_for(effects, motion_blur=False):
    for animation in ('flicker','shake','bounce','slide'):
        if animation in effects:return EFFECTS[animation]
    if motion_blur:return EFFECTS['mblur']
    if 'blur' in effects:return EFFECTS['blur']
    return None

def load_animation(entry):
    try:
        for marker in (entry['item'].GetMarkers() or {}).values():
            data=marker.get('customData','')
            if data.startswith('TitanAnim:'):
                state=json.loads(data[len('TitanAnim:'):])
                if isinstance(state,dict) and state.get('version')==1:return state
    except (AttributeError,TypeError,ValueError):pass
    return None

def save_animation(entry,state):
    item=entry['item']
    data={'version':1,'in':sorted(state.get('in',set())),'out':sorted(state.get('out',set())),
          'mblur':bool(state.get('mblur')),'duration':state.get('duration',20)}
    for side in ('in','out'):
        data['dir_'+side]=state.get('dir_'+side,'none')
        data['sfx_'+side]=state.get('sfx_'+side,'auto')
    payload='TitanAnim:'+json.dumps(data,separators=(',',':'))
    markers=item.GetMarkers() or {}
    existing=next((frame for frame,m in markers.items() if m.get('customData','').startswith('TitanAnim:')),None)
    if existing is not None:
        if markers[existing].get('customData')==payload:return
        item.UpdateMarkerCustomData(existing,payload)
    else:
        length=max(1,int(item.GetEnd())-int(item.GetStart()))
        frame=next((f for f in range(length) if f not in markers),None)
        if frame is None:return
        item.AddMarker(frame,'Blue','Titan Animation','',1,payload)

def plan_events(entries,states,duration,mappings=None):
    events=[]
    for entry in entries:
        item=entry['item']
        start,end=int(item.GetStart()),int(item.GetEnd())
        length=end-start
        if length<=0:continue
        state=states(entry)
        # Same bounded duration as Animator.render, including its end keyframe.
        span=min(length,max(2,min(int(state.get('duration',duration)),max(2,length//2)))+1)
        for side in ('in','out'):
            choice=state.get('sfx_'+side,'auto')
            active=bool(state.get(side,set()) or state.get('mblur'))
            animations=[key for key,_ in ANIMATION_SOUNDS if key in state.get(side,set()) or key=='mblur' and state.get('mblur')]
            effects=[]
            if choice=='auto':
                for animation in animations:
                    mapped=(mappings or {}).get(animation,'auto')
                    effect=EFFECTS[animation] if mapped=='auto' else mapped
                    if effect in EFFECTS.values():effects.append((animation,effect))
            elif choice in EFFECTS.values() and active:effects=[('manual',choice)]
            for animation,effect in effects:
                events.append({'uid':str(entry['uid']),'side':side,'effect':effect,
                    'animation':animation,
                    'start':start if side=='in' else end-span,'frames':span,
                    'gain':1.0 if side=='in' else 0.5})
    return events

def owned_uid(clip):
    try:
        for marker in (clip.GetMarkers() or {}).values():
            data=marker.get('customData','')
            if data.startswith(PREFIX):return str(json.loads(data[len(PREFIX):])['uid'])
    except (AttributeError,KeyError,TypeError,ValueError):pass
    return None

def fit_audio(source,destination,frames,fps,gain):
    with wave.open(str(source),'rb') as input:
        if input.getsampwidth()!=2 or input.getnchannels()!=2:raise ValueError('Sound must be stereo PCM16.')
        rate=input.getframerate(); samples=array('h');samples.frombytes(input.readframes(input.getnframes()))
    old_frames=len(samples)//2
    target_frames=max(1,int(round(int(frames)*rate/float(fps))))
    out=array('h')
    for i in range(target_frames):
        position=i*(old_frames-1)/max(1,target_frames-1)
        low=int(position);high=min(old_frames-1,low+1);fraction=position-low
        fade=min(1.0,i/max(1,int(rate*.006)),(target_frames-1-i)/max(1,int(rate*.012)))
        for ch in (0,1):
            value=(samples[low*2+ch]*(1-fraction)+samples[high*2+ch]*fraction)*gain*max(0,fade)
            out.append(int(max(-32767,min(32767,value))))
    with wave.open(str(destination),'wb') as output:
        output.setnchannels(2);output.setsampwidth(2);output.setframerate(rate);output.writeframes(out.tobytes())

def export_without_sfx(timeline,export):
    muted=[]
    try:
        for track in range(1,int(timeline.GetTrackCount('audio'))+1):
            clips=values(timeline.GetItemListInTrack('audio',track))
            is_titan_track=(str(timeline.GetTrackName('audio',track) or '').startswith('Titan SFX ')
                            or bool(clips and all(owned_uid(c) for c in clips)))
            if is_titan_track and clips and all(owned_uid(c) for c in clips):
                if timeline.GetIsTrackEnabled('audio',track):
                    _set_track_enabled(timeline,track,False)
                    muted.append(track)
        return export()
    finally:
        for track in muted:
            _set_track_enabled(timeline,track,True)

def _set_track_enabled(timeline,track,enabled):
    """Resolve's Lua/Python bridge may return nil on macOS after a successful call."""
    result=timeline.SetTrackEnable('audio',track,enabled)
    if result is True:return
    try:actual=timeline.GetIsTrackEnabled('audio',track)
    except Exception:actual=None
    if actual is bool(enabled):return
    if result is False or actual is not None:
        raise RuntimeError('Could not %s Titan sound track.' % ('enable' if enabled else 'mute'))

class SoundEffects:
    def __init__(self,resources):
        self.assets=Path(resources)/'sfx'
        # This directory survives reinstall/removal; projects reference these WAVs.
        self.cache=Path(resources).parent/'TitanTitlesStudio-audio'
        self.media={}
        self.folders={}
        self.fingerprints={}
    def _media_item(self,project,pool,path):
        project_id=str(project.GetUniqueId())
        key=(project_id,path)
        if key in self.media:return self.media[key]
        if project_id not in self.folders:
            root=pool.GetRootFolder()
            folder=next((f for f in values(root.GetSubFolderList()) if f.GetName()=='Titan Sound Effects'),None)
            if folder is None:folder=pool.AddSubFolder(root,'Titan Sound Effects')
            if not folder:raise RuntimeError('Could not create sound media folder.')
            self.folders[project_id]=folder
            for clip in values(folder.GetClipList()):
                filename=clip.GetClipProperty('File Path')
                if filename:self.media[(project_id,str(filename))]=clip
        if key in self.media:return self.media[key]
        previous=pool.GetCurrentFolder()
        try:
            if not pool.SetCurrentFolder(self.folders[project_id]):raise RuntimeError('Could not select sound folder.')
            imported=values(pool.ImportMedia([path]))
            if not imported:raise RuntimeError('Could not import sound effect.')
            self.media[key]=imported[0]
        finally:
            if previous:pool.SetCurrentFolder(previous)
        return self.media[key]
    def _audio_file(self,event,fps):
        source=self.assets/(event['effect']+'.wav')
        key=hashlib.sha256(source.read_bytes()+repr((event['frames'],fps,event['gain'])).encode()).hexdigest()
        self.cache.mkdir(parents=True,exist_ok=True)
        path=self.cache/(key+'.wav')
        if not path.exists():
            fd,temp=tempfile.mkstemp(suffix='.wav',prefix='titan-',dir=str(self.cache));os.close(fd)
            try:
                fit_audio(source,temp,event['frames'],fps,event['gain']);os.replace(temp,path)
            finally:
                if os.path.exists(temp):os.unlink(temp)
        return str(path)
    def _old(self,timeline,uids):
        clips=[]
        for track in range(1,int(timeline.GetTrackCount('audio'))+1):
            for clip in values(timeline.GetItemListInTrack('audio',track)):
                if owned_uid(clip) in uids:clips.append(clip)
        return clips
    def remove_titles(self,timeline,uids):
        old=self._old(timeline,set(map(str,uids)))
        if old:self._delete_clips(timeline,old,'Could not replace Titan sound clips.')
    @staticmethod
    def _delete_clips(timeline,clips,error):
        result=timeline.DeleteClips(clips,False)
        if result is True:return
        remaining=[c for track in range(1,int(timeline.GetTrackCount('audio'))+1)
                   for c in values(timeline.GetItemListInTrack('audio',track))]
        if any(clip in remaining for clip in clips):
            raise RuntimeError(error)
    @staticmethod
    def _add_marker(clip,event):
        metadata=PREFIX+json.dumps({'uid':event['uid'],'side':event['side']},separators=(',',':'))
        result=clip.AddMarker(0,'Blue','Titan SFX','',1,metadata)
        if result is True:return
        if owned_uid(clip)==str(event['uid']):return
        raise RuntimeError('Could not mark sound ownership.')
    def sync(self,project,timeline,entries,states,duration,enabled=True,mappings=None):
        uids={str(e['uid']) for e in entries}
        if not uids:return 0
        events=plan_events(entries,states,duration,mappings) if enabled else []
        fps=float(timeline.GetSetting('timelineFrameRate') or 24)
        timeline_id=str(timeline.GetUniqueId()) if hasattr(timeline,'GetUniqueId') else str(id(timeline))
        context=(str(project.GetUniqueId()),timeline_id)
        fingerprints={uid:tuple((e['side'],e['effect'],e['start'],e['frames'],e['gain'],fps)
                                for e in events if e['uid']==uid) for uid in uids}
        if all(self.fingerprints.get(context+(uid,))==value for uid,value in fingerprints.items()):
            return len(events)
        old=self._old(timeline,uids)
        pool=project.GetMediaPool()
        lanes={}
        for track in range(1,int(timeline.GetTrackCount('audio'))+1):
            if str(timeline.GetTrackName('audio',track) or '').startswith('Titan SFX '):
                lanes[track]=[(int(c.GetStart()),int(c.GetEnd())) for c in values(timeline.GetItemListInTrack('audio',track))]
        # Prepare every WAV and media item before changing the timeline.
        prepared=[]
        for event in events:
            path=self._audio_file(event,fps)
            prepared.append((event,self._media_item(project,pool,path)))
        made=[]
        new_tracks=[]
        try:
            for event,media in prepared:
                start,end=event['start'],event['start']+event['frames']
                track=next((t for t,ranges in sorted(lanes.items()) if all(end<=a or start>=b for a,b in ranges)),None)
                if track is None:
                    before=int(timeline.GetTrackCount('audio'))
                    try:timeline.AddTrack('audio','stereo')
                    except TypeError:timeline.AddTrack('audio')
                    track=int(timeline.GetTrackCount('audio'))
                    if track<=before:raise RuntimeError('O DaVinci Resolve não conseguiu criar uma faixa de áudio.')
                    new_tracks.append(track)
                    try:timeline.SetTrackName('audio',track,'Titan SFX '+str(track))
                    except Exception:pass
                    lanes[track]=[]
                try:source_fps=float(media.GetClipProperty('FPS') or fps)
                except (TypeError,ValueError):source_fps=fps
                if source_fps<=0:source_fps=fps
                source_frames=max(1,int(round(event['frames']*source_fps/fps)))
                result=values(pool.AppendToTimeline([{'mediaPoolItem':media,'mediaType':2,
                    'startFrame':0,'endFrame':source_frames-1,'recordFrame':start,'trackIndex':track}]))
                made.extend(result)
                if len(result)!=1:raise RuntimeError('Could not insert sound effect.')
                clip=result[0]
                if int(round(float(clip.GetStart())))!=start or int(round(float(clip.GetEnd())))!=end:
                    raise RuntimeError('Resolve inserted sound outside its animation window.')
                self._add_marker(clip,event)
                clip.SetName('Titan '+event['effect']+' '+event['side'])
                lanes[track].append((start,end))
            if old:self._delete_clips(timeline,old,'Could not replace old sounds.')
        except Exception:
            if made:timeline.DeleteClips(made,False)
            for track in reversed(new_tracks):
                if not values(timeline.GetItemListInTrack('audio',track)):
                    try:timeline.DeleteTrack('audio',track)
                    except AttributeError:pass
            raise
        for uid,value in fingerprints.items():self.fingerprints[context+(uid,)]=value
        return len(made)
