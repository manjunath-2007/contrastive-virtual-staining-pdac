import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.autograd import Variable
import torchvision.transforms.functional as VF
from torchvision import transforms
import random
from torch.utils.tensorboard import SummaryWriter
import yaml
import random
import sys, argparse, os, copy, itertools, glob, datetime, shutil
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
# matplotlib.use('TkAGG')
import matplotlib.pyplot as plt
from ROC_CrossVal import ROC_CrossVal
import time

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def shrink_down_feats(data, mode):
    for i in range(len(data)):
        tensor = data[i][0]
        if tensor.shape[1] > 500:
            print('####shrinking')
            indices = np.random.choice(tensor.shape[1], size=500, replace=False)
            # selected_rows=tensor[:,indices,:].cuda()
            selected_rows = tensor[:, :500, :].to(DEVICE)
        else:
            selected_rows = tensor.to(DEVICE)
        if mode != 'test':
            bag_label = data[i][1]
            data[i] = (selected_rows, bag_label)
        if mode == 'test':
            bag_label = data[i][1]
            label = data[i][2]
            data[i] = (selected_rows, bag_label, label)
    return data


def BalancedSampler(data, args):
    if args.balancedSampler == 'over':
        positive_rows = data[data['label'] == 1]
        data = pd.concat([data, positive_rows])
        data = data.reset_index(drop=True)
    if args.balancedSampler == 'Doubleover':
        positive_rows = data[data['label'] == 1]
        data = pd.concat([data, positive_rows, positive_rows])
        data = data.reset_index(drop=True)
    else:
        data = data

    return data


def save_checkpoint(state, WeightsDir, is_best, thresholds, filename="checkpoint.pth"):
    filename = os.path.join(WeightsDir, filename)
    torch.save(state, filename)
    if is_best:
        best_filepath = os.path.join(WeightsDir, "checkpoint_best_loss.pth")
        shutil.copyfile(filename, best_filepath)
        with open(os.path.join(WeightsDir, 'thresholds.txt'), 'w') as file:
            file.write('Best thresholds ===>>> ' + '|'.join('class-{}>>{}'.format(*k) for k in enumerate(thresholds)))


def get_bag_feats(csv_file_df, dataset, num_classes, args):
    if dataset == 'TCGA-lung-default':
        feats_csv_path = 'datasets/tcga-dataset/tcga_lung_data_feats/' + csv_file_df.iloc[0].split('/')[1] + '.csv'
    else:
        feats_csv_path = csv_file_df.iloc[0]
    df = torch.load(feats_csv_path, weights_only=True)
    feats = df[torch.randperm(df.size()[0])]
    label = np.zeros(num_classes)
    if num_classes == 1:
        label[0] = csv_file_df.iloc[1]
    else:
        if int(csv_file_df.iloc[1]) <= (len(label) - 1):
            label[int(csv_file_df.iloc[1])] = 1

    return label, feats.unsqueeze(0)


def train(train_df, milnet, criterion, optimizer, dataset, num_classes, dropout_patch, feats_size):
    random.shuffle(train_df)
    milnet.train()
    total_loss = 0
    bc = 0
    Tensor = torch.FloatTensor
    for i in range(len(train_df)):
        optimizer.zero_grad()
        bag_feats, bag_label = train_df[i]  # this line was added

        if augmentations == 'False':
            bag_feats = bag_feats[:, :, :feats_size]
            bag_feats = bag_feats.view(-1, feats_size)
        else:
            augm_val = random.randint(0, 6)
            feats_pos = augm_val * feats_size
            bag_feats = bag_feats[:, :, feats_pos:feats_pos + feats_size]
            bag_feats = bag_feats.view(-1, feats_size)

        ins_prediction, bag_prediction, _, _ = milnet(bag_feats)
        max_prediction, _ = torch.max(ins_prediction, 0)
        bag_loss = criterion(bag_prediction.view(1, -1), bag_label.view(1, -1))
        max_loss = criterion(max_prediction.view(1, -1), bag_label.view(1, -1))
        # loss = 0.5*bag_loss + 0.5*max_loss
        loss = bag_loss + 0.2 * max_loss
        # if bag_label.item()==1.0 or (bag_label.item()==1.0 and random.random()<1/3):
        loss.backward()
        optimizer.step()
        total_loss = total_loss + loss.item()
        sys.stdout.write('\r Training bag [%d/%d] bag loss: %.4f' % (i, len(train_df), loss.item()))
        sys.stdout.flush()
    return total_loss / len(train_df), loss


def dropout_patches(feats, p):
    idx = np.random.choice(np.arange(feats.shape[0]), int(feats.shape[0] * (1 - p)), replace=False)
    sampled_feats = np.take(feats, idx, axis=0)
    pad_idx = np.random.choice(np.arange(sampled_feats.shape[0]), int(feats.shape[0] * p), replace=False)
    pad_feats = np.take(sampled_feats, pad_idx, axis=0)
    sampled_feats = np.concatenate((sampled_feats, pad_feats), axis=0)
    return sampled_feats


def test(test_df, milnet, criterion, optimizer, dataset, num_classes, feats_size, average):
    random.shuffle(test_df)
    milnet.eval()
    total_loss = 0
    test_labels = []
    test_predictions = []
    Tensor = torch.FloatTensor
    with torch.no_grad():
        for i in range(len(test_df)):
            bag_feats, bag_label, label = test_df[i]  # this line was added

            bag_feats = bag_feats.view(-1, feats_size)
            ins_prediction, bag_prediction, _, _ = milnet(bag_feats)
            max_prediction, _ = torch.max(ins_prediction, 0)
            bag_loss = criterion(bag_prediction.view(1, -1), bag_label.view(1, -1))
            max_loss = criterion(max_prediction.view(1, -1), bag_label.view(1, -1))
            loss = 0.5 * bag_loss + 0.5 * max_loss
            total_loss = total_loss + loss.item()
            sys.stdout.write('\r Testing bag [%d/%d] bag loss: %.4f' % (i, len(test_df), loss.item()))
            sys.stdout.flush()
            test_labels.extend([label])
            if average:
                test_predictions.extend([(0.5 * torch.sigmoid(max_prediction) + 0.5 * torch.sigmoid(
                    bag_prediction)).squeeze().cpu().numpy()])
            else:
                test_predictions.extend([(0.0 * torch.sigmoid(max_prediction) + 1.0 * torch.sigmoid(
                    bag_prediction)).squeeze().cpu().numpy()])
    test_labels = np.array(test_labels)
    test_predictions = np.array(test_predictions)
    auc_value, _, thresholds_optimal, fprs, tprs = multi_label_roc(test_labels, test_predictions, num_classes,
                                                                   pos_label=1)
    if num_classes == 1:
        class_prediction_bag = copy.deepcopy(test_predictions)
        class_prediction_bag[test_predictions >= thresholds_optimal[0]] = 1
        class_prediction_bag[test_predictions < thresholds_optimal[0]] = 0
        test_predictions = class_prediction_bag
        test_labels = np.squeeze(test_labels)
    else:
        for i in range(num_classes):
            class_prediction_bag = copy.deepcopy(test_predictions[:, i])
            class_prediction_bag[test_predictions[:, i] >= thresholds_optimal[i]] = 1
            class_prediction_bag[test_predictions[:, i] < thresholds_optimal[i]] = 0
            test_predictions[:, i] = class_prediction_bag
    bag_score = 0
    for i in range(0, len(test_df)):
        bag_score = np.array_equal(test_labels[i], test_predictions[i]) + bag_score
    avg_score = bag_score / len(test_df)

    return total_loss / len(test_df), avg_score, auc_value, thresholds_optimal, fprs, tprs


def multi_label_roc(labels, predictions, num_classes, pos_label=1):
    fprs = []
    tprs = []
    thresholds = []
    thresholds_optimal = []
    aucs = []
    if len(predictions.shape) == 1:
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
    return aucs, thresholds, thresholds_optimal, fprs, tprs


def optimal_thresh(fpr, tpr, thresholds, p=0):
    """
    Finding optimal threshold for a given p
    used to predict class thresholds for the classification
    """
    loss = (fpr - tpr) - p * tpr / (fpr + tpr + 1)
    idx = np.argmin(loss, axis=0)
    return fpr[idx], tpr[idx], thresholds[idx]


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = True


def log_elapsed_time(reference_time, event_name):
    current_time = time.time()
    elapsed_time = current_time - reference_time
    days = elapsed_time // (24 * 3600)
    elapsed_time %= (24 * 3600)
    hours = elapsed_time // 3600
    elapsed_time %= 3600
    minutes = elapsed_time // 60
    seconds = elapsed_time % 60
    sys.stdout.write(
        f"Elapsed time for {str(event_name)}: {int(days)} days, {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds")



parser = argparse.ArgumentParser()
parser.add_argument('--dataset')
parser.add_argument('--featssize')
parser.add_argument('--seed')
parser.add_argument('--Folds')
parser.add_argument('--augment')
parser.add_argument('--optimizer')
parser.add_argument('--sampling')
parser.add_argument('--checkpoint')
parser.add_argument('--env')
parser.add_argument('--balancedSampler')
parser.add_argument('--featsExtractor')

args = parser.parse_args()


config = yaml.load(open('config.yaml', 'r'),Loader=yaml.FullLoader)


dataset = str(args.dataset)
feats_size = int(args.featssize)
seed = int(args.seed)
Folds = int(args.Folds)
augmentations = str(args.augment)
num_classes = int(config['num_classes'])
lr = float(config['lr'])
num_epochs = int(config['num_epochs'])
weight_decay = float(config['weight_decay'])
split = float(config['split'])
model = str(config['model'])
average = config['average']
non_linearity = int(config['non_linearity'])
dropout_patch = float(config['dropout_patch'])
dropout_node = float(config['dropout_node'])
balancedSampler = str(args.balancedSampler)
feats_extractor = 'UNI'
seed_everything(seed)

gpu_index = (0,)

outputDir = os.path.join(os.environ['EXPERIMENT_LOCATION'])


if args.checkpoint != None:
    OutPath_CheckpointKey = 'Checkpoint'
else:
    OutPath_CheckpointKey = ''

OutPutDataSetDir = os.path.join(outputDir, dataset, OutPath_CheckpointKey, str(Folds), 'aug_' + augmentations,
                                str(seed))
if not os.path.exists(OutPutDataSetDir):
    os.makedirs(OutPutDataSetDir)
    print('Dir created')
    print(OutPutDataSetDir)
_, UniqueIdent, _ = next(os.walk(OutPutDataSetDir))
UniqueIdent = str(len(UniqueIdent))
RunDir = os.path.join(OutPutDataSetDir, datetime.now().strftime("%d%m%Y_%H%M%S") + '_' + UniqueIdent)
if not os.path.exists(RunDir):
    os.makedirs(RunDir)

if args.env == 'cluster':
    sys.stdout = open(os.path.join(RunDir, 'Logs.txt'), 'w')

gpu_ids = tuple(gpu_index)
os.environ['CUDA_VISIBLE_DEVICES'] = ','.join(str(x) for x in gpu_ids)

if model == 'dsmil':
    import dsmil as mil
elif model == 'abmil':
    import abmil as mil


bags_csv = os.path.join('Path.csv')

sys.stdout.flush()
bags_path = pd.read_csv(bags_csv)
if dataset == 'HNF':
    data_key = 'HNF'
elif dataset == 'KRT':
    data_key = 'KRT'
elif dataset == 'HE#KRT':
    data_key = 'HE'
elif dataset == 'HE#HNF':
    data_key = 'HE'
elif dataset == 'VirtualKRT':
    data_key = 'KRT'
Data = Splitter(bags_path, 0.2, data_key, args, Folds)
Training_Start = time.time()
sys.stdout.write('\rLoop Started at: %s' % datetime.now().strftime("%d%m%Y_%H%M%S"))
for f in range(len(Data[0])):
    Fold_start_time = time.time()
    i_classifier = mil.FCLayer(in_size=feats_size, out_size=num_classes).to(DEVICE)
    b_classifier = mil.BClassifier(input_size=feats_size, output_class=num_classes, dropout_v=dropout_node,
                                   nonlinear=non_linearity).to(DEVICE)
    milnet = mil.MILNet(i_classifier, b_classifier).to(DEVICE)
    if model == 'dsmil':
        if args.checkpoint != None:
            state_dict_weights = torch.load(
                os.path.join(args.checkpoint, 'Fold_' + str(f) + '/Weights/checkpoint_best_loss.pth'), weights_only=True)
        else:
            if args.env == 'cluster':
                state_dict_weights = torch.load(os.environ['MODEL_INIT'], weights_only=True)
            else:
                state_dict_weights = torch.load('init.pth', weights_only=True)
        try:
            milnet.load_state_dict(state_dict_weights, strict=False)
        except:
            del state_dict_weights['b_classifier.v.1.weight']
            del state_dict_weights['b_classifier.v.1.bias']
            milnet.load_state_dict(state_dict_weights, strict=False)
    if config['criterion'] == 'BCE':
        criterion = nn.BCEWithLogitsLoss()
    elif config['criterion'] == 'CE':
        criterion = nn.CrossEntropyLoss()

    if args.optimizer == 'SGD':
        optimizer = torch.optim.SGD(milnet.parameters(), lr=lr)
    elif args.optimizer == 'Adam':
        optimizer = torch.optim.Adam(milnet.parameters(), lr=lr, betas=(0.5, 0.9), weight_decay=weight_decay)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, num_epochs, 0.000005)
    elif args.optimizer == 'AdamW':
        optimizer = torch.optim.AdamW(milnet.parameters(), lr=lr, betas=(0.5, 0.9), weight_decay=weight_decay)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, num_epochs, 0.000005)

    Fold = 'Fold_' + str(f)
    FoldDir = os.path.join(RunDir, Fold)
    if not os.path.exists(FoldDir):
        os.makedirs(FoldDir)
    TBLogDir = os.path.join(FoldDir, 'TBRuns')
    train_writer = SummaryWriter(log_dir=TBLogDir)
    WeightsDir = os.path.join(FoldDir, 'Weights')
    if not os.path.exists(WeightsDir):
        os.makedirs(WeightsDir)
    train_path = Data[0][f]
    test_path = Data[1][f]
    #####begin cuda optimized section
    train_path = BalancedSampler(train_path, args)
    train_list = []
    Tensor = torch.FloatTensor
    for i in range(len(train_path)):
        label, feats = get_bag_feats(train_path.iloc[i], dataset, num_classes, args)
        if feats_size < 500:
            bag_feats = feats.to(DEVICE)
        else:
            bag_feats = feats
        bag_label = Variable(Tensor([label])).to(DEVICE)
        train_list.append((bag_feats, bag_label))
    train_path = train_list
    test_list = []
    for i in range(len(test_path)):
        label, feats = get_bag_feats(test_path.iloc[i], dataset, num_classes, args)
        if feats_size < 500:
            bag_feats = feats.to(DEVICE)
        else:
            bag_feats = feats
        bag_label = Variable(Tensor([label])).to(DEVICE)
        test_list.append((bag_feats, bag_label, label))
    test_path = test_list
    #####
    best_score = 0
    for epoch in range(0, num_epochs):
        epoch_start_time = time.time()
        sys.stdout.write('\r Epoch %d' % epoch)
        train_start_time = time.time()
        print('featssize',feats_size)
        if feats_size > 500:
            train_path = shrink_down_feats(train_path, mode='train')
            test_path = shrink_down_feats(test_path, mode='test')
        train_loss_bag, loss = train(train_path, milnet, criterion, optimizer, dataset, num_classes, dropout_patch,
                                     feats_size)  # iterate all bags
        log_elapsed_time(train_start_time, 'Training')
        test_start_time = time.time()
        test_loss_bag, avg_score, aucs, thresholds_optimal, fprs, tprs = test(test_path, milnet, criterion, optimizer,
                                                                              dataset, num_classes, feats_size,
                                                                              average)  # iterate all bags
        log_elapsed_time(test_start_time, 'Testing')
        sys.stdout.write('\r Epoch [%d/%d] train loss: %.4f test loss: %.4f, average score: %.4f, AUC: ' % (
        epoch, num_epochs, train_loss_bag, test_loss_bag, avg_score) + '|'.join(
            'class-{}>>{}'.format(*k) for k in enumerate(aucs)))
        # scheduler.step()
        current_score = (sum(aucs) + avg_score) / 2
        if current_score >= best_score:
            best_score = current_score
            is_best = True
            for c in range(num_classes):
                fpr = fprs[c]
                tpr = tprs[c]
                auc = aucs[c]
                plt.plot(fpr, tpr, label=f'Class {c} (AUC = {auc:.2f})')
            plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Random classifier')
            plt.title('Receiver Operating Characteristic (ROC) Curve')
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.legend()
            plt.savefig(os.path.join(FoldDir, 'ROC.png'))
            plt.close()
        else:
            is_best = False
        save_checkpoint(milnet.state_dict(), WeightsDir, is_best, thresholds_optimal)
        sys.stdout.write(
            'Best thresholds ===>>> ' + '|'.join('class-{}>>{}'.format(*k) for k in enumerate(thresholds_optimal)))
        for i in range(len(aucs)):
            train_writer.add_scalar('AUC/class-{}'.format(i), aucs[i], epoch)
            # train_writer.add_scalar('LR', scheduler.get_lr()[0], epoch)
            train_writer.add_scalar('Weights Mean',
                                    np.asarray(milnet.i_classifier.state_dict()['fc.0.weight'].cpu()).mean(), epoch)
            train_writer.add_scalar('Loss', loss, epoch)
            # sys.stdout.write(str(np.asarray(milnet.i_classifier.state_dict()['fc.0.weight'].cpu()).mean()))
        log_elapsed_time(epoch_start_time, 'One Epoch')
    train_writer.close()
    log_elapsed_time(Fold_start_time, 'End of CrossVal')
    del milnet
args_dict = vars(args)
config['args'] = args_dict
with open(os.path.join(RunDir, 'config.yaml'), 'w') as fp:
    yaml.dump(config, fp)
i_classifier = mil.FCLayer(in_size=feats_size, out_size=num_classes).to(DEVICE)
b_classifier = mil.BClassifier(input_size=feats_size, output_class=num_classes, dropout_v=dropout_node,
                               nonlinear=non_linearity).to(DEVICE)
milnet = mil.MILNet(i_classifier, b_classifier).to(DEVICE)
log_elapsed_time(Training_Start, 'Completion of Training')
before_finalROC = time.time()
ROC_CrossVal(RunDir=RunDir, Dataset=dataset, Folds=Folds, model=milnet, num_classes=num_classes, feats_size=feats_size,
             average=average, args=args)

log_elapsed_time(before_finalROC, 'Completion of ROC')
if args.env == 'cluster':
    sys.stdout.close()