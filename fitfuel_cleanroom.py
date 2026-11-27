"""Clean-room FitFuel short-form production engine.
New footage-first path. Does not import HyperFrames, visual_engine, visual_beats,
scene_presentation_director, avatar, or the legacy assembler.
"""
from __future__ import annotations
import argparse, json, os, re, subprocess
from pathlib import Path
from clips import search as search_stock, pick_file, download
from stock_sources import track_coverr_download

OUT=Path("output/cleanroom"); W,H,FPS=1080,1920,30
STOP={"the","a","an","and","or","but","to","of","in","on","for","with","is","are","was","were","be","this","that","your","you","it","as","by","from","how","why","what","when","can","will","do","does","not","than","then"}
SYNONYMS={
 "muscle":{"muscle","muscles","hypertrophy","biceps","triceps","bodybuilding","bodybuilder"},
 "protein":{"protein","amino","whey","chicken","eggs"},
 "sleep":{"sleep","sleeping","bed","rest","recovery"},
 "hydration":{"water","hydration","dehydration","fluid","electrolyte"},
 "heart":{"heart","cardio","pulse","heartbeat","blood","circulation"},
 "fat":{"fat","adipose","weight","calorie","deficit"},
 "exercise":{"exercise","training","workout","lifting","squat","deadlift","athlete"},
 "food":{"food","meal","nutrition","cooking","eating","diet","kitchen"},
 "hormone":{"hormone","insulin","cortisol","testosterone","estrogen","ghrelin","leptin"},
 "genetics":{"genetic","genetics","dna","gene","genes","hereditary","chromosome"}}
GENERIC={"fitness","sport","sports","person","people","healthy","active","lifestyle","strong","fit","exercise","workout","training","athlete"}
def words(value):
 return re.findall(r"[a-z0-9]+",str(value or "").lower())

def expand(tokens):
 expanded=set(tokens)
 for token in list(tokens):
  for group in SYNONYMS.values():
   if token in group:
    expanded.update(group)
 return expanded
def score_clip(hit,narration,keywords):
 metadata=" ".join(str(hit.get(k,"")) for k in ("tags","title","description"))
 meta=set(words(metadata)); raw=set(words(" ".join(keywords))); narrative=set(words(narration))
 specific=expand((raw|narrative)-GENERIC)
 exact=specific & meta
 meaningful=exact-GENERIC
 if not meta or not specific or not meaningful: return 0.0,[]
 coverage=len(meaningful)/max(1,min(5,len(specific-GENERIC)))
 query_match=len((raw-GENERIC)&meta)/max(1,len(raw-GENERIC))
 return round(min(1.0,coverage*0.72+query_match*0.28),4),sorted(meaningful)

def build_storyboard(script,audio):
 scenes=script.get("scenes") or []
 if not scenes or len(scenes)!=len(audio): raise ValueError("script/audio scene count mismatch or empty script")
 timeline=[]; cursor=0.0
 for i,(scene,voice) in enumerate(zip(scenes,audio),1):
  narration=str(scene.get("narration") or "").strip(); duration=float(voice.get("seconds") or 0)
  if not narration or duration<=0: raise ValueError(f"scene {i}: narration/duration invalid")
  keywords=[x.strip() for x in str(scene.get("keyword") or "").split("|") if x.strip()]
  if not keywords:
   tokens=words(narration); keywords=[" ".join(tokens[:4])] if tokens else []
  if not keywords: raise ValueError(f"scene {i}: no usable visual search intent")
  timeline.append({"scene":i,"start":round(cursor,3),"duration":round(duration,3),"end":round(cursor+duration,3),
   "narration":narration,"keywords":keywords,"role":"opening" if i==1 else ("closing" if i==len(scenes) else "evidence"),
   "visual_intent":" ".join(keywords[:2])})
  cursor+=duration
 return {"engine":"fitfuel-cleanroom","version":1,"format":"9:16","width":W,"height":H,"fps":FPS,
  "duration":round(cursor,3),"scene_count":len(timeline),"scenes":timeline}
def retrieve(board,used):
 results=[]
 for scene in board["scenes"]:
  candidates={}
  for query in scene["keywords"][:4]:
   for hit in search_stock(query):
    ident=str(hit.get("id") or "")
    if not ident or ident in used: continue
    info=pick_file(hit)
    if not info: continue
    url,width,height=info; relevance,matched=score_clip(hit,scene["narration"],scene["keywords"])
    if relevance<float(os.getenv("CLEANROOM_MIN_RELEVANCE","0.34")): continue
    rank=(relevance,bool(height>width),int(hit.get("duration") or 0))
    if ident not in candidates or rank>candidates[ident]["rank"]:
     candidates[ident]={"rank":rank,"id":ident,"url":url,"width":width,"height":height,
      "page":hit.get("pageURL"),"author":hit.get("user"),"tags":hit.get("tags",""),
      "source":ident.split(":",1)[0] if ":" in ident else "pixabay","matched_terms":matched,"relevance":relevance,"query":query}
  if not candidates: raise RuntimeError(f"Scene {scene['scene']}: no stock clip passed strict topic relevance; refusing unrelated footage for {scene['keywords']}")
  selected=max(candidates.values(),key=lambda x:x["rank"]); used.add(selected["id"])
  results.append({**{k:v for k,v in selected.items() if k!="rank"},"scene":scene["scene"],
   "start":scene["start"],"duration":scene["duration"],"narration":scene["narration"]})
 return results
def ass_time(seconds):
 cs=max(0,round(seconds*100)); h,cs=divmod(cs,360000); m,cs=divmod(cs,6000); s,cs=divmod(cs,100)
 return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
def write_captions(board,path):
 header=f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Editorial,Arial,76,&H00FFFFFF,&H0000D7FF,&H00101820,&H90081018,-1,0,0,0,100,100,0,0,1,4,2,2,90,90,300,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
 lines=[header]
 for scene in board["scenes"]:
  text=re.sub(r"[{}\\]","",scene["narration"]).upper(); chunks=[]; cur=""
  for word in text.split():
   if len((cur+" "+word).strip())>24 and cur: chunks.append(cur); cur=word
   else: cur=(cur+" "+word).strip()
  if cur: chunks.append(cur)
  weights=[max(1,len(x)) for x in chunks]; total=sum(weights); t=scene["start"]
  for chunk,weight in zip(chunks,weights):
   d=scene["duration"]*weight/total
   lines.append(f"Dialogue: 0,{ass_time(t)},{ass_time(t+d)},Editorial,,0,0,0,,{{\\fad(90,100)}}{chunk}")
   t+=d
 Path(path).write_text("\n".join(lines)+"\n",encoding="utf-8")
def run(cmd): subprocess.run(cmd,check=True)
def render(board,clips,audio):
 OUT.mkdir(parents=True,exist_ok=True); parts=[]
 for item in clips:
  i=item["scene"]; raw=OUT/f"source_{i}.mp4"; part=OUT/f"shot_{i}.mp4"; download(item["url"],str(raw))
  if item.get("source")=="coverr": track_coverr_download(item["id"].split(":",1)[1])
  dur=float(item["duration"])
  vf=f"scale=1200:2134:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.06:saturation=1.08:brightness=-0.015,zoompan=z='min(zoom+0.00035,1.045)':d=1:s=1080x1920:fps={FPS},fps={FPS},format=yuv420p"
  run(["ffmpeg","-y","-loglevel","error","-stream_loop","-1","-i",str(raw),"-t",str(dur),"-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p",str(part)])
  raw.unlink(missing_ok=True); parts.append(part)
 concat=OUT/"shots.txt"; concat.write_text("".join(f"file '{p.resolve()}'\n" for p in parts),encoding="utf-8")
 visual=OUT/"visual.mp4"; run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(visual)]); concat.unlink(missing_ok=True)
 captions=OUT/"captions.ass"; write_captions(board,captions); final=OUT/"final.mp4"
 cmd=["ffmpeg","-y","-loglevel","error","-i",str(visual)]
 for item in audio: cmd += ["-i",item["file"]]
 n=len(audio); filters=[]
 for i,item in enumerate(audio): filters.append(f"[{i+1}:a]aresample=44100,aformat=channel_layouts=stereo,apad,atrim=0:{float(item['seconds'])},asetpts=PTS-STARTPTS[a{i}]")
 filters.append("".join(f"[a{i}]" for i in range(n))+f"concat=n={n}:v=0:a=1[voice]")
 filters.append("[voice]alimiter=limit=0.95[aout]")
 cmd += ["-vf",f"ass={captions}","-filter_complex",";".join(filters),"-map","0:v","-map","[aout]","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-t",str(board["duration"]),"-movflags","+faststart",str(final)]
 run(cmd); return final
def main():
 parser=argparse.ArgumentParser(); parser.add_argument("--plan-only",action="store_true"); args=parser.parse_args()
 script=json.loads(Path("output/script.json").read_text(encoding="utf-8")); audio=json.loads(Path("output/audio_info.json").read_text(encoding="utf-8"))
 board=build_storyboard(script,audio); OUT.mkdir(parents=True,exist_ok=True)
 (OUT/"storyboard.json").write_text(json.dumps(board,indent=2),encoding="utf-8")
 if args.plan_only: print(f"Clean-room plan ready: {board['scene_count']} scenes / {board['duration']} sec"); return
 clips=retrieve(board,set()); (OUT/"footage_manifest.json").write_text(json.dumps(clips,indent=2),encoding="utf-8")
 final=render(board,clips,audio); report={"passed":final.exists() and final.stat().st_size>100000,"file":str(final),
  "scene_count":len(clips),"unique_stock_assets":len({x["id"] for x in clips}),
  "sources":sorted({x.get("source","unknown") for x in clips}),
  "all_scenes_have_distinct_assets":len({x["id"] for x in clips})==len(clips),
  "minimum_relevance":min((x.get("relevance",0) for x in clips),default=0),
  "visual_engine":"clean-room full-bleed editorial stock","publishing":"disabled"}
 (OUT/"review.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 if not report["passed"]: raise SystemExit("Clean-room render failed output gate")
 print(json.dumps(report,indent=2))
if __name__=="__main__": main()
