#!/usr/bin/env python3
"""Generate inventory.ini from an approved IP range.
Usage: python3 gen_inventory.py 192.168.1.110 192.168.1.115
       python3 gen_inventory.py 192.168.1.110 192.168.1.115 --start-num 1 --out inventory.ini
"""
import argparse, ipaddress, sys
from pathlib import Path

MAX_HOSTS = 64   # safety cap so a typo can't target a whole subnet

p = argparse.ArgumentParser()
p.add_argument("start"); p.add_argument("end")
p.add_argument("--start-num", type=int, default=1, help="number for the first PC (default 1)")
p.add_argument("--out", default="inventory.ini")
a = p.parse_args()

s, e = ipaddress.ip_address(a.start), ipaddress.ip_address(a.end)
if e < s:
    sys.exit("End IP is lower than start IP.")
count = int(e) - int(s) + 1
if count > MAX_HOSTS:
    sys.exit(f"Range has {count} addresses; the safety cap is {MAX_HOSTS}.")

lines = ["[windows]"]
for i in range(count):
    ip = ipaddress.ip_address(int(s) + i)
    lines.append(f"pc{a.start_num + i:02d} ansible_host={ip}")

lines += ["", "[windows:vars]",
          "ansible_connection=winrm",
          "ansible_port=5985",
          "ansible_winrm_transport=ntlm",
          "ansible_user=AnsibleAdmin", ""]

Path(a.out).write_text("\n".join(lines))
print(f"Wrote {count} hosts to {a.out}:")
print("\n".join(lines[1:count + 1]))