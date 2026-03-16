#!/usr/bin/env python3

"""LOG_IMAGES - Create a log of FITS images.

creation : Feb 2026
"""

#
# --- IMPORTS -----------------------------------------------------------------
#

# Command line arguments parser
import argparse

# Filesytem paths
from pathlib import Path

# FITS, table and time
from astropy.io import fits, ascii
from astropy.table import Table, vstack, unique
from astropy.time import Time

# for nan handling
import numpy as np

# pipeline-specific imports
import sys

sys.path.append(str(Path(__file__).parents[2] / "setup"))
from telescopes import telescope_parameters  # type: ignore

#
# --- FUNCTIONS ---------------------------------------------------------------
#


def get_date(date_isot):
    """
    Get date of observation from the header DATE-OBS. Return the day before if
    the observation started after midnight.
    """
    jd_obs = Time(date_isot, format="isot").jd
    jd_obs = int(jd_obs) - 0.3
    date_obs = Time(jd_obs, format="jd").isot
    return date_obs.split("T")[0]


def fits_log(dir_data: Path, verbose=False):
    """
    Create a log of the data containing the file names, obs date, binning,
    image type, exptime, filter, ra, dec, airmass, ccd temperature, image size,
    and side of pier.

    Parameters
    ----------
    dir_data : {str, pathlib.PosixPath}, required
        Directory containing the FITS images.

    Returns
    -------
    t : Table
        Astropy Table with the data logs.
    """

    inst_trans = {
        "ASI Camera (2)": "ZWO ASI2600MM Pro",  # Fix for RO with MDL
    }

    typ_trans = {
        "Bias Frame": "BIAS",
        "Dark Frame": "DARK",
        "Flat Field": "FLAT",
        "Light Frame": "LIGHT",
        "EXPOSE": "LIGHT",
    }

    # get fits file names
    dir_data = Path(dir_data)
    files = []
    suffix_list = [".fits", ".fts", "fit"]
    for suffix in suffix_list:
        files.extend(dir_data.rglob(f"*{suffix}"))

    if len(files) == 0:
        raise ValueError(f"No data found in {dir_data} with suffixes {suffix_list}")

    # get telescope and instrument from 1st file
    header = fits.getheader(files[0])
    telescope = header["TELESCOP"]
    instrument = header["INSTRUME"]
    instrument = inst_trans.get(instrument, instrument)
    # get telescope specific params dict
    obsparam = telescope_parameters[f"{telescope} {instrument}"]
    date = get_date(header[obsparam["date_obs"]])
    if "readoutm" in obsparam.keys():
        readoutm = header[obsparam["readoutm"]]

    # define lists to fill
    date_obs, object, bin, typ, exptime, ccd_temp = [], [], [], [], [], []
    filter, ra, dec, airmass = [], [], [], []
    naxis1, naxis2, pierside = [], [], []

    for file in files:
        header = fits.getheader(file)

        # check for unique telescope, instrument, date obs, and readout mode
        date_i = get_date(header[obsparam["date_obs"]])
        iinstrument = header["INSTRUME"]
        iinstrument = inst_trans.get(iinstrument, iinstrument)
        if (header["TELESCOP"] != telescope) & (header["TELESCOP"] != ""):
            raise ValueError(
                f"Multiple telescope detected : {telescope}, {header['TELESCOP']} ..."
            )
        elif iinstrument != instrument:
            raise ValueError(
                f"Multiple instrument detected : {instrument}, {iinstrument} ..."
            )
        elif date != date_i:
            raise ValueError(f"Multiple date detected : {date}, {date_i} ...")
        if "readoutm" in obsparam.keys():
            readoutm_i = header[obsparam["readoutm"]]
            if readoutm != readoutm_i:
                raise ValueError(
                    f"Multiple readout mode detected : {readoutm}, {readoutm_i} ..."
                )

        date_obs.append(header[obsparam["date_obs"]])
        if obsparam["object"] in header.keys():
            object.append(header[obsparam["object"]])
        else:
            object.append("")
        bin.append(header[obsparam["binning"][0]])
        ityp = header[obsparam["image_type"]]
        typ.append(typ_trans.get(ityp, ityp))
        exptime.append(header[obsparam["exptime"]])
        if typ[-1] in ["LIGHT", "FLAT"]:
            filter.append(header[obsparam["filter"]])
        else:
            filter.append("")
        if obsparam["ra"] in header.keys():
            ra.append(header[obsparam["ra"]])
        else:
            ra.append(np.nan)
        if obsparam["dec"] in header.keys():
            dec.append(header[obsparam["dec"]])
        else:
            dec.append(np.nan)
        if obsparam["airmass"] in header.keys():
            airmass.append(header[obsparam["airmass"]])
        else:
            airmass.append(np.nan)
        ccd_temp.append(header[obsparam["ccd_temp"]])
        naxis1.append(header[obsparam["extent"][0]])
        naxis2.append(header[obsparam["extent"][1]])
        if "PIERSIDE" in header.keys():
            pierside.append(header["PIERSIDE"])

    t = Table()
    t["filename"] = files
    t["date_obs"] = date_obs
    t["jd_obs"] = [Time(date, format="isot").jd for date in date_obs]
    t["object"] = object
    t["bin"] = bin
    t["type"] = typ
    t["exptime"] = exptime
    t["filter"] = filter
    t["ra"] = ra
    t["dec"] = dec
    t["airmass"] = airmass
    t["ccd_temp"] = ccd_temp
    t["naxis1"] = naxis1
    t["naxis2"] = naxis2
    t["pierside"] = pierside
    if "readoutm" in obsparam.keys():
        t["readoutm"] = [readoutm] * len(t)
    # fixing string length
    t["filename"] = t["filename"].astype("U200")
    t["object"] = t["object"].astype("U20")
    t["filter"] = t["filter"].astype("U10")

    # sort chronologicaly
    t.sort("jd_obs")

    logfile = f"{obsparam['observatory_abbrv']}_{date}.log"
    logfile = dir_data / logfile
    if verbose:
        print(f"> Writing data logs to : {logfile}")
    t.write(logfile, format="ascii.rst", overwrite=True, comment=False)

    # make log of all files
    logfile_all = logfile.parents[1] / f"{obsparam['observatory_abbrv']}_{date[:4]}.log"
    if logfile_all.is_file():
        tall = ascii.read(logfile_all, format="rst")
        tall["filename"] = tall["filename"].astype("U200")
        tall["object"] = tall["object"].astype("U20")
        tall["filter"] = tall["filter"].astype("U10")
        tall = vstack([tall, t])
        tall = unique(tall, keys=("filename", "jd_obs"))
        tall.sort("jd_obs")
        tall.write(logfile_all, format="ascii.rst", overwrite=True, comment=False)
    else:
        t.write(logfile_all, format="ascii.rst", overwrite=True, comment=False)

    return t, logfile, obsparam, date


#
# --- ARGS PARSER -------------------------------------------------------------
#
if __name__ == "__main__":
    # command line arguments
    parser = argparse.ArgumentParser(
        description="Create a log of images before calibration"
    )

    parser.add_argument("dir_data", help="Directory containing the images", type=str)
    parser.add_argument("-t", "--verbose", help="Verbose mode", action="store_true")
    parser.add_argument("-v", "--verbose", help="Verbose mode", action="store_true")

    args = parser.parse_args()

    #
    # --- SCRIPT CODE ---------------------------------------------------------
    #

    t, logfile, obsparam = fits_log(args.dir_data, verbose=args.verbose)
