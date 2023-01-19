import pandas as pd
import numpy as np
from tools.sp import median_filt

def any_nan(l):
    for ll in l:
        if ll != ll: return True
    return False

sensor_cap = ['pixel%02d' % i for i in list(range(16))]
sensor_temp = ['pixel%02d' % i for i in list(range(16,21))]
def get_sdiff_with_mmed(data, ma_len):

    moving_med = median_filt(data, ma_len)
    diff = data - moving_med
    return diff

def find_noisy_bit_seq(data, lsb=25, ma_len=25):
    assert type(data) is np.ndarray
    diff = get_sdiff_with_mmed(data, ma_len)
    diff_abs = np.abs(diff)
    assert diff.shape == data.shape
    diff_qabs = np.around(diff_abs / (2 ** lsb)).astype(np.int32)

    noise_bits = []
    for i, d in enumerate(diff_qabs):
        d_binstr = "".join(reversed(bin(d)[2:]))
        assert d_binstr[-1] == '1' or d_binstr == '0'
        bidxs = [bidx for bidx, c in enumerate(d_binstr) if c == '1']
        # TODO: Assert indices can be composed to the number
        noise_bits.extend([(i, bidx + lsb) for bidx in bidxs])
    assert min([x for _, x in noise_bits] + [lsb]) >= lsb

    return noise_bits

def find_noisy_bit(df, sensor_names=sensor_cap, lsb=25, ma_len=25):
    ma_filter = [1 / ma_len] * ma_len
    noise_location = []
    for i, k in enumerate(sensor_names):
        data = np.array([int(x, 16) for x in df[k].to_numpy()])
        per_location = find_noisy_bit_seq(data, lsb, ma_len)
        noise_location.extend([(m, k, n) for m, n in per_location])
    return noise_location

def find_noisy_symb(df, sensor_names=sensor_cap, lsb=25, ma_len=25):
    noisy_bits = find_noisy_bit(df, sensor_names, lsb, ma_len)
    return [(m, k) for m, k, _ in noisy_bits]

def denoise_bit(data, lsb=25, ma_len=25):
    diff = get_sdiff_with_mmed(data, ma_len)
    noisy_bits = find_noisy_bit_seq(np.array(data), lsb, ma_len)
    noise = np.zeros_like(data)
    for i, b in noisy_bits:
        noise[i] += (2 ** b) * np.sign(diff[i])

    if type(data) is np.array:
        return data - noise
    else:
        denoise = [d - n for d, n in zip(data, noise.tolist())]
        assert not any_nan(denoise)
        return denoise

def mask0_bits(data, bits=[]):
    assert type(data) is np.array or type(data) is list
    mask = int(sum([2 ** b for b in bits]))
    if type(data) is np.array:
        return data & (~mask)
    else:
        assert type(data[0]) is int
        return [d & (~mask) for d in data]

def mask1_bits(data, bits=[]):
    assert type(data) is np.array or type(data) is list
    mask = int(sum([2 ** b for b in bits]))
    if type(data) is np.array:
        return data | mask
    else:
        assert type(data[0]) is int
        return [d | mask for d in data]

def mask_bits(data, bits=[], value=70e6):
    out0 = mask0_bits(data, bits)
    out1 = mask1_bits(data, bits)
    closer_than = lambda x0, x1, v: abs(x0 - v) < abs(x1 - v)
    return [x0 if closer_than(x0, x1, value) else x1 for x0, x1 in zip(out0, out1)]

def get_bit(data, idx):
    assert type(data) is list and type(data[0]) is int
    assert type(idx) is int and idx < 32
    bit_str = [np.binary_repr(s, width=32)[-idx-1] for s in data]
    bit_int = [int(c) for c in bit_str]
    return np.array(bit_int).astype(np.bool)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('fname', type=str)
    parser.add_argument('--output', type=str, default=None)
    args = parser.parse_args()

    # Data assertion
    assert args.fname[-4:] == '.csv'

    # Data load
    sensor_data_df = pd.read_csv(args.fname)

    # Metadata
    ndata = len(sensor_data_df)
    sensor_name = ['pixel%02d' % i for i in range(25)]

    # Error analysis - 1: Bad ending symbol
    noisy_symb = find_noisy_symb(sensor_data_df)
    perc_noisy_symb = len(noisy_symb) / (ndata * len(sensor_cap)) * 100
    print("Noisy symbol found : %d/%d (%.2f%%)" % (len(noisy_symb), ndata * len(sensor_cap), perc_noisy_symb))

    # Error
    for pname in ['pixel%02d' % i for i in range(16)]:
        noisy_bit = find_noisy_bit(sensor_data_df, [pname])
        bit_set = set([x for _, _, x in noisy_bit])
        bit_all = [x for _, _, x in noisy_bit]
        print("%s: %.2f%% (%3d/%4d) [" % (pname, len(bit_all) / ndata * 100, len(bit_all), ndata), ", ".join(["%d(%2d)" % (b, bit_all.count(b)) for b in bit_set]), "]")

    # Bit rate stats
    for pname in ['pixel%02d' % i for i in range(16)]:
        data_str_list = sensor_data_df[pname].tolist()
        data_list = [int(x, 16) for x in data_str_list]
        ndata = len(data_list)
        bit_rates = [get_bit(data_list, i).sum() / ndata for i in range(32)]
        print("%s: " % pname, ", ".join(["%3d%%" % (x * 100) for x in bit_rates]))

