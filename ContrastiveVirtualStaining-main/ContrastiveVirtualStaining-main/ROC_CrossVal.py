import torch
torch.manual_seed(42)
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.autograd import Variable
import torchvision.transforms.functional as VF
from torchvision import transforms
from torch.utils.tensorboard import SummaryWriter
import sys, argparse, os, copy, itertools, glob, datetime,shutil
import pandas as pd
import numpy as np
import sklearn
from sklearn.utils import shuffle
from sklearn.metrics import roc_curve, roc_auc_score, precision_recall_fscore_support
from sklearn.datasets import load_svmlight_file
from collections import OrderedDict
from Train_Test_Splitter import Splitter
from datetime import datetime
import matplotlib
#matplotlib.use('TkAGG')
import matplotlib.pyplot as plt
import dsmil as mil

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def get_bag_feats(csv_file_df,dataset, num_classes):
    if dataset == 'TCGA-lung-default':
        feats_csv_path = 'datasets/tcga-dataset/tcga_lung_data_feats/' + csv_file_df.iloc[0].split('/')[1] + '.csv'
    else:
        feats_csv_path = csv_file_df.iloc[0]

    df=torch.load(feats_csv_path, weights_only=True)
    feats=df[torch.randperm(df.size()[0])]
    label = np.zeros(num_classes)
    if num_classes == 1:
        label[0] = csv_file_df.iloc[1]
    else:
        if int(csv_file_df.iloc[1]) <= (len(label) - 1):
            label[int(csv_file_df.iloc[1])] = 1

    return label, feats.unsqueeze(0)
def multi_label_roc(labels, predictions, num_classes, pos_label=1):
    fprs = []
    tprs = []
    thresholds = []
    thresholds_optimal = []
    aucs = []
    if len(predictions.shape)==1:
        predictions = predictions[:, None]
    for c in range(0, num_classes):
        label = labels[:, c]
        prediction = predictions[:, c]
        fpr, tpr, threshold = roc_curve(label, prediction, pos_label=1)
        fpr_optimal, tpr_optimal, threshold_optimal = optimal_thresh(fpr, tpr, threshold)
        try:
            c_auc = roc_auc_score(label, prediction)
        except ValueError:
            c_auc = 0.5
        aucs.append(c_auc)
        fprs.append(fpr)
        tprs.append(tpr)
        thresholds.append(threshold)
        thresholds_optimal.append(threshold_optimal)
    return aucs, thresholds, thresholds_optimal,fprs,tprs
def optimal_thresh(fpr, tpr, thresholds, p=0):
    """
    Finding optimal threshold for a given p
    used to predict class thresholds for the classification
    """
    loss = (fpr - tpr) - p * tpr / (fpr + tpr + 1)
    idx = np.argmin(loss, axis=0)
    return fpr[idx], tpr[idx], thresholds[idx]
def ROC_CrossVal(RunDir,Dataset,Folds,model,num_classes,feats_size,average,args=None):
    dataset=Dataset
    if 'HNF' in dataset:
        data_key='HNF'
    elif 'KRT' in dataset:
        data_key='KRT'
    else:
        data_key='KRT'

    num_classes=num_classes
    feats_size=feats_size
    bags_csv = os.path.join('Path.csv')
    bags_path = pd.read_csv(bags_csv)
    Data = Splitter(bags_path, 0.2, data_key, args, Folds)
    All_labels = []
    All_predictions = []
    All_bin_predictions=[]
    Tensor = torch.FloatTensor
    for fold in range(Folds):
        States=torch.load(os.path.join(RunDir,'Fold_'+str(fold),'Weights','checkpoint_best_loss.pth'), weights_only=True)
        model.load_state_dict(States)
        model.to(DEVICE)
        model.eval()
        Fold_labels = []
        Fold_predictions = []
        with torch.no_grad():
            test_df=Data[1][fold]
            print(len(test_df))
            for i in range(len(test_df)):
                label, feats = get_bag_feats(test_df.iloc[i], dataset, num_classes)
                bag_feats = feats.view(-1, feats_size)
                bag_feats = bag_feats.to(DEVICE)
                ins_prediction, bag_prediction, _, _ = model(bag_feats)
                max_prediction, _ = torch.max(ins_prediction, 0)
                Fold_labels.extend([label])
                if average:
                    Fold_predictions.extend(
                        [(0.5 * torch.sigmoid(max_prediction) + 0.5 * torch.sigmoid(
                            bag_prediction)).squeeze().cpu().detach().numpy()])
                else:
                    Fold_predictions.extend(
                        [(0.0 * torch.sigmoid(max_prediction) + 1.0 * torch.sigmoid(
                            bag_prediction)).squeeze().cpu().detach().numpy()])
        Fold_labels = np.array(Fold_labels)
        Fold_predictions = np.array(Fold_predictions)
        Fold_Auc,_,thresh,fpr,tpr=multi_label_roc(Fold_labels, Fold_predictions, num_classes=num_classes,pos_label=1)
        Bin_Preds = np.where(Fold_predictions > thresh, 1, 0)
        All_labels.extend(Fold_labels)
        All_predictions.extend(Fold_predictions)
        All_bin_predictions.extend(Bin_Preds)

    All_labels = np.array(All_labels)
    All_predictions = np.array(All_predictions)

    auc_value, _, thresholds_optimal, fprs, tprs = multi_label_roc(All_labels, All_predictions, num_classes=num_classes,pos_label=1)

    accuracy=sklearn.metrics.accuracy_score(All_labels, All_bin_predictions)
    auc_bin_preds=sklearn.metrics.roc_auc_score(All_labels, All_bin_predictions)
    precision=sklearn.metrics.precision_score(All_labels, All_bin_predictions)
    recall=sklearn.metrics.recall_score(All_labels, All_bin_predictions)
    f1=sklearn.metrics.f1_score(All_labels, All_bin_predictions)


    for c in range(num_classes):
        fpr = fprs[c]
        tpr = tprs[c]
        auc = auc_value[c]
        plt.plot(fpr, tpr, label=f'Class {c} (AUC = {auc:.2f})')
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Random classifier')
    plt.plot([],[], ' ', label=f'Bin AUC = {auc_bin_preds:.2f}')
    plt.plot([],[], ' ', label=f'Accuracy = {accuracy:.2f}')
    plt.plot([],[], ' ', label=f'Precision = {precision:.2f}')
    plt.plot([],[], ' ', label=f'Recall = {recall:.2f}')
    plt.plot([],[], ' ', label=f'F1 = {f1:.2f}')
    plt.title('Receiver Operating Characteristic (ROC) Curve')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.legend()
    plt.savefig(os.path.join(RunDir, 'ROC.png'))
    plt.close()


