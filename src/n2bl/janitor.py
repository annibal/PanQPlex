import os, json, math, time
from dataclasses import dataclass, asdict
from typing import List
from . import logger as log

SIDECAR_SUFFIX = ".ytmeta.json"
STATE_FILE = ".n2bl_state.json"  # cache of results/attempts

@dataclass
class Job:
    file: str
    title: str = ""
    description: str = ""
    tags: List[str] = None
    categoryId: str = "22"
    privacy: str = "private"
    thumbnail: str = ""
    state: str = "pending"   # pending|uploading|done|failed
    yt_id: str = ""
    attempts: int = 0
    last_msg: str = ""

    def meta_path(self):
        return self.file + SIDECAR_SUFFIX

    def to_row(self):
        size_mb = round(os.path.getsize(self.file)/1024/1024, 1) if os.path.exists(self.file) else "-"
        return [self.file, size_mb, self.state, (self.title or os.path.basename(self.file)), self.privacy]

def _default_title(path):
    base = os.path.basename(path)
    name, _ = os.path.splitext(base)
    return name

def _load_sidecar(path):
    if os.path.exists(path + SIDECAR_SUFFIX):
        with open(path + SIDECAR_SUFFIX, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_sidecar(job: Job):
    data = asdict(job).copy()
    # sidecar should only carry metadata, not volatile fields
    for k in ("state","yt_id","attempts","last_msg"):
        data.pop(k, None)
    with open(job.meta_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def scan_dir(dirpath, exts=None) -> List[Job]:
    exts = set([e.lower() for e in (exts or [".mp4",".mov",".mkv",".avi"])])
    jobs = []
    for name in os.listdir(dirpath):
        p = os.path.join(dirpath, name)
        if not os.path.isfile(p): continue
        if os.path.splitext(name)[1].lower() not in exts: continue
        side = _load_sidecar(p)
        job = Job(
            file=p,
            title=side.get("title", _default_title(p)),
            description=side.get("description", ""),
            tags=side.get("tags", []),
            categoryId=side.get("categoryId","22"),
            privacy=side.get("privacy","private"),
            thumbnail=side.get("thumbnail",""),
            state="pending",
        )
        jobs.append(job)
    # merge volatile state from STATE_FILE
    state = _load_state()
    for j in jobs:
        if j.file in state:
            s = state[j.file]
            j.state = s.get("state", j.state)
            j.yt_id = s.get("yt_id","")
            j.attempts = s.get("attempts",0)
            j.last_msg = s.get("last_msg","")
    return sorted(jobs, key=lambda x: x.file)

def load_job(path) -> Job:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    side = _load_sidecar(path)
    return Job(
        file=path,
        title=side.get("title", _default_title(path)),
        description=side.get("description",""),
        tags=side.get("tags",[]),
        categoryId=side.get("categoryId","22"),
        privacy=side.get("privacy","private"),
        thumbnail=side.get("thumbnail",""),
        state=_load_state().get(path,{}).get("state","pending"),
        yt_id=_load_state().get(path,{}).get("yt_id",""),
        attempts=_load_state().get(path,{}).get("attempts",0),
        last_msg=_load_state().get(path,{}).get("last_msg",""),
    )

def save_job(job: Job):
    _save_sidecar(job)
    # persist volatile bits too
    st = _load_state()
    st[job.file] = {"state": job.state, "yt_id": job.yt_id, "attempts": job.attempts, "last_msg": job.last_msg}
    _save_state(st)

def mark(job: Job, **kv):
    for k,v in kv.items():
        setattr(job, k, v)
    save_job(job)

def _load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_state(state):
    with open(STATE_FILE,"w",encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def status_rows(include_done=False):
    rows = []
    st = _load_state()
    for file, s in st.items():
        if not include_done and s.get("state") == "done":
            continue
        rows.append([
            os.path.basename(file),
            s.get("state","-"),
            s.get("yt_id",""),
            _load_sidecar(file).get("title", _default_title(file)),
            s.get("last_msg",""),
            s.get("attempts",0),
        ])
    return rows

# Pretty helpers for remote objects
def pretty_channel(c):
    sn = c["snippet"]
    stats = c.get("statistics", {})
    return f"{sn.get('title')} (subs={stats.get('subscriberCount','?')}, videos={stats.get('videoCount','?')})"

def pretty_video(v):
    sn = v["snippet"]
    return f"{sn['title']} — https://youtu.be/{v['contentDetails']['videoId']}"
