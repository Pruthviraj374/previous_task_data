"""Emit every dataset into the task repo.

  task/environment/data/water_quality.csv        <- the one the agent sees
  task/tests/fixtures/<name>/water_quality.csv   <- graded (incl. a pristine
                                                    copy of the shipped one)

This script, gen.py, fixtures.py and autotune.py are authoring tools and are
NEVER committed to the task repo -- they encode the data-generating process, so
shipping them would hand the agent the answer.  They are committed to the
playbook repo instead, so the next session does not have to reconstruct them
(the predecessor generator was lost with its session's scratchpad).
"""
import os
import pickle
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen import generate
from fixtures import ALL

REPO = Path(os.environ.get(
    "DYNAMO_TASK_REPO",
    r"C:\Users\chara\Downloads\Handshake\dynamo-93acae6-scientific-computing-and-domain-science"))
SHIPPED = REPO / "task" / "environment" / "data" / "water_quality.csv"
FIXDIR = REPO / "task" / "tests" / "fixtures"

TUNED = pickle.load(open("tuned.pkl", "rb"))

if FIXDIR.exists():
    shutil.rmtree(FIXDIR)
FIXDIR.mkdir(parents=True)

for name, _ in ALL:
    df = generate(TUNED[name])
    d = FIXDIR / name
    d.mkdir()
    df.to_csv(d / "water_quality.csv", index=False, lineterminator="\n")
    if name == "shipped":
        SHIPPED.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(SHIPPED, index=False, lineterminator="\n")
    print(f"  {name}: {len(df)} rows -> {d}")

# the shipped CSV and its graded copy must be byte-identical
a = SHIPPED.read_bytes()
b = (FIXDIR / "shipped" / "water_quality.csv").read_bytes()
assert a == b, "shipped CSV and its tests/ copy diverged"
print(f"\nshipped copy is byte-identical ({len(a)} bytes)")

old = REPO / "task" / "tests" / "water_quality_reference.csv"
if old.exists():
    old.unlink()
    print("removed the predecessor's tests/water_quality_reference.csv")
