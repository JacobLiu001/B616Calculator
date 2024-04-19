import matplotlib.pyplot as plt

from b616.utils import plots
from b616.utils.data_handler import DataHandler


def main():
    # Set font library to support Chinese characters
    plt.rc("font", family=plots.get_available_fonts())

    maxlines = int(input("Please input the number of datapoints to analyse: "))
    data_handler = DataHandler.from_xlsx("scores.xlsx", maxlines=maxlines)

    plots.ptt_against_chartconstant(data_handler)
    plots.score_against_chartconstant(data_handler)

    plt.show()
