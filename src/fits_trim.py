#!/usr/bin/env python3

"""FITS_TRIM - Trim fits images

creation : FEB 2026
"""

#
# --- IMPORTS -----------------------------------------------------------------
#

# Command line arguments parser
import argparse

# Filesytem paths
from pathlib import Path

# FITS manipulation
from astropy.io import fits

# Plotting
import matplotlib.pyplot as plt


# Image vizualization
from src.image_scaling import z_scale

#
# --- FUNCTIONS ---------------------------------------------------------------
#


def fits_trim(file, trim, overwrite=False, verbose=False, display=False):
    """Trim fits images

    Parameters
    ----------
    file : {str, pathlib.PosixPath}, required
        Path to the fits file.
    trim : list, required
        List with for element containing the slicing indexes

    Returns
    -------

    """
    if len(trim) == 1:
        trim = [trim[0], -trim[0], trim[0], -trim[0]]
    elif len(trim) == 4:
        trim = [trim[0], -trim[1], trim[2], -trim[3]]
    else:
        raise ValueError(f"Trim must have 1 or 4 values : {trim}")
    file = Path(file)
    data = fits.getdata(file)
    header = fits.getheader(file)
    if "TRIM" in header.keys():
        if verbose:
            print(f"File already trimmed to {trim} : {file}")
        return
    header["TRIM"] = f"Trim is {trim}"
    if trim[1] == 0:
        trim[1] = data.shape[1] + 1
    if trim[3] == 0:
        trim[3] = data.shape[0] + 1
    datat = data[trim[2] : trim[3], trim[0] : trim[1]]
    if verbose:
        print(f"> Trimming : {file}")
        print(f"> Trim : {trim}")
        print(f"> Shape before : {data.shape}")
        print(f"> Shape after  : {datat.shape}")
    if display:
        fig, axes = plt.subplots(ncols=2, figsize=(12, 6))
        axes[0].imshow(z_scale(data), cmap="Greys_r")  # , origin="lower")
        axes[0].set_title("original")
        axes[1].imshow(z_scale(datat), cmap="Greys_r")  # , origin="lower")
        axes[1].set_title("trimmed")
        plt.tight_layout()
        plt.show()
    for i in range(2):
        if trim[(2 * i) + 1] < 0:
            trim[(2 * i) + 1] = data.shape[i - 1] + trim[(2 * i) + 1] + 1
    trim_ds = f"[{trim[0] + 1}:{trim[1] - 1},{trim[2] + 1}:{trim[3] - 1}]"
    header["TRIMDS"] = f"Trim data section is {trim_ds}"
    if not overwrite:
        header["OLDNAME"] = str(file)
        file = file.with_stem(file.stem + "_trim")
    if verbose:
        print(f"> Writing trimmed file to : {file}")
    fits.writeto(file, datat, header, overwrite=True)
    return


#
# --- ARGS PARSER -------------------------------------------------------------
#
if __name__ == "__main__":
    # command line arguments
    parser = argparse.ArgumentParser(description="Trim fits images")

    parser.add_argument("filenames", help="list of fits files", nargs="+")
    parser.add_argument("-t", "--trim", help="Trim value. ", type=int, nargs="+")
    parser.add_argument(
        "-o",
        "--overwrite",
        help="Overwrite fits files, else add _trim to file name",
        action="store_true",
    )
    parser.add_argument("-v", "--verbose", help="Verbose mode", action="store_true")
    parser.add_argument(
        "-d", "--display", help="Display trimmed image", action="store_true"
    )

    args = parser.parse_args()

    filenames = sorted(args.filenames)
    trim = args.trim
    overwrite = args.overwrite
    verbose = args.verbose
    display = args.display

    #
    # --- SCRIPT CODE ---------------------------------------------------------
    #
    for file in filenames:
        fits_trim(file, trim, overwrite=overwrite, verbose=verbose, display=display)
