import pandas as pd

# As recommended by the pandas documentation, we enable copy-on-write mode
# This improves DataHandler's performance since it returns copies of the data
# We run this on package import.
pd.set_option("mode.copy_on_write", True)
