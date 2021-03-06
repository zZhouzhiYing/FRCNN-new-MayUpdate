import numpy as np
import torch
import torch.backends.cudnn as cudnn
import torch.optim as optim
from torch.autograd import Variable
from torch.utils.data import DataLoader
from tqdm import tqdm

from nets.frcnn import FasterRCNN
from trainer import FasterRCNNTrainer
from utils.dataloader import FRCNNDataset, frcnn_dataset_collate
from utils.utils import LossHistory, weights_init


def get_lr(optimizer):
    for param_group in optimizer.param_groups:
        return param_group['lr']
        
def fit_ont_epoch(net,epoch,epoch_size,epoch_size_val,gen,genval,Epoch,cuda):
    total_loss = 0
    rpn_loc_loss = 0
    rpn_cls_loss = 0
    roi_loc_loss = 0
    roi_cls_loss = 0
    val_toal_loss = 0
    with tqdm(total=epoch_size,desc=f'Epoch {epoch + 1}/{Epoch}',postfix=dict,mininterval=0.3) as pbar:
        for iteration, batch in enumerate(gen):
            if iteration >= epoch_size:
                break
            imgs, boxes, labels = batch[0], batch[1], batch[2]
            with torch.no_grad():
                if cuda:
                    imgs = Variable(torch.from_numpy(imgs).type(torch.FloatTensor)).cuda()
                else:
                    imgs = Variable(torch.from_numpy(imgs).type(torch.FloatTensor))

            losses = train_util.train_step(imgs, boxes, labels, 1)
            rpn_loc, rpn_cls, roi_loc, roi_cls, total = losses
            total_loss += total.item()
            rpn_loc_loss += rpn_loc.item()
            rpn_cls_loss += rpn_cls.item()
            roi_loc_loss += roi_loc.item()
            roi_cls_loss += roi_cls.item()
            
            pbar.set_postfix(**{'total'    : total_loss / (iteration + 1), 
                                'rpn_loc'  : rpn_loc_loss / (iteration + 1),  
                                'rpn_cls'  : rpn_cls_loss / (iteration + 1), 
                                'roi_loc'  : roi_loc_loss / (iteration + 1), 
                                'roi_cls'  : roi_cls_loss / (iteration + 1), 
                                'lr'       : get_lr(optimizer)})
            pbar.update(1)

    print('Start Validation')
    with tqdm(total=epoch_size_val, desc=f'Epoch {epoch + 1}/{Epoch}',postfix=dict,mininterval=0.3) as pbar:
        for iteration, batch in enumerate(genval):
            if iteration >= epoch_size_val:
                break
            imgs,boxes,labels = batch[0], batch[1], batch[2]
            with torch.no_grad():
                if cuda:
                    imgs = Variable(torch.from_numpy(imgs).type(torch.FloatTensor)).cuda()
                else:
                    imgs = Variable(torch.from_numpy(imgs).type(torch.FloatTensor))

                train_util.optimizer.zero_grad()
                losses = train_util.forward(imgs, boxes, labels, 1)
                _, _, _, _, val_total = losses

                val_toal_loss += val_total.item()

            pbar.set_postfix(**{'total_loss': val_toal_loss / (iteration + 1)})
            pbar.update(1)

    loss_history.append_loss(total_loss/(epoch_size+1), val_toal_loss/(epoch_size_val+1))
    print('Finish Validation')
    print('Epoch:'+ str(epoch+1) + '/' + str(Epoch))
    print('Total Loss: %.4f || Val Loss: %.4f ' % (total_loss/(epoch_size+1),val_toal_loss/(epoch_size_val+1)))
    print('Saving state, iter:', str(epoch+1))
    torch.save(model.state_dict(), 'logs/Epoch%d-Total_Loss%.4f-Val_Loss%.4f.pth'%((epoch+1),total_loss/(epoch_size+1),val_toal_loss/(epoch_size_val+1)))
    
if __name__ == "__main__":
    #-------------------------------#
    #   ????????????Cuda
    #   ??????GPU???????????????False
    #-------------------------------#
    Cuda = True
    #----------------------------------------------------#
    #   ???????????????????????????NUM_CLASSES
    #   ??????????????????????????????????????????
    #----------------------------------------------------#
    NUM_CLASSES = 20
    #-------------------------------------------------------------------------------------#
    #   input_shape????????????????????????????????????800,800,3??????????????????????????????????????????????????????
    #   ????????????600,600,3????????????????????????800,800,3????????????
    #-------------------------------------------------------------------------------------#
    input_shape = [800,800,3]
    #----------------------------------------------------#
    #   ????????????????????????????????????
    #   vgg??????resnet50
    #----------------------------------------------------#
    backbone = "resnet50"
    model = FasterRCNN(NUM_CLASSES,backbone=backbone)
    weights_init(model)

    # #------------------------------------------------------#
    #   ??????????????????README?????????????????????
    #------------------------------------------------------#
    model_path = 'model_data/voc_weights_resnet.pth'
    print('Loading weights into state dict...')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # model_dict = model.state_dict()
    pretrained_dict = torch.load(model_path, map_location=device)
    dict_new = model.state_dict().copy()
    new_list = list (model.state_dict().keys() )
    trained_list = list (pretrained_dict.keys()  )
    # print("new_state_dict size: {}  trained state_dict size: {}".format(len(new_list),len(trained_list)) )
    # print("New state_dict first 10th parameters names")
    # print(new_list[:],)
    # print("trained state_dict first 10th parameters names")
    # print(trained_list[:1])

    for i in range(258):
        dict_new[ new_list[i] ] = pretrained_dict[ trained_list[i] ]

    dict_new[ new_list[334] ] = pretrained_dict[ trained_list[258] ]
    dict_new[ new_list[335] ] = pretrained_dict[ trained_list[259] ]
    dict_new[ new_list[336] ] = pretrained_dict[ trained_list[260] ]
    dict_new[ new_list[337] ] = pretrained_dict[ trained_list[261] ]
    dict_new[ new_list[338] ] = pretrained_dict[ trained_list[262] ]
    dict_new[ new_list[339] ] = pretrained_dict[ trained_list[263] ]
    dict_new[ new_list[342] ] = pretrained_dict[ trained_list[324] ]
    dict_new[ new_list[343] ] = pretrained_dict[ trained_list[325] ]
    dict_new[ new_list[344] ] = pretrained_dict[ trained_list[326] ]
    dict_new[ new_list[345] ] = pretrained_dict[ trained_list[327] ]
    model.load_state_dict(dict_new)


    # pretrained_dict = {k: v for k, v in pretrained_dict.items() if np.shape(model_dict[k]) ==  np.shape(v)}
    
    # print(pretrained_dict.keys())
    # num=0
    # params = list(model.named_parameters())
    # for k, v in params:
    #     num=num+1
    #     print('?????????key',k)
    # print(num)

    # for k,v in pretrained_dict.items():
    #     print('pth???key???',k) 
    # model_dict.update(pretrained_dict)
    # model.load_state_dict(model_dict)
    # model.load_state_dict(pretrained_dict)

    # i=0
    # for child in model.children():
    #     i+=1
    #     print("???{}???child".format(str(i)))
    #     print(child)
    #     print('Finished!')
    # torch.save(model.state_dict(),'xxx.pth')

    net = model.train()
    if Cuda:
        net = torch.nn.DataParallel(model)
        cudnn.benchmark = True
        net = net.cuda()

    loss_history = LossHistory("logs/")

    annotation_path = '2007_train.txt'
    #----------------------------------------------------------------------#
    #   ?????????????????????train.py??????????????????
    #   2007_test.txt???2007_val.txt?????????????????????????????????????????????????????????
    #   ?????????????????????????????????????????????????????????1:9
    #----------------------------------------------------------------------#
    val_split = 0.1
    with open(annotation_path) as f:
        lines = f.readlines()
    np.random.seed(10101)
    np.random.shuffle(lines)
    np.random.seed(None)
    num_val = int(len(lines)*val_split)
    num_train = len(lines) - num_val

    #------------------------------------------------------#
    #   ???????????????????????????????????????????????????????????????????????????
    #   ????????????????????????????????????????????????
    #   Init_Epoch???????????????
    #   Freeze_Epoch????????????????????????
    #   Epoch???????????????
    #   ??????OOM???????????????????????????Batch_size
    #------------------------------------------------------#
    if True:
        lr = 1e-4
        Batch_size = 2
        Init_Epoch = 0
        Freeze_Epoch = 50
        
        optimizer = optim.Adam(filter(lambda p: p.requires_grad, net.parameters()), lr, weight_decay=5e-4)
        lr_scheduler = optim.lr_scheduler.StepLR(optimizer,step_size=1,gamma=0.95)

        train_dataset = FRCNNDataset(lines[:num_train], (input_shape[0], input_shape[1]), is_train=True)
        val_dataset   = FRCNNDataset(lines[num_train:], (input_shape[0], input_shape[1]), is_train=False)
        gen     = DataLoader(train_dataset, shuffle=True, batch_size=Batch_size, num_workers=4, pin_memory=True,
                                drop_last=True, collate_fn=frcnn_dataset_collate)
        gen_val = DataLoader(val_dataset, shuffle=True, batch_size=Batch_size, num_workers=4, pin_memory=True,
                                drop_last=True, collate_fn=frcnn_dataset_collate)
                        
        epoch_size = num_train // Batch_size
        epoch_size_val = num_val // Batch_size

        if epoch_size == 0 or epoch_size_val == 0:
            raise ValueError("????????????????????????????????????????????????????????????")

        # ------------------------------------#
        #   ????????????????????????
        # ------------------------------------#
        for param in model.extractor.parameters():
            if not str(param).startswith('extractor.0.layer4.'):
                param.requires_grad = False

        # ------------------------------------#
        #   ??????bn???
        # ------------------------------------#
        model.freeze_bn()

        train_util = FasterRCNNTrainer(model, optimizer)

        for epoch in range(Init_Epoch,Freeze_Epoch):
            fit_ont_epoch(net,epoch,epoch_size,epoch_size_val,gen,gen_val,Freeze_Epoch,Cuda)
            lr_scheduler.step()

    if True:
        lr = 1e-5
        Batch_size = 2
        Freeze_Epoch = 50
        Unfreeze_Epoch = 100

        optimizer = optim.Adam(net.parameters(), lr, weight_decay=5e-4)
        lr_scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.95)

        train_dataset = FRCNNDataset(lines[:num_train], (input_shape[0], input_shape[1]), is_train=True)
        val_dataset   = FRCNNDataset(lines[num_train:], (input_shape[0], input_shape[1]), is_train=False)
        gen     = DataLoader(train_dataset, shuffle=True, batch_size=Batch_size, num_workers=4, pin_memory=True,
                                drop_last=True, collate_fn=frcnn_dataset_collate)
        gen_val = DataLoader(val_dataset, shuffle=True, batch_size=Batch_size, num_workers=4, pin_memory=True,
                                drop_last=True, collate_fn=frcnn_dataset_collate)
                        
        epoch_size = num_train // Batch_size
        epoch_size_val = num_val // Batch_size
        
        if epoch_size == 0 or epoch_size_val == 0:
            raise ValueError("????????????????????????????????????????????????????????????")
            
        #------------------------------------#
        #   ???????????????
        #------------------------------------#
        for param in model.extractor.parameters():
            param.requires_grad = True

        # ------------------------------------#
        #   ??????bn???
        # ------------------------------------#
        model.freeze_bn()

        train_util = FasterRCNNTrainer(model,optimizer)

        for epoch in range(Freeze_Epoch,Unfreeze_Epoch):
            fit_ont_epoch(net,epoch,epoch_size,epoch_size_val,gen,gen_val,Unfreeze_Epoch,Cuda)
            lr_scheduler.step()
