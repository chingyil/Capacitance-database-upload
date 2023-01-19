import pandas as pd

def count_symb(df, col_name, target):
    symbols = df[col_name].tolist()
    return [(i, col_name) for i, s in enumerate(symbols) if s == target]

def find_bad_endsymb(df):
    end_symbols = df['pixel24'].tolist()
    return [(i, 'pixel24') for i, s in enumerate(end_symbols) if s != '10101010']

def strsim(s0, s1):
    assert len(s0) == len(s1)
    return sum([1 if c0 == c1 else 0 for c0, c1 in zip(s0, s1)])

sensor_name_nonref = ['pixel%02d' % i for i in list(range(1,23)) + [24]]
def find_replicated_symbol(df, sensor_names=sensor_name_nonref, similarity=8):
    repl_location = []
    for i, k in enumerate(sensor_names):
        if i == 0: continue
        k_prev = sensor_names[i - 1]
        col_prev, col = df[k_prev].tolist(), df[k].tolist()
        assert type(df[k].tolist()[0]) is str
        repl = [(i,k) for i, (s0, s1) in enumerate(zip(col_prev, col)) if strsim(s0, s1) == similarity]
        repl_location.extend(repl)
    return repl_location

sensor_name_all = ['pixel%02d' % i for i in list(range(25))]
def find_zero_symbol(df, sensor_names=sensor_name_all):
    zero_symb = []
    for s in sensor_name_all:
        zero_symb.extend(count_symb(df, s, '00000000'))
    return zero_symb

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('fname', type=str)
    parser.add_argument('--output', type=str, default=None)
    args = parser.parse_args()

    # Data assertion
    assert args.fname[-4:] == '.csv'

    # Data load
    sensor_data_df = pd.read_csv(args.fname, dtype=str)

    # Metadata
    ndata = len(sensor_data_df)
    sensor_name = ['pixel%02d' % i for i in range(25)]

    # Error analysis - 1: Bad ending symbol
    bad_endsymb = find_bad_endsymb(sensor_data_df)
    perc_bad_endsymb = len(bad_endsymb) / ndata * 100
    print("Bad end symbol found : %d/%d (%.2f%%)" % (len(bad_endsymb), ndata, perc_bad_endsymb))
    
    # Error analysis - 2: Replicating symbol
    idx_cols = list(range(1,23)) + [24]
    repl_symb = find_replicated_symbol(sensor_data_df)
    perc_repl_symb = len(repl_symb) / (ndata * len(idx_cols)) * 100
    print("Replicated symbol found : %d/%d (%.2f%%)" % (len(repl_symb), ndata * len(idx_cols), perc_repl_symb))
   
    # Error analysis - 3: Zero symbol
    n_zero_symb = sum([len(count_symb(sensor_data_df, s, '00000000')) for s in sensor_name])
    perc_zero_symb = n_zero_symb / (ndata * len(sensor_name)) * 100
    print("Zero symbol found : %d/%d (%.2f%%)" % (n_zero_symb, ndata * len(sensor_name), perc_zero_symb))
   
    # Error analysis - 4: Unmatch reference symbol
    replref_symb = find_replicated_symbol(sensor_data_df, sensor_names=['pixel23'])
    perc_replref_symb = (ndata - len(replref_symb)) / ndata * 100
    print("Unmatch reference symbol found : %d/%d (%.2f%%)" % (ndata - len(replref_symb), ndata, perc_replref_symb))
