import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.font_manager as fm
from matplotlib import colors
from matplotlib.widgets import Button

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

# Prevent the garbage collector from collecting the objects
# This is necessary because Matplotlib widgets need to be kept alive by the user
_keepalive: list = []

# colormap
_score_colormap = plt.cm.get_cmap("plasma_r")
_score_norm = colors.Normalize(vmin=9_500_000, vmax=10_000_000, clip=True)
_score_scalarmappable = plt.cm.ScalarMappable(norm=_score_norm, cmap=_score_colormap)


def get_available_fonts():
    available_fonts = set(fm.get_font_names())

    usefonts = [font for font in _FONT_CANDIDATES if font in available_fonts]
    usefonts.append("sans-serif")

    return usefonts


def add_toggleable_annotations(xs, ys, texts, fig, ax, artist):
    DEFAULT_OFFSET = (5, 0)
    annotations_by_x = dict()  # map x to list of annotations
    all_annotations = []  # flat list of all annotations, for indexing when toggling
    for x, y, text in zip(xs, ys, texts):
        annotation = ax.annotate(
            text,
            (x, y),
            textcoords="offset pixels",
            xytext=DEFAULT_OFFSET,
            horizontalalignment="left",
            verticalalignment="baseline",
            fontsize=8,
            color="black",
            bbox={"facecolor": "white", "alpha": 0.2, "edgecolor": "none", "pad": 1},
        )
        annotations_by_x.setdefault(x, []).append(annotation)
        all_annotations.append(annotation)

    def adjust_positions():
        fig.draw_without_rendering()
        for annotations in annotations_by_x.values():
            # Annotations are already sorted by y, because the data is sorted by PTT
            # So for any given chart constant, scores are in descending order
            for annotation, prev_annotation in zip(annotations[1:], annotations[:-1]):
                annotation.set_position(DEFAULT_OFFSET)
                bbox = annotation.get_window_extent()
                this_y_top = bbox.bounds[1] + bbox.bounds[3]
                prev_y = prev_annotation.get_tightbbox().bounds[1]

                if this_y_top > prev_y:
                    delta = this_y_top - prev_y
                    xtext, ytext = annotation.get_position()
                    annotation.set_position((xtext, ytext - delta - 5))
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("resize_event", lambda _: adjust_positions())
    ax.callbacks.connect("ylim_changed", lambda _: adjust_positions())

    def set_all_visibility(visible):
        for annotation in all_annotations:
            annotation.set_visible(visible)
        fig.canvas.draw_idle()

    ax_select_all = fig.add_axes([0.65, 0.01, 0.14, 0.05])
    button_show_all = Button(ax_select_all, "Show All")
    button_show_all.on_clicked(lambda _: set_all_visibility(True))
    ax_deselect_all = fig.add_axes([0.8, 0.01, 0.14, 0.05])
    button_hide_all = Button(ax_deselect_all, "Hide All")
    button_hide_all.on_clicked(lambda _: set_all_visibility(False))
    # Keep the buttons alive so that they are not garbage collected
    _keepalive.extend([button_show_all, button_hide_all])

    artist.set_picker(5)

    def on_pick(event):
        ind = event.ind[0]
        visibility = not all_annotations[ind].get_visible()
        all_annotations[ind].set_visible(visibility)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("pick_event", on_pick)


def ptt_against_chartconstant(data_handler: DataHandler):
    x = data_handler.data["chart_constant"]
    y = data_handler.data["ptt"]
    titles = data_handler.data["title"]
    scores = data_handler.data["score"]

    fig, ax = plt.subplots()

    scatter = ax.scatter(x, y, s=15, c=_score_norm(scores), cmap=_score_colormap)

    # Draw the PTT lines for each score threshold
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

    add_toggleable_annotations(x, y, titles, fig, ax, scatter)
    return fig


def score_against_chartconstant(data_handler: DataHandler):
    x = data_handler.data["chart_constant"]
    y = data_handler.data["score"]
    titles = data_handler.data["title"]
    scores = data_handler.data["score"]

    fig, ax = plt.subplots()

    scatter = ax.scatter(x, y, s=15, c=_score_norm(scores), cmap=_score_colormap)
    ax.set_xlabel("Chart Constant")
    ax.set_ylabel("Score")
    ax.set_title("Score against Chart Constant")

    add_toggleable_annotations(x, y, titles, fig, ax, scatter)
    return fig
