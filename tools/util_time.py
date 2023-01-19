def abstime2hr(time_seq):
    return [((t - time_seq[0]).total_seconds() / 3600) for t in time_seq]

