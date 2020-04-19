# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/100_layers.ipynb (unless otherwise specified).

__all__ = ['noop', 'same_padding1d', 'ZeroPad1d', 'ConvSP1d', 'Chomp1d', 'CausalConv1d', 'convlayer', 'CoordConv1D',
           'LambdaPlus', 'Flatten', 'Squeeze', 'Unsqueeze', 'YRange', 'Temp']

# Cell
import torch
import torch.nn as nn
from fastai2.torch_core import Module

# Cell
def noop(x): return x

# Cell
def same_padding1d(seq_len,ks,stride=1,dilation=1):
    assert stride > 0
    assert dilation >= 1
    effective_ks = (ks - 1) * dilation + 1
    out_dim = (seq_len + stride - 1) // stride
    p = max(0, (out_dim - 1) * stride + effective_ks - seq_len)
    padding_before = p // 2
    padding_after = p - padding_before
    return padding_before, padding_after

class ZeroPad1d(nn.ConstantPad1d):
    def __init__(self, padding):
        super().__init__(padding, 0.)

class ConvSP1d(Module):
    "Conv1d padding='same'"
    def __init__(self,c_in,c_out,ks,stride=1,padding='same',dilation=1,bias=True):
        super().__init__()
        self.ks, self.stride, self.dilation = ks, stride, dilation
        self.conv = nn.Conv1d(c_in,c_out,ks,stride=stride,padding=0,dilation=dilation,bias=bias)
        self.zeropad = ZeroPad1d
        self.weight = self.conv.weight
        self.bias = self.conv.bias

    def forward(self, x):
        padding = same_padding1d(x.shape[-1],self.ks,stride=self.stride,dilation=self.dilation)
        return self.conv(self.zeropad(padding)(x))

# Cell
class Chomp1d(Module):
    def __init__(self, chomp_size):
        self.chomp_size = chomp_size
    def forward(self, x):
        return x[:, :, :-self.chomp_size].contiguous()


class CausalConv1d(Module):
    def __init__(self, c_in, c_out, ks, dilation=1, **kwargs):
        padding = (ks-1) * dilation
        self.conv = nn.Conv1d(c_in, c_out, ks, padding=padding, dilation=dilation, **kwargs)
        self.chomp = Chomp1d(padding)
    def forward(self, x):
        return self.chomp(self.conv(x))

# Cell
def convlayer(c_in,c_out,ks=3,padding='same',bias=True,stride=1,
              bn_init=False,zero_bn=False,bn_before=True,act_fn=True,**kwargs):
    '''conv layer (padding="same") + bn + act'''
    if ks % 2 == 1 and padding == 'same': padding = ks // 2
    layers = [ConvSP1d(c_in,c_out, ks, bias=bias, stride=stride) if padding == 'same' else \
    nn.Conv1d(c_in,c_out, ks, stride=stride, padding=padding, bias=bias)]
    bn = nn.BatchNorm1d(c_out)
    if bn_init: nn.init.constant_(bn.weight, 0. if zero_bn else 1.)
    if bn_before: layers.append(bn)
    if act_fn: layers.append(nn.ReLU())
    if not bn_before: layers.append(bn)
    return nn.Sequential(*layers)

# Cell
class CoordConv1D(Module):
    def forward(self, x):
        bs, _, seq_len = x.size()
        cc = torch.arange(seq_len, device=device, dtype=torch.float) / (seq_len - 1)
        cc = cc * 2 - 1
        cc = cc.repeat(bs, 1, 1)
        x = torch.cat([x, cc], dim=1)
        return x

# Cell
class LambdaPlus(Module):
    def __init__(self, func, *args, **kwargs): self.func,self.args,self.kwargs=func,args,kwargs
    def forward(self, x): return self.func(x, *self.args, **self.kwargs)

# Cell
class Flatten(Module):
    def forward(self, x): return x.view(x.size(0), -1)

class Squeeze(Module):
    def __init__(self, dim=-1):
        self.dim = dim
    def forward(self, x): return x.squeeze(dim=self.dim)

class Unsqueeze(Module):
    def __init__(self, dim=-1):
        self.dim = dim
    def forward(self, x): return x.unsqueeze(dim=self.dim)

class YRange(Module):
    def __init__(self, y_range:tuple):
        self.y_range = y_range
    def forward(self, x):
        x = F.sigmoid(x)
        return x * (self.y_range[1] - self.y_range[0]) + self.y_range[0]

class Temp(Module):
    def __init__(self, temp):
        self.temp = float(temp)
        self.temp = nn.Parameter(torch.Tensor(1).fill_(self.temp).to(device))
    def forward(self, x):
        return x.div_(self.temp)