__version__ = "0.1.0"
__author__ = "Matt Jaquiery"
__email__ = "matt.jaquiery@dtc.ox.ac.uk"
__url__ = "https://github.com/OxfordRSE/trd-cli"
__description__ = "A command line interface for converting True Colours data for REDCap import."

import sys


# Check for a minimum Python version
if sys.version_info < (3, 9):
    raise RuntimeError("This package requires Python 3.8 or higher.")
