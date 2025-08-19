import os, time, math
from dataclasses import dataclass
from typing import List
from tqdm import tqdm
from . import logger as log
from . import bridge, janitor

@dataclass
class SessionConfig:
    interval_min: int = 65           # throttle to be safe
    max_uploads: int = 0             # 0 = all
    default_privacy: str = "private"
    default_category: str = "22"
    dry_run: bool = False

def _render_queue(jobs: List[janitor.Job], current_idx:int):
    lines = []
    for i, j in enumerate(jobs):
        mark = "▶" if i == current_idx else " "
        lines.append(f"{mark} {os.path.basename(j.file)} [{j.state}] -> {j.title}")
    return "\n".join(lines)

def upload_once(job: janitor.Job, show_progress: bool):
    try:
        janitor.mark(job, state="uploading", attempts=job.attempts+1, last_msg="starting")
        resp = bridge.upload_video(
            job.file, title=(job.title or os.path.basename(job.file)),
            description=job.description, tags=job.tags, categoryId=job.categoryId,
            privacy=job.privacy, show_progress=show_progress
        )
        vid = resp["id"]
        janitor.mark(job, yt_id=vid, last_msg="uploaded")
        # optional thumbnail
        if job.thumbnail and os.path.exists(job.thumbnail):
            try:
                bridge.set_thumbnail(vid, job.thumbnail)
                janitor.mark(job, last_msg="uploaded+thumb")
            except Exception as e:
                janitor.mark(job, last_msg=f"thumb fail: {e}")
        # ensure metadata is up to date (idempotent update)
        bridge.update_metadata(vid, title=job.title, description=job.description,
                               tags=job.tags, categoryId=job.categoryId, privacy=job.privacy)
        janitor.mark(job, state="done", last_msg="done")
        log.info(f"OK https://youtu.be/{vid}")
        return True
    except Exception as e:
        janitor.mark(job, state="failed", last_msg=str(e))
        log.error(f"FAIL {job.file}: {e}")
        return False

def run_session(jobs: List[janitor.Job], cfg: SessionConfig):
    # normalize metadata defaults
    for j in jobs:
        if not j.privacy: j.privacy = cfg.default_privacy
        if not j.categoryId: j.categoryId = cfg.default_category

    done = 0
    for idx, job in enumerate(jobs):
        os.system("clear" if os.name != "nt" else "cls")
        print("Queue:\n" + _render_queue(jobs, idx))
        if cfg.max_uploads and done >= cfg.max_uploads:
            log.info("Reached --max")
            break

        if job.state == "done":
            log.info(f"Skip done: {job.file}")
            continue

        if cfg.dry_run:
            log.info(f"[DRY] would upload: {job.file} -> {job.title} ({job.privacy})")
        else:
            ok = upload_once(job, show_progress=True)
            if not ok:
                # backoff a bit before next attempt/file to avoid rapid-fire failures
                time.sleep(15)
            else:
                done += 1

        # throttle between uploads regardless of success (safer)
        if idx < len(jobs)-1:
            mins = cfg.interval_min
            for s in range(mins*60, 0, -1):
                m, ss = divmod(s, 60)
                print(f"\rWait {m:02d}:{ss:02d} before next upload…  ", end="", flush=True)
                time.sleep(1)
            print()
