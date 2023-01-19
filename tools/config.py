import argparse

def get_parser():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('csv_name', type=str, default=None)
    parser.add_argument('--time-fname', type=str, default=None)
    parser.add_argument('--pixel-roi', nargs='+', type=int, default=list(range(25)))
    parser.add_argument('--lmin', type=int, default=0)
    parser.add_argument('--lmax', type=int, default=1000)
    parser.add_argument('--denoise-lsb', type=int, default=32)
    parser.add_argument('--denoise-lsb-temp', type=int, default=32)
    parser.add_argument('--outlier-tol', type=float, default=None)
    parser.add_argument('--mask-bits', type=int, nargs='+', default=[])
    parser.add_argument('--cap-noylim', action='store_true')
    parser.add_argument('--show-repl-symb', action='store_true')
    parser.add_argument('--show-zero-symb', action='store_true')
    parser.add_argument('--show-noisy-symb', action='store_true')
    parser.add_argument('--show-outlier-symb', action='store_true')
    parser.add_argument('--show-bad-endsymb', action='store_true')
    parser.add_argument('--value-ref', action='store_true')
    parser.add_argument('--time-ref', action='store_true')
    parser.add_argument('--no-ref', action='store_true')
    parser.add_argument('--time-ref-time', type=int, default=30)

    args = parser.parse_args()

    return args
