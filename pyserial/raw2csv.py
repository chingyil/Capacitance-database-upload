from datetime import datetime, timedelta
import pandas as pd
from tools.error_analysis import find_bad_endsymb, find_replicated_symbol, count_symb
from tools.bitmask import mask_with0

sensor_name = ['pixel%02d' % i for i in range(25)]

# Parsing utility
def get_hex(s):
    idx_hex = 10
    assert s[idx_hex:idx_hex+2] == '0x', print("Not a hex:", s[idx_hex:])
    s_hex = s[idx_hex+2:idx_hex+10]
    assert '(' not in s_hex and 'x' not in s_hex
    return s_hex

def load_datahex_sa(fname):
    count = 0
    count_data = 0
    time_str = []
    data_hex = []
    traw_latest = None
    t_latest = datetime.strptime("00", "%S")
    day_os = 0
    with open(fname) as f:
        while 1:
            l = f.readline()[27:]
            # l = f.readline()
            if len(l) == 0:
                break
            if "->" in l: # Has timestamp
                assert len(l.split("-> ")) >= 2
                if len(l.split("-> ")) == 2:
                    traw_latest, msg = l[:-1].split("-> ")
                elif len(l.split("-> ")) > 2:
                    traw_latest = l[:-1].split("-> ")[0]
                    msg = l[:-1].split("-> ")[-1]
            else:
                msg = l[:-1]
            count += 1
            
            assert '\n' not in msg
            if msg[:6] == 'Data #': # Has data
                assert t_latest is not None

                # Data handling
                msg_hex = get_hex(msg)
                data_hex.append(msg_hex)

                # Time handling: Add day offset since no time info is available\
                try:
                    t = datetime.strptime(traw_latest, "%H:%M:%S.%f")
                except ValueError:
                    idx_semicolon = traw_latest.index(":")
                    print(traw_latest, idx_semicolon)
                    t = datetime.strptime(traw_latest[idx_semicolon + 1:], "%M:%S.%f") + timedelta(hours=int(traw_latest[idx_semicolon - 2: idx_semicolon]))
                if t + timedelta(day_os) < t_latest:
                    day_os += 1
                    assert t + timedelta(day_os) > t_latest
                tstr = (t + timedelta(day_os)).strftime('%y/%m/%d %H:%M:%S.%f')
                time_str.append(tstr)

                # Update counter and latest time
                t_latest = t + timedelta(day_os)
                count_data += 1
    print("%d lines read" % count)
    print("%d lines data" % count_data)
    assert len(data_hex) == len(time_str)
    return data_hex, time_str

def load_datahex(fname, has_time):
    count = 0
    count_data = 0
    time_str = []
    data_hex = []
    with open(fname) as f:
        while 1:
            l = f.readline()
            if len(l) == 0:
                break
            if has_time:
                if l[0] == '[' and l[25:27] == '] ' and l[-1] == '\n':
                    msg = l[27:-1]
                elif l[24:27] == ' : ':
                    msg = l[27:-1]
                else:
                    print("l[24:27] = ", l[24:27])
                    raise Exception()
            else:
                msg = l[:-1]
            count += 1
            
            assert '\n' not in msg
            if msg[:4] == 'Data':
                count_data += 1
                msg_hex = get_hex(msg)
                data_hex.append(msg_hex)
                time_str.append(l[1:25] if has_time else "")
    print("%d lines read" % count)
    print("%d lines data" % count_data)
    assert len(data_hex) == len(time_str)
    return data_hex, time_str

def chunk_seg(indices):
    intervals = [indices[0]] + [indices[i] - indices[i-1] for i in range(1, len(indices))]

    intv_prev, idx_prev = 0, 0
    idx_endsymbol2 = []
    for idx_end, intv in zip(indices, intervals):
        if intv == 25:
            if idx_prev != -1:
                idx_endsymbol2.append(idx_prev)
            idx_endsymbol2.append(idx_end)
            idx_prev = -1
        elif intv % 25 == 0:
            if idx_prev != -1:
                idx_endsymbol2.append(idx_prev)
            for i in reversed(range(intv // 25)):
                idx_endsymbol2.append(idx_end - 25 * i)
            idx_prev = -1
        elif intv + intv_prev == 25:
            idx_prev = -1
            idx_endsymbol2.append(idx_end)
        else:
            intv_prev = intv
            idx_prev = idx_end
    return idx_endsymbol2

def assign_allsensor(sensor_dict, chunk):
    assert len(chunk) == 25
    l = len(sensor_dict[sensor_name[0]])
    for k, val in zip(sensor_name, chunk):
        sensor_dict[k].append(val)
        assert len(sensor_dict[k]) == l + 1
    return

def get_sensordf(data_hex, time_str):
    idx_endsymbol = chunk_seg([i for i, s in enumerate(data_hex) if s == '10101010'])

    intervals = [idx_endsymbol[0]] + [idx_endsymbol[i] - idx_endsymbol[i-1] for i in range(1, len(idx_endsymbol))]

    sensor_time = {k:[] for k in sensor_name}
    sensor_data = {k:[] for k in sensor_name}
    for i, (idx_end, intv) in enumerate(zip(idx_endsymbol, intervals)):
        idx_start = idx_end + 1 - intv
        if intv == 25:
            chunk = data_hex[idx_start: idx_start + 25]
            assign_allsensor(sensor_data, chunk)
            chunk_time = time_str[idx_end - 24: idx_end + 1]
            assign_allsensor(sensor_time, chunk_time)
        elif intv % 25 == 0:
            for idx_chunk in range(intv // 25):
                chunk = data_hex[idx_start + 25 * idx_chunk: idx_start + 25 * idx_chunk + 25]
                assign_allsensor(sensor_data, chunk)
                chunk_time = time_str[idx_start + 25 * idx_chunk: idx_start + 25 * idx_chunk + 25]
                assign_allsensor(sensor_time, chunk_time)
            assert idx_start + 25 * idx_chunk + 24 == idx_end
        else:
            print("Invalid interval %-3d (@%-5d)" % (intv, idx_end))
        assert idx_end == idx_endsymbol[i-1] + intv if i > 0 else True
    sensor_data_df = pd.DataFrame(data=sensor_data)
    sensor_time_df = pd.DataFrame(data=sensor_time)
    return sensor_data_df, sensor_time_df

# def count_symb(df, col_name, target):
#     symbols = df[col_name].tolist()
#     return [i for i, s in enumerate(symbols) if s != target]
# 
# def find_bad_endsymb(df):
#     end_symbols = df['pixel24'].tolist()
#     return [(i, 25) for i, s in enumerate(end_symbols) if s != '10101010']
# 
# def strsim(s0, s1):
#     assert len(s0) == len(s1)
#     return sum([1 if c0 == c1 else 0 for c0, c1 in zip(s0, s1)])
# 
# def find_replicated_symbol(df, idx_cols=list(range(1,23)) + [24], similarity=8):
#     repl_location = []
#     for idx_col in idx_cols:
#         k_prev, k_curr = sensor_name[idx_col - 1], sensor_name[idx_col]
#         col_prev, col_curr = df[k_prev].tolist(), df[k_curr].tolist()
#         repl = [(i,idx_col) for i, (s0, s1) in enumerate(zip(col_prev, col_curr)) if strsim(s0, s1) == similarity]
#         repl_location.extend(repl)
#     return repl_location
# 
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('fname', type=str)
    parser.add_argument('--output', type=str, default=None)
    parser.add_argument('--no-time', action='store_true')
    parser.add_argument('--safmt', action='store_true')
    parser.add_argument('--merge', type=str, nargs='+', default=None)
    args = parser.parse_args()

    # Metadata
    sensor_name = ['pixel%02d' % i for i in range(25)]
    fname_csv = args.output if args.output is not None else args.fname.split('/')[-1][:-4] + '.csv'
    fname_csvtime = args.fname.split('/')[-1][:-4] + '_time.csv'

    # Load hex data
    fname = args.fname
    if args.safmt:
        data_hex, time_str = load_datahex_sa(fname)
    else:
        has_time = True if not args.no_time else False
        data_hex, time_str = load_datahex(fname, has_time=has_time)
    assert type(data_hex) is list and type(time_str) is list

    if args.merge is not None:
        fname = args.fname
        if args.safmt:
            data_hex_new, time_str_new = load_datahex_sa(fname)
        else:
            has_time = True if not args.no_time else False
            data_hex_new, time_str_new = load_datahex(fname, has_time=has_time)
        data_hex.extend(data_hex_new)
        time_str.extend(time_str_new)
        assert type(data_hex) is list and type(time_str) is list

    sensor_data_df, sensor_time_df = get_sensordf(data_hex, time_str)
    print(sensor_data_df)
    print("Export %s" % fname_csv)
    sensor_data_df.to_csv(fname_csv, index=False)
    print("Export %s" % fname_csvtime)
    sensor_time_df.to_csv(fname_csvtime, index=False)
