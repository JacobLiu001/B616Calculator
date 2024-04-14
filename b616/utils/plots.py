import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm
from matplotlib import colors

from b616.utils.data_handler import DataHandler
from b616.utils.arcaea_ptt import get_ptt_delta

_FONT_CANDIDATES = ["Arial", "Microsoft YaHei", "HeiTi TC"]
_SCORE_THRESHOLDS_NAMES: list[tuple[str, int]] = [
    ("PM", 10_000_000),
    ("EX+", 9_900_000),
    ("EX", 9_800_000),
    ("AA", 9_500_000),
    ("A", 9_200_000),
]

_score_colormap = plt.cm.get_cmap("plasma_r")
_score_norm = colors.Normalize(vmin=9_500_000, vmax=10_000_000, clip=True)
_score_scalarmappable = plt.cm.ScalarMappable(norm=_score_norm, cmap=_score_colormap)


def get_available_fonts():
    available_fonts = set(fm.get_font_names())

    usefonts = [font for font in _FONT_CANDIDATES if font in available_fonts]
    usefonts.append("sans-serif")

    return usefonts


def _add_hover_annotation(fig, ax, artist, text_from_ind):
    def hover(event):
        if event.inaxes != ax:
            return
        cont, ind = artist.contains(event)
        if not cont:
            hover_annotation.set_visible(False)
            fig.canvas.draw_idle()
            return
        ind = ind["ind"][0]
        x, y = artist.get_offsets()[ind]
        hover_annotation.xy = (x, y)
        hover_annotation.set_text(text_from_ind(ind))
        hover_annotation.set_visible(True)
        fig.canvas.draw_idle()

    hover_annotation = ax.annotate(
        "",
        xy=(0, 0),
        xytext=(10, 10),
        textcoords="offset points",
        bbox={"fc": "w"},
        arrowprops={"arrowstyle": "->"},
        visible=False,
    )
    fig.canvas.mpl_connect("motion_notify_event", hover)


def ptt_against_chartconstant(data_handler: DataHandler):
    x = data_handler.data["chart_constant"]
    y = data_handler.data["ptt"]
    titles = data_handler.data["title"]
    scores = data_handler.data["score"]

    fig, ax = plt.subplots()

    scatter = ax.scatter(x, y, s=15, c=_score_norm(scores), cmap=_score_colormap)
    fig.draw_without_rendering()
    ax.autoscale(False)  # Fix the axes so that the line can be drawn

    line_x = np.array([0, 15])
    min_score = scores.min()
    for threshold_name, threshold in _SCORE_THRESHOLDS_NAMES:
        line_y = get_ptt_delta(threshold) + line_x
        ax.plot(
            line_x,
            line_y,
            label=f"{threshold_name}",
            linestyle="--",
            linewidth=1,
            alpha=0.3,
            color=_score_colormap(_score_norm(threshold)),
        )

        if min_score > threshold:
            break

    ax.set_xlabel("Chart Constant")
    ax.xaxis.set_minor_locator(plt.MultipleLocator(0.1))
    ax.xaxis.set_major_locator(plt.MultipleLocator(0.2))
    ax.set_ylabel("Song PTT")
    ax.set_title("PTT against Chart Constant")
    ax.legend()
    fig.colorbar(_score_scalarmappable, ax=ax, extend="both")
    # _add_hover_annotation(fig, ax, scatter, lambda ind: titles.iloc[ind])
    return fig


def score_against_chartconstant(data_handler: DataHandler):
    x = data_handler.data["chart_constant"]
    y = data_handler.data["score"]
    titles = data_handler.data["title"]

    fig, ax = plt.subplots()

    scatter = ax.scatter(x, y)
    ax.set_xlabel("Chart Constant")
    ax.set_ylabel("Score")
    ax.set_title("Score against Chart Constant")
    _add_hover_annotation(fig, ax, scatter, lambda ind: titles.iloc[ind])
    return fig
