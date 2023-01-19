def mask_with0(symbols, nbit):
    assert type(symbols) is list
    mask = ~(1 << nbit)
    if type(symbols[0]) is str:
        return [hex(int(x,16) & mask)[2:] for x in symbols]
    elif type(symbols[0]) is int:
        return [(x & mask) for x in symbols]

def mask_closeto(symbols, nbit, value=0):
    assert type(symbols) is list
    assert type(symbols[0]) is int
    mask_oh = 1 << nbit[0]
    list_dn = [(x & ~mask_oh) for x in symbols]
    list_up = [(x |  mask_oh) for x in symbols]
    return [u if abs(value-u) < abs(value-d) else d for u, d in zip(list_up, list_dn)]
