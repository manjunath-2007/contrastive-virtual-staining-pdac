import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold


def Splitter(bags_path, split, data_key, args, Folds):
    df = bags_path.copy()
    df.columns = ['path', 'label']

    skf = StratifiedKFold(n_splits=Folds, shuffle=True, random_state=42)
    labels = df['label'].values

    train_splits = []
    test_splits = []

    for train_idx, test_idx in skf.split(df, labels):
        train_splits.append(df.iloc[train_idx].reset_index(drop=True))
        test_splits.append(df.iloc[test_idx].reset_index(drop=True))

    return train_splits, test_splits
