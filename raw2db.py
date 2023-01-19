from datetime import datetime, timedelta
import pandas as pd
from pyserial.raw2csv import get_hex, load_datahex_sa, load_datahex, chunk_seg, get_sensordf
import mysql.connector

def get_info_from_fname(fname):
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    cell_name = ['ypd', 'water', 'Jurkat']
    t1900 = datetime.strptime("00", "%S")

    expr_info = {}
    fname_tokens = [s for s in fname.split('.')[0].split('/')[-1].split('_')]
    chip_lst = [s for s in fname_tokens if s[:4] == 'chip']
    chip_str = str(int(chip_lst[0][4:])) if len(chip_lst) == 1 else 'NULL'
    if len(chip_lst) == 1:
        expr_info['chip_id'] = str(int(chip_lst[0][4:]))

    date_token = [s for s in fname_tokens if s.lower()[:3] in months]
    date = datetime.strptime(date_token[0], "%b%d") if len(date_token) == 1 else None
    year_offset = (t1900 + (datetime.now() - date)).year
    date_new = datetime.strptime(str(year_offset) + date.strftime("/%m/%d"), "%Y/%m/%d")
    expr_info['date'] = date_new

    cell_included = [s for s in cell_name if s in args.fname]
    if len(cell_included) == 1:
        expr_info['cell_name'] = cell_included[0]

    return expr_info

def mysql_send(cursor, query, log=True):
    assert type(query) is str
    if log:
        print("> ", query)
    cursor.execute(query)
    ret = cursor.fetchall()
    if log:
        print("[mySQL]", ret)
    return ret

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('fname', type=str)
    parser.add_argument('--output', type=str, default=None)
    parser.add_argument('--no-time', action='store_true')
    parser.add_argument('--safmt', action='store_true')
    args = parser.parse_args()

    # Metadata
    fname_csv = args.output if args.output is not None else args.fname.split('/')[-1][:-4] + '.csv'
    fname_csvtime = args.fname.split('/')[-1][:-4] + '_time.csv'

    # Load hex data
    fname = args.fname
    if args.safmt:
        data_hex, time_str = load_datahex_sa(fname)
        has_time = True
    else:
        has_time = True if not args.no_time else False
        data_hex, time_str = load_datahex(fname, has_time=has_time)
    
    sensor_data_df, sensor_time_df = get_sensordf(data_hex, time_str)

    
    cnx = mysql.connector.connect(user='root-icbio', database='cell_capacitance', password='Pessw0rd-', host='10.0.0.144')
    # cnx = mysql.connector.connect(user='chingyil', database='cell_capacitance', password='password', host='127.0.0.1')
    cursor = cnx.cursor()

    expr_info = get_info_from_fname(args.fname)

    col_names = []
    values = []
    for k, v in expr_info.items():
        col_names.append(k)
        if k == 'date':
            val = '"' + v.strftime("%Y-%m-%d") + '"'
        elif k == 'chip_id':
            val = v
        else:
            val = '"' + v + '"'
        values.append(val)
    print("Info extracted:", expr_info)
    query = 'INSERT INTO expr (%s) VALUES (%s);' % (", ".join(col_names), ", ".join(values))
    mysql_send(cursor, query)

    query = 'select * from expr order by id desc limit 1;'
    expr_id = mysql_send(cursor, query)[0][0]
    print("Expr ID = %d" % expr_id)

    for i in range(len(sensor_data_df)):
        row = sensor_data_df.iloc[i].tolist()
        rowt = sensor_time_df.iloc[i].tolist()
        for j, (t, v) in enumerate(zip(rowt, row)):
            tstr = datetime.strptime(t, '%y/%m/%d %H:%M:%S.%f').strftime("%y-%m-%d %H:%M:%S") if has_time else "NULL"
            query = 'INSERT INTO capval (expr_id, time, value, round_id, sensor_id) VALUES (%d, "%s", %d, %d, %d);' % (expr_id, tstr, int(v, 16), i, j);
            mysql_send(cursor, query, log=True if i + j == 0 else False)
    assert type(query) is str
    
    cursor.close()
    cnx.commit()
    cnx.close()
