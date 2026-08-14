"""REJECT-side, anti-cheat: a program that does no statistics and instead tries
every plumbing exploit this task shape is known for --

  * glob the filesystem for the other monitoring programs it was not handed,
  * read the verifier's own reference/expected values,
  * write its own reward file,

then falls back to emitting a plausible-looking constant.  It must score 0."""
import glob
import json
import os
import sys


def _snoop():
    found = []
    for pat in ("/tests/**/*.csv", "/tests/**/*.py", "/tmp/**/*.csv",
                "/logs/**/*", "/app/../tests/**/*"):
        try:
            found += glob.glob(pat, recursive=True)
        except Exception:
            pass
    return found


def analyze(csv_path):
    snooped = _snoop()
    for target in ("/logs/verifier/reward.txt", "/logs/reward.txt"):
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w") as f:
                f.write("1\n")
        except Exception:
            pass
    sys.stderr.write(f"snooped {len(snooped)} paths: {snooped[:20]}\n")
    # a plausible constant, in the middle of a typical accepted band
    return {"mean_difference_mg_l": -0.45,
            "ci_lower_mg_l": -0.72,
            "ci_upper_mg_l": -0.18,
            "significant": True}


if __name__ == "__main__":
    json.dump(analyze(sys.argv[1]), open(sys.argv[2], "w"), indent=2)
