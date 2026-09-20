"""
generate_demo_data.py
Run this ONCE before train.py to create synthetic demo data.
"""
import torch
import pandas as pd
import numpy as np
import os

FEATS_SIZE = 512   # must match --featssize passed to train.py
NUM_PATIENTS = 40  # 20 positive, 20 negative
NUM_TILES = 200    # tiles per patient bag
DATA_DIR = os.path.join(os.path.dirname(__file__), 'demo_feats')
os.makedirs(DATA_DIR, exist_ok=True)

rows = []
np.random.seed(42)
for i in range(NUM_PATIENTS):
    label = i % 2          # alternating 0/1
    # positive bags have slightly higher mean to make the task learnable
    mean = 0.5 if label == 1 else 0.0
    feats = torch.tensor(
        np.random.randn(NUM_TILES, FEATS_SIZE).astype(np.float32) + mean
    )
    pt_path = os.path.join(DATA_DIR, f'patient_{i:03d}.pt')
    torch.save(feats, pt_path)
    rows.append({'path': pt_path, 'label': label})

df = pd.DataFrame(rows)
csv_path = os.path.join(os.path.dirname(__file__), 'Path.csv')
df.to_csv(csv_path, index=False, header=False)
print(f'Saved {len(df)} rows to {csv_path}')

# ── init.pth: a fresh DSMIL state-dict so train.py can load it ──────────────
import sys
sys.path.insert(0, os.path.dirname(__file__))
import dsmil as mil

i_clf = mil.FCLayer(in_size=FEATS_SIZE, out_size=1)
b_clf = mil.BClassifier(input_size=FEATS_SIZE, output_class=1, dropout_v=0.0, nonlinear=1)
net  = mil.MILNet(i_clf, b_clf)
init_path = os.path.join(os.path.dirname(__file__), 'init.pth')
torch.save(net.state_dict(), init_path)
print(f'Saved init checkpoint to {init_path}')
print('Demo data generation complete.')
