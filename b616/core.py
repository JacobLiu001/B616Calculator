import matplotlib.pyplot as plt
import pandas as pd

from b616.utils import plots
from b616.utils.data_handler import DataHandler

# As recommended by the pandas documentation, we enable copy-on-write mode
# This improves DataHandler's performance since it returns copies of the data
pd.set_option("mode.copy_on_write", True)


def main():
    # Set font library to support Chinese characters
    plt.rc("font", family=plots.get_available_fonts())

    maxlines = int(input("Please input the number of datapoints to analyse: "))
    data_handler = DataHandler.from_xlsx("scores.xlsx", maxlines=maxlines)

    plots.ptt_against_chartconstant(data_handler)
    plots.score_against_chartconstant(data_handler)

    plt.show()
