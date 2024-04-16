import numpy as np

_THRESHOLDS = {
    "score": [9_500_000 - 12 * 300_000, 9_500_000, 9_800_000, 10_000_000],
    "ptt_delta": [-12, 0, 1, 2],
}


def get_score_thresholds():
    return _THRESHOLDS["score"]


def get_ptt_delta(score):
    return np.interp(score, _THRESHOLDS["score"], _THRESHOLDS["ptt_delta"])


def get_score(ptt_delta):
    # NOTE: will never return a score less than 9_500_000 - 12 * 300_000 == 5_900_000
    return np.interp(ptt_delta, _THRESHOLDS["ptt_delta"], _THRESHOLDS["score"])
