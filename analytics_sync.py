"""Sync YouTube Analytics into performance_memory.json for evidence-based script learning."""
import json, os
from datetime import date, timedelta, datetime, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
 "https://www.googleapis.com/auth/youtube.upload",
 "https://www.googleapis.com/auth/youtube.readonly",
 "https://www.googleapis.com/auth/yt-analytics.readonly",
]
MEMORY_PATH="performance_memory.json"
UPLOAD_LOG="output/uploaded_videos.json"
WINDOW_DAYS=int(os.getenv("ANALYTICS_WINDOW_DAYS","28"))

def get_credentials():
 refresh=os.getenv("YT_REFRESH_TOKEN")
 if not refresh and os.path.exists("token.json"):
  with open("token.json",encoding="utf-8") as f: refresh=json.load(f).get("refresh_token")
 if not refresh: raise SystemExit("YT_REFRESH_TOKEN is missing.")
 c=Credentials(None,refresh_token=refresh,token_uri="https://oauth2.googleapis.com/token",
  client_id=os.environ["YT_CLIENT_ID"],client_secret=os.environ["YT_CLIENT_SECRET"],scopes=SCOPES)
 c.refresh(Request()); return c

def read_json(path,default):
 try:
  with open(path,encoding="utf-8") as f: return json.load(f)
 except (OSError,json.JSONDecodeError): return default

def main():
 memory=read_json(MEMORY_PATH,{})
 uploads=read_json(UPLOAD_LOG,[])
 if not isinstance(memory,dict): memory={}
 if not isinstance(uploads,list) or not uploads:
  print("No upload history yet; nothing to sync."); return
 end=date.today()-timedelta(days=2) # Analytics data may lag.
 start=end-timedelta(days=WINDOW_DAYS-1)
 print(f"Analytics window: {start} -> {end}")
 api=build("youtubeAnalytics","v2",credentials=get_credentials())
 try:
  report=api.reports().query(ids="channel==MINE",startDate=start.isoformat(),endDate=end.isoformat(),
   dimensions="video",metrics="views,engagedViews,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained,subscribersLost",
   sort="-views",maxResults=200).execute()
 except HttpError as e:
  if e.resp.status in (401,403):
   raise SystemExit("Analytics access denied. Re-run auth.py and update YT_REFRESH_TOKEN with the authorized token (yt-analytics.readonly).")
  raise
 headers=[h["name"] for h in report.get("columnHeaders",[])]
 videos={}
 for row in report.get("rows",[]):
  d=dict(zip(headers,row)); vid=str(d.get("video",""))
  if not vid: continue
  videos[vid]={
   "views":int(d.get("views",0) or 0),"engaged_views":int(d.get("engagedViews",0) or 0),
   "average_view_duration_seconds":round(float(d.get("averageViewDuration",0) or 0),2),
   "average_view_percentage":round(float(d.get("averageViewPercentage",0) or 0),2),
   "likes":int(d.get("likes",0) or 0),"comments":int(d.get("comments",0) or 0),
   "shares":int(d.get("shares",0) or 0),"subscribers_gained":int(d.get("subscribersGained",0) or 0),
   "subscribers_lost":int(d.get("subscribersLost",0) or 0),"period_start":start.isoformat(),"period_end":end.isoformat(),
   "synced_at":datetime.now(timezone.utc).isoformat()}
 enriched=[]
 for item in uploads:
  if not isinstance(item,dict): continue
  copy=dict(item); vid=copy.get("video_id")
  if vid in videos: copy["analytics"]=videos[vid]
  enriched.append(copy)
 memory["analytics"]={"source":"YouTube Analytics API","window_days":WINDOW_DAYS,"period_start":start.isoformat(),
  "period_end":end.isoformat(),"last_sync":datetime.now(timezone.utc).isoformat(),"videos":videos}
 memory["video_performance"]=enriched
 memory["learning_note"]="Per-video metrics synced from YouTube Analytics. Compare videos at similar age; use retention and engaged views, not raw views alone."
 with open(MEMORY_PATH,"w",encoding="utf-8") as f: json.dump(memory,f,ensure_ascii=False,indent=2)
 print(f"Synced {len(videos)} videos into {MEMORY_PATH}")
 if not videos: print("No report rows returned (API delay or no views in selected period).")
if __name__=="__main__": main()
