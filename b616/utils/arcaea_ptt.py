import numpy as np

_THRESHOLDS = {
    "score": [0, 9_500_000, 9_800_000, 10_000_000],
    "ptt_delta": [-9_500_000 / 300_000, 0, 1, 2],
}


def get_score_thresholds():
    return _THRESHOLDS["score"]


def get_ptt_delta(score):
    return np.interp(score, _THRESHOLDS["score"], _THRESHOLDS["ptt_delta"])


def get_score(ptt_delta):
    return np.interp(ptt_delta, _THRESHOLDS["ptt_delta"], _THRESHOLDS["score"])
