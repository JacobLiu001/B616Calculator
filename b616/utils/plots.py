import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from b616.utils.data_handler import DataHandler

_FONT_CANDIDATES = ["Arial", "Microsoft YaHei", "HeiTi TC"]


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
    x = data_handler.get_column("chart_constant")
    y = data_handler.get_column("ptt")
    titles = data_handler.get_column("title")

    fig, ax = plt.subplots()

    scatter = ax.scatter(x, y)
    ax.set_xlabel("Chart Constant")
    ax.set_ylabel("Song PTT")
    ax.set_title("PTT against Chart Constant")
    _add_hover_annotation(fig, ax, scatter, lambda ind: titles.iloc[ind])
    return fig


def score_against_chartconstant(data_handler: DataHandler):
    x = data_handler.get_column("chart_constant")
    y = data_handler.get_column("score")
    titles = data_handler.get_column("title")

    fig, ax = plt.subplots()

    scatter = ax.scatter(x, y)
    ax.set_xlabel("Chart Constant")
    ax.set_ylabel("Score")
    ax.set_title("Score against Chart Constant")
    _add_hover_annotation(fig, ax, scatter, lambda ind: titles.iloc[ind])
    return fig
