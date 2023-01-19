import numpy as np

def median_filt(data, ma_len):
    # Type check
    assert type(data) is np.ndarray or type(data) is list

    # Expand (roll) with padding preprocessing
    hma = (ma_len + 1) // 2
    data_pad = np.pad(data, (hma, hma), 'edge')
    assert len(data_pad) == len(data) + 2 * hma
    data_unroll = np.array([np.roll(data_pad, x) for x in range(-hma, hma)])

    # Get median from expanded array
    result = np.median(data_unroll, axis=0)[hma:-hma]
    assert len(result) == len(data)
    return result

