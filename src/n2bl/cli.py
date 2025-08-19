import argparse, os, time
from . import bridge, janitor, engine
from . import logger as log

try:
    import googleapiclient.discovery
    import google_auth_oauthlib
    import google.auth
except ImportError as e:
    print("Missing dependencies. Run: pip install -r requirements.txt")
    raise

def main():
    parser = argparse.ArgumentParser(description="n2bl batch YouTube uploader")
    sub = parser.add_subparsers(dest="cmd")

    scan = sub.add_parser("scan", help="Scan PWD for uploadable videos")
    scan.add_argument("--ext", nargs="+", default=[".mp4",".mov",".mkv",".avi"])

    sub.add_parser("list-channels", help="List your channels")
    lu = sub.add_parser("list-uploads", help="List recent uploads")
    lu.add_argument("--max", type=int, default=20)

    edit = sub.add_parser("edit", help="Edit local sidecar metadata for a file")
    edit.add_argument("file"); edit.add_argument("--title"); edit.add_argument("--desc")
    edit.add_argument("--tags"); edit.add_argument("--category", default="22")
    edit.add_argument("--privacy", choices=["private","unlisted","public"], default=None)
    edit.add_argument("--thumb")

    stat = sub.add_parser("status", help="Show local queue + results")
    stat.add_argument("--all", action="store_true")

    start = sub.add_parser("start", help="Start throttled upload loop")
    start.add_argument("--interval-min", type=int, default=65)
    start.add_argument("--max", type=int, default=0)
    start.add_argument("--privacy", choices=["private","unlisted","public"], default="private")
    start.add_argument("--dry-run", action="store_true")
    start.add_argument("--select", nargs="*")
    start.add_argument("--category", default="22")

    up = sub.add_parser("upload", help="Upload a single file immediately")
    up.add_argument("file"); up.add_argument("--title"); up.add_argument("--desc")
    up.add_argument("--tags"); up.add_argument("--category", default="22")
    up.add_argument("--privacy", choices=["private","unlisted","public"], default="private")
    up.add_argument("--thumb")

    args = parser.parse_args()
    cmd = args.cmd

    if cmd == "scan":
        files = janitor.scan_dir(os.getcwd(), exts=args.ext)
        if not files: log.warn("No videos found."); return
        log.print_as_table([j.to_row() for j in files], ["FILE","SIZE_MB","STATE","TITLE","PRIVACY"]); return

    if cmd == "list-channels":
        for c in bridge.list_my_channels(): log.info(janitor.pretty_channel(c)); return

    if cmd == "list-uploads":
        for v in bridge.list_my_uploads(max_results=args.max): log.info(janitor.pretty_video(v)); return

    if cmd == "edit":
        job = janitor.load_job(args.file)
        if args.title: job.title = args.title
        if args.desc: job.description = args.desc
        if args.tags is not None: job.tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
        if args.category: job.categoryId = args.category
        if args.privacy: job.privacy = args.privacy
        if args.thumb: job.thumbnail = args.thumb
        janitor.save_job(job); log.info(f"Saved sidecar for {job.file}"); return

    if cmd == "status":
        rows = janitor.status_rows(include_done=args.all)
        if not rows: log.info("No queue entries."); return
        log.print_as_table(rows, ["FILE","STATE","YT_ID","TITLE","LAST_MSG","ATTEMPTS"]); return

    if cmd == "start":
        jobs = [janitor.load_job(f) for f in args.select] if args.select else janitor.scan_dir(os.getcwd())
        jobs = [j for j in jobs if j.state in ("pending","failed")]
        if not jobs: log.warn("No pending jobs."); return
        conf = engine.SessionConfig(args.interval_min, args.max, args.privacy, args.category, args.dry_run)
        engine.run_session(jobs, conf); return

    if cmd == "upload":
        job = janitor.load_job(args.file)
        if args.title: job.title = args.title
        if args.desc: job.description = args.desc
        if args.tags is not None: job.tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
        if args.category: job.categoryId = args.category
        if args.privacy: job.privacy = args.privacy
        janitor.save_job(job); engine.upload_once(job, show_progress=True); return

    parser.print_help()

if __name__ == "__main__":
    main()