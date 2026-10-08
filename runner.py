#!/usr/bin/env python3
import argparse, getpass, json, os, re, subprocess, sys, uuid
from datetime import datetime, timezone
from pathlib import Path
import yaml

BASE = Path(__file__).resolve().parent
HIST = BASE / "history"
RECAP = re.compile(r"^(\S+)\s*:\s+ok=(\d+)\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)", re.M)
RESULT = re.compile(r'RESULT host=(\S+) version=([^\s"]+)')

def load_catalog():
    return yaml.safe_load((BASE / "catalog.yml").read_text())

def inventory_hosts():
    out = subprocess.run(["ansible-inventory", "-i", str(BASE / "inventory.ini"), "--list"],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)["windows"]["hosts"]

def deploy(args):
    catalog = load_catalog()
    if args.software not in catalog:
        sys.exit(f"'{args.software}' is not in the approved catalog: {', '.join(catalog)}")
    sw = {"id": args.software, **catalog[args.software]}
    allowed = inventory_hosts()
    targets = allowed if args.hosts == "all" else args.hosts.split(",")
    bad = [h for h in targets if h not in allowed]
    if bad:
        sys.exit(f"Unknown hosts: {bad}")

    job_id = uuid.uuid4().hex[:8]
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cmd = ["ansible-playbook", "-i", str(BASE / "inventory.ini"),
           str(BASE / "playbooks" / "install_msi.yml"),
           "--limit", ",".join(targets), "-e", json.dumps({"sw": sw})]
    env = {**os.environ, "ANSIBLE_NOCOLOR": "1", "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"}
    print(f"Job {job_id}: deploying {sw['name']} {sw['version']} to {', '.join(targets)} ...")
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=BASE)

    (HIST / "logs").mkdir(parents=True, exist_ok=True)
    (HIST / "logs" / f"{job_id}.log").write_text(proc.stdout + proc.stderr)

    versions = dict(RESULT.findall(proc.stdout))
    results = {}
    for host, ok, changed, unreach, failed in RECAP.findall(proc.stdout):
        status = "unreachable" if int(unreach) else "failed" if int(failed) else "success"
        results[host] = {"status": status, "version": versions.get(host),
                         "changed": int(changed) > 0}
    for h in targets:
        results.setdefault(h, {"status": "failed", "version": None, "changed": False})

    record = {"job_id": job_id, "started": started, "requested_by": getpass.getuser(),
              "software": args.software, "approved_version": sw["version"], "results": results}
    with open(HIST / "jobs.jsonl", "a") as f:
        f.write(json.dumps(record) + "\n")

    print(f"\n{'HOST':8} {'STATUS':12} {'VERSION':10} CHANGED")
    for h, r in results.items():
        print(f"{h:8} {r['status']:12} {str(r['version']):10} {r['changed']}")
    sys.exit(0 if all(r["status"] == "success" for r in results.values()) else 1)

def history(_):
    f = HIST / "jobs.jsonl"
    if not f.exists():
        return print("No jobs yet.")
    for line in f.read_text().splitlines():
        j = json.loads(line)
        ok = sum(r["status"] == "success" for r in j["results"].values())
        print(f"{j['started']}  {j['job_id']}  {j['software']:8} {ok}/{len(j['results'])} ok  by {j['requested_by']}")

def show_catalog(_):
    for k, v in load_catalog().items():
        print(f"{k:10} {v['name']} {v['version']}")

p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd", required=True)
d = sub.add_parser("deploy"); d.add_argument("software"); d.add_argument("--hosts", required=True)
d.set_defaults(fn=deploy)
sub.add_parser("history").set_defaults(fn=history)
sub.add_parser("catalog").set_defaults(fn=show_catalog)
a = p.parse_args(); a.fn(a)