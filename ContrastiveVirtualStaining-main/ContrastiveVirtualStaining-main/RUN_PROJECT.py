import os, sys, subprocess

# Always run from the folder this file lives in — works no matter what VS Code sets as cwd
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON      = sys.executable          # uses whichever interpreter VS Code launched this with
TRAIN_PY    = os.path.join(PROJECT_DIR, "train.py")

env = os.environ.copy()
env["EXPERIMENT_LOCATION"] = os.path.join(PROJECT_DIR, "results")

cmd = [
    PYTHON, TRAIN_PY,
    "--dataset",         "KRT",
    "--featssize",       "512",
    "--seed",            "42",
    "--Folds",           "5",
    "--augment",         "False",
    "--optimizer",       "AdamW",
    "--sampling",        "default",
    "--env",             "local",
    "--balancedSampler", "over",
    "--featsExtractor",  "UNI",
]

print(f"[RUN_PROJECT] cwd      : {PROJECT_DIR}")
print(f"[RUN_PROJECT] python   : {PYTHON}")
print(f"[RUN_PROJECT] train.py : {TRAIN_PY}")
print(f"[RUN_PROJECT] EXPERIMENT_LOCATION: {env['EXPERIMENT_LOCATION']}")
print("-" * 60)
sys.stdout.flush()

result = subprocess.run(cmd, cwd=PROJECT_DIR, env=env)
sys.exit(result.returncode)
