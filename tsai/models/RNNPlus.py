# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/105_models.RNNPlus.ipynb (unless otherwise specified).

__all__ = ['RNNPlus', 'LSTMPlus', 'GRUPlus']

# Cell
from ..imports import *
from ..utils import *
from ..data.core import *
from .layers import *

# Cell
class _RNNPlus_Base(Module):
    def __init__(self, c_in, c_out, seq_len=None, hidden_size=100, n_layers=1, bias=True, rnn_dropout=0, bidirectional=False, fc_dropout=0.,
                 last_step=True, flatten=False, custom_head=None, y_range=None, **kwargs):
        if flatten: assert seq_len, 'you need to enter a seq_len to use flatten=True'
        self.ls, self.fl = last_step, flatten
        self.rnn = self._cell(c_in, hidden_size, num_layers=n_layers, bias=bias, batch_first=True, dropout=rnn_dropout, bidirectional=bidirectional)
        if flatten: self.flatten = Reshape(-1)

        # Head
        self.head_nf = seq_len * hidden_size * (1 + bidirectional) if flatten and not last_step else hidden_size * (1 + bidirectional)
        self.c_out = c_out
        if custom_head: self.head = custom_head(self.head_nf, c_out) # custom head must have all required kwargs
        else: self.head = self.create_head(self.head_nf, c_out, fc_dropout=fc_dropout, y_range=y_range)

    def forward(self, x):
        x = x.transpose(2,1)                                             # [batch_size x n_vars x seq_len] --> [batch_size x seq_len x n_vars]
        output, _ = self.rnn(x)                                          # [batch_size x seq_len x hidden_size * (1 + bidirectional)]
        if self.ls: output = output[:, -1]                               # [batch_size x hidden_size * (1 + bidirectional)]
        if self.fl: output = self.flatten(output)                        # [batch_size x seq_len * hidden_size * (1 + bidirectional)]
        if not self.ls and not self.fl: output = output.transpose(2,1)
        return self.head(output)

    def create_head(self, nf, c_out, fc_dropout=0., y_range=None):
        layers = [nn.Dropout(fc_dropout)] if fc_dropout else []
        layers += [nn.Linear(self.head_nf, c_out)]
        if y_range is not None: layers += [SigmoidRange(*y_range)]
        return nn.Sequential(*layers)


class RNNPlus(_RNNPlus_Base):
    _cell = nn.RNN

class LSTMPlus(_RNNPlus_Base):
    _cell = nn.LSTM

class GRUPlus(_RNNPlus_Base):
    _cell = nn.GRU