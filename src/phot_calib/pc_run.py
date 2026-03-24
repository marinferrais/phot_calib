#!/usr/bin/env -S uv run --script

"""PC_RUN - Calibration of astronomical images pipeline
            Rely on eloy (https://github.com/lgrcia/eloy) for the calibration.

creation : FEB 2026
"""

#
# --- IMPORTS -----------------------------------------------------------------
#

# Command line arguments parser
import argparse

import logging
from datetime import datetime
from pathlib import Path
from tqdm.auto import tqdm

from astropy.io import fits, ascii
from astropy.table import Table, unique
from astropy.time import Time
import warnings
from astropy.wcs import FITSFixedWarning

# eloy
from eloy import calibration, viz

# plot and videos
import matplotlib.pyplot as plt
import imageio.v2 as imageio
import io

# pipeline-specific imports
from fits_trim import fits_trim  # type: ignore
from fits_log import fits_log  # type: ignore
from fits_platesolve import fits_platesolve  # type: ignore

# wanings suppresion
warnings.simplefilter("ignore", FITSFixedWarning)

#
# --- FUNCTIONS ---------------------------------------------------------------
#


def setup_logger(log_dir: Path, name: str = "pipeline"):
    """
    Create a logger that logs to both console and a timestamped file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Remove all existing handlers
    if logger.hasHandlers():
        for h in logger.handlers[:]:
            logger.removeHandler(h)
            h.close()

    # Create log directory if needed
    log_dir.mkdir(parents=True, exist_ok=True)

    # Build timestamped filename
    timestamp = datetime.now().isoformat().replace(":", "-")
    logfile = log_dir / f"{timestamp}.log"

    # Handlers
    file_handler = logging.FileHandler(logfile)
    console_handler = logging.StreamHandler()

    file_handler.setLevel(logging.INFO)
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Attach handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging started -> {logfile}")

    return logger


def edit_header(header, n=None, mbias_file=None, mdark_file=None, mflat_file=None):
    """

    Parameters
    ----------

    Returns
    -------

    """
    typ_trans = {
        "Bias Frame": "BIAS",
        "Dark Frame": "DARK",
        "Flat Field": "FLAT",
        "Light Frame": "LIGHT",
    }
    header["IMAGETYP"] = typ_trans.get(header["IMAGETYP"], header["IMAGETYP"])
    if n:
        header["NCOMBINE"] = n
    if mbias_file:
        header["ZEROCOR"] = f"Master bias is {mbias_file}"
    if mdark_file:
        header["DARKCOR"] = f"Master dark is {mdark_file}"
    if mflat_file:
        header["FLATCOR"] = f"Master flat is {mflat_file}"
    return header


def update_mcalibs(t, file, header, obsparam):
    typ_trans = {
        "Bias Frame": "BIAS",
        "Dark Frame": "DARK",
        "Flat Field": "FLAT",
    }
    date_obs = header[obsparam["date_obs"]]
    jd_obs = Time(date_obs, format="isot").jd
    binning = header[obsparam["binning"][0]]
    typ = header[obsparam["image_type"]]
    typ = typ_trans.get(typ, typ)
    if typ == "FLAT":
        filter = header[obsparam["filter"]]
    else:
        filter = ""
    ccdtemp = header[obsparam["ccd_temp"]]
    naxis1 = header["NAXIS1"]
    naxis2 = header["NAXIS2"]
    new_row = [
        str(file),
        date_obs,
        jd_obs,
        binning,
        typ,
        filter,
        ccdtemp,
        naxis1,
        naxis2,
    ]
    if "readoutm" in obsparam.keys():
        readoutm = header[obsparam["readoutm"]]
        new_row.append(readoutm)
    t.add_row(new_row)
    t = unique(t, keys=("filename", "jd_obs"))
    t.sort("jd_obs")
    return t


def get_mcalib(t, typ, binning, date_obs, filter=None, readoutm=None):
    """

    Parameters
    ----------

    Returns
    -------

    """
    t_sel = t[(t["type"] == typ) & (t["bin"] == binning)]
    if filter is not None:
        t_sel = t_sel[t_sel["filter"] == filter]
    if readoutm is not None and "readoutm" in t_sel.colnames:
        t_sel = t_sel[t_sel["readoutm"] == readoutm]
    if len(t_sel) == 0:
        return None
    else:
        # Find the closest calibration file in time
        t_sel["time_diff"] = abs(t_sel["jd_obs"] - Time(date_obs, format="isot").jd)
        t_sel.sort("time_diff")
        if len(t_sel) == 0:
            return None
        else:
            return t_sel["filename"][0]


def make_mcalibs(traw, obsparam, logfile_mcalibs, dir_datacalib, nmin=5, display=False):
    """

    Parameters
    ----------
    traw : Table, required
        Table with data from only one binning mode and filter

    Returns
    -------

    """
    binning = traw["bin"][0]
    date_obs = traw["date_obs"][0].split("T")[0]
    if "readoutm" in traw.colnames:
        readoutm = traw["readoutm"][0]
    else:
        readoutm = None

    # get master calibs table
    if logfile_mcalibs.is_file():
        tmcalib = ascii.read(logfile_mcalibs, format="rst")
        tmcalib["filter"] = tmcalib["filter"].astype("U10")
    else:
        col_names = [
            "filename",
            "date_obs",
            "jd_obs",
            "bin",
            "type",
            "filter",
            "ccd_temp",
            "naxis1",
            "naxis2",
        ]
        dtypes = [
            "U200",
            "U30",
            "float64",
            "int64",
            "U10",
            "U10",
            "float64",
            "int64",
            "int64",
        ]
        if "readoutm" in obsparam.keys():
            col_names.append("readoutm")
            dtypes.append("U10")
        tmcalib = Table(names=col_names, dtype=dtypes)

    # get list of bias and dark files
    bias = traw[traw["type"] == "BIAS"]["filename"]
    darks = traw[traw["type"] == "DARK"]["filename"]

    # bias
    new_bias = False
    if len(bias) >= nmin:
        mbias = calibration.master_bias(files=bias)
        header = fits.getheader(bias[0])
        header = edit_header(header, n=len(bias))
        mbias_file = dir_datacalib / f"mbias_B{binning}.fits"
        fits.writeto(mbias_file, mbias, header, overwrite=True)
        tmcalib = update_mcalibs(tmcalib, mbias_file, header, obsparam)
        new_bias = True
    elif len(tmcalib[tmcalib["type"] == "BIAS"]) > 0:
        mbias_file = get_mcalib(tmcalib, "BIAS", binning, date_obs, readoutm=readoutm)
        if mbias_file is not None:
            mbias = fits.getdata(mbias_file)

    # dark
    new_dark = False
    if (len(darks) >= nmin) and (mbias_file is not None):
        try:
            mdark = calibration.master_dark(files=darks, bias=mbias)
        except UnboundLocalError:
            print("Error: master bias not found. Cannot build master dark.")
        header = fits.getheader(darks[0])
        header = edit_header(header, n=len(bias), mbias_file=mbias_file)
        mdark_file = dir_datacalib / f"mdark_B{binning}.fits"
        fits.writeto(mdark_file, mdark, header, overwrite=True)
        tmcalib = update_mcalibs(tmcalib, mdark_file, header, obsparam)
        new_dark = True
    elif len(tmcalib[tmcalib["type"] == "DARK"]) > 0:
        mdark_file = get_mcalib(tmcalib, "DARK", binning, date_obs, readoutm=readoutm)
        if mdark_file is not None:
            mdark = fits.getdata(mdark_file)

    # flat
    tflats = traw[traw["type"] == "FLAT"]
    mflats_list, filter_list = [], []
    for filter in set(tflats["filter"]):
        flats = tflats[tflats["filter"] == filter]["filename"]
        if len(flats) >= nmin:
            try:
                mflat = calibration.master_flat(files=flats, bias=mbias, dark=mdark)
            except UnboundLocalError:
                print(
                    "Error: master bias and/or dark not found. Cannot build master flat."
                )
                continue
            mflats_list.append(mflat)
            filter_list.append(filter)
            header = fits.getheader(flats[0])
            header = edit_header(
                header, n=len(bias), mbias_file=mbias_file, mdark_file=mdark_file
            )
            mflat_file = f"mflat_{header[obsparam['filter']]}_B{binning}.fits"
            mflat_file = dir_datacalib / mflat_file
            fits.writeto(mflat_file, mflat, header, overwrite=True)
            tmcalib = update_mcalibs(tmcalib, mflat_file, header, obsparam)

    # update master calibs log table
    tmcalib.write(logfile_mcalibs, format="ascii.rst", overwrite=True, comment=False)

    # Plot master calibs
    if display:
        ncols = 2 + len(mflats_list)
        fig, axes = plt.subplots(
            sharex=True, sharey=True, nrows=1, ncols=ncols, figsize=(18, 5)
        )
        if new_bias:
            axes[0].imshow(viz.z_scale(mbias), cmap="Greys_r", origin="lower")
        axes[0].set_title("bias")
        if new_dark:
            axes[1].imshow(viz.z_scale(mdark), cmap="Greys_r", origin="lower")
        axes[1].set_title("dark")
        for i, mflat in enumerate(mflats_list):
            axes[2 + i].imshow(viz.z_scale(mflat), cmap="Greys_r", origin="lower")
            axes[2 + i].set_title(f"flat {filter_list[i]}")
        fig.suptitle(f"{obsparam['observatory_name']} - {date_obs} - B{binning}")
        plt.tight_layout()
        plt.show()

    return tmcalib


def calibration_sequence(t, obsparam, logfile_mcalibs, dir_datacalib):
    """

    Parameters
    ----------

    Returns
    -------

    """
    # get science files
    lights = t["filename"]

    # get master calib log table
    tmcalib = ascii.read(logfile_mcalibs, format="rst")
    # select only master frame without filter or with same filter as sciences frames
    tmcalib = tmcalib[(tmcalib["filter"].mask) | (tmcalib["filter"] == t["filter"][0])]
    if "readoutm" in t.colnames:
        readoutm = t["readoutm"][0]
    else:
        readoutm = None
    mbias_file = get_mcalib(
        tmcalib, "BIAS", t["bin"][0], t["date_obs"][0], readoutm=readoutm
    )
    mdark_file = get_mcalib(
        tmcalib, "DARK", t["bin"][0], t["date_obs"][0], readoutm=readoutm
    )
    mflat_file = get_mcalib(
        tmcalib,
        "FLAT",
        t["bin"][0],
        t["date_obs"][0],
        filter=t["filter"][0],
        readoutm=readoutm,
    )
    mbias = fits.getdata(mbias_file)
    mdark = fits.getdata(mdark_file)
    mflat = fits.getdata(mflat_file)

    for file in tqdm(lights):
        data = fits.getdata(file)
        header = fits.getheader(file)
        exposure = header[obsparam["exptime"]]
        calib_data = calibration.calibrate(data, exposure, mdark, mflat, mbias)

        header = edit_header(
            header, mbias_file=mbias_file, mdark_file=mdark_file, mflat_file=mflat_file
        )
        calibname = f"{obsparam['observatory_abbrv']}_{header[obsparam['date_obs']][:-4].replace(':', '-')}_{header[obsparam['filter']]}.fits"
        calibname = dir_datacalib / calibname
        fits.writeto(calibname, calib_data, header, overwrite=True)


def write_plot(writer):
    """ """
    buf = io.BytesIO()
    plt.savefig(buf)
    writer.append_data(imageio.imread(buf))
    plt.close()


def make_video(t, obsparam, date_obs, dir_datacalib):
    """

    Parameters
    ----------

    Returns
    -------

    """
    outname = f"{obsparam['observatory_abbrv']}_{date_obs}.mp4"
    writer = imageio.get_writer(
        dir_datacalib / outname, mode="I", fps=5, format="FFMPEG"
    )

    for i, row in enumerate(tqdm(t)):
        data = fits.getdata(row["filename"])
        header = fits.getheader(row["filename"])
        fig, ax = plt.subplots()

        ax.imshow(viz.z_scale(data), cmap="Greys_r", origin="lower")

        ax.annotate(
            f"{row['object']} ({row['filter']})",
            xy=(0, 1),
            ha="left",
            va="top",
            xycoords="axes fraction",
            xytext=(1, -1),
            textcoords="offset points",
            fontsize=10,
            color="white",
        )
        ax.annotate(
            obsparam["observatory_name"],
            xy=(0, 0),
            ha="left",
            va="bottom",
            xycoords="axes fraction",
            xytext=(1, +1),
            textcoords="offset points",
            fontsize=10,
            color="white",
        )
        ax.annotate(
            f"{i + 1}/{len(t)} : {header[obsparam['date_obs']]}",
            xy=(1, 0),
            ha="right",
            va="bottom",
            xycoords="axes fraction",
            xytext=(-1, +1),
            textcoords="offset points",
            fontsize=10,
            color="white",
        )
        fig.tight_layout()

        write_plot(writer)

    writer.close()


def main(dir_dataraw, display=False, plate_solve=False, safe_mode=False):
    """

    Parameters
    ----------

    Returns
    -------

    """
    dir_datacalib = dir_dataraw.parent.parent / "datacalib" / dir_dataraw.name
    dir_datacalib.mkdir(parents=True, exist_ok=True)

    # start logs
    logger = setup_logger(dir_dataraw)

    # make logs of the raw data and get the telescope specific params dict
    traw, logfile_raw, obsparam, date_obs = fits_log(dir_dataraw)
    files = traw["filename"]  # list of file names
    _ = logger.info(f"Processing data in {dir_dataraw}")
    _ = logger.info(f"Raw data logged in {logfile_raw}")
    _ = logger.info(f"Date of observation: {date_obs}")
    _ = logger.info(f"Observatory: {obsparam['observatory_name']}")
    _ = logger.info(f"Telescope: {obsparam['telescope']}")
    _ = logger.info(f"Instrument: {obsparam['instrument']}")
    _ = logger.info(f"Found {len(files)} fits file in {dir_dataraw}")

    for binning in set(traw["bin"]):
        traw_b = traw[traw["bin"] == binning]
        len_bias = len(traw_b[traw_b["type"] == "BIAS"])
        len_dark = len(traw_b[traw_b["type"] == "DARK"])
        len_flat = len(traw_b[traw_b["type"] == "FLAT"])
        len_light = len(traw_b[traw_b["type"] == "LIGHT"])
        _ = logger.info(f"Files : {len_bias:3d}  BIAS     B{binning}")
        _ = logger.info(f"Files : {len_dark:3d}  DARK     B{binning}")
        _ = logger.info(f"Files : {len_flat:3d}  FLAT     B{binning}")
        _ = logger.info(f"Files : {len_light:3d}  LIGHT    B{binning}")
        traw_bf = traw_b[traw_b["type"] == "FLAT"]
        for filter in set(traw_bf["filter"]):
            len_flat = len(traw_bf[traw_bf["filter"] == filter])
            _ = logger.info(
                f"Files : {len_flat:3d} {' FLAT'.rjust(1)} {filter.rjust(3)} B{binning}"
            )
        traw_bl = traw_b[traw_b["type"] == "LIGHT"]
        for filter in set(traw_bl["filter"]):
            len_light = len(traw_bl[traw_bl["filter"] == filter])
            _ = logger.info(
                f"Files : {len_light:3d} {'LIGHT'.rjust(1)} "
                f"{filter.rjust(3)} B{binning}"
            )

    # trim images
    for binning in set(traw["bin"]):
        if f"trimB{binning}" in obsparam.keys():
            traw_b = traw[traw["bin"] == binning]
            for file in traw_b["filename"]:
                trim = obsparam[f"trimB{binning}"]
                fits_trim(file, trim, overwrite=True)
            _ = logger.info(f"Files B{binning} trimmed by: {trim}")

    # get master calibs log file
    logfile_mcalibs = f"{obsparam['observatory_abbrv']}_mcalibs.log"
    logfile_mcalibs = dir_dataraw.parents[1] / "datacalib" / logfile_mcalibs
    # make master frames
    if len(traw[traw["type"] != "LIGHT"]) == 0:
        _ = logger.info("No calibration frame to process")
    else:
        for binning in set(traw["bin"]):
            traw_b = traw[traw["bin"] == binning]
            logger.info(f"Building B{binning} master calibrations...")
            _ = make_mcalibs(
                traw_b,
                obsparam,
                logfile_mcalibs,
                dir_datacalib,
                nmin=5,
                display=display,
            )
        _ = logger.info(f"Master calibrations built and logged to {logfile_mcalibs}")

    # calibration
    tsci = traw[traw["type"] == "LIGHT"]
    for binning in set(tsci["bin"]):
        tsci_b = tsci[tsci["bin"] == binning]
        for filter in set(tsci_b["filter"]):
            tsci_bf = tsci_b[tsci_b["filter"] == filter]
            logger.info(f"Building calibrated images {filter} - B{binning} ...")
            _ = calibration_sequence(tsci_bf, obsparam, logfile_mcalibs, dir_datacalib)
    _ = logger.info(f"Image calibration done in {dir_datacalib}")

    # plate-solving
    if plate_solve:
        _ = logger.info("Plate-solving calibrated images...")
        fits_platesolve(
            tsci["filename"],
            nstars=15,
            safe_mode=safe_mode,
            verbose=False,
            display=False,
        )
        _ = logger.info("Plate-solving done")

    # make logs of the calibrated data
    _, logfile_sci, _, _ = fits_log(dir_datacalib)
    _ = logger.info(f"Calibrated data logged in {logfile_sci}")

    # make video of the calibrated images
    _ = logger.info("Making video of calibrated images")
    make_video(tsci, obsparam, date_obs, dir_datacalib)
    _ = logger.info("Video done")


#
# --- ARGS PARSER -------------------------------------------------------------
#
if __name__ == "__main__":
    # command line arguments
    parser = argparse.ArgumentParser(
        description="Calibration of astronomical images pipeline"
    )

    parser.add_argument(
        "listraw", help="File containing list of dates with raw data", type=str
    )
    parser.add_argument(
        "-d",
        "--display",
        help="Display cablibration master frames",
        action="store_true",
    )
    parser.add_argument(
        "-ps",
        "--plate_solve",
        help="Enable plate-solving of calibrated images",
        action="store_true",
    )
    parser.add_argument(
        "-sm",
        "--safe_mode",
        help="Recompute the pixel scale, image center and update gaia catalog for each images during plate-solving (safer but slower)",
        action="store_true",
    )

    args = parser.parse_args()

    listraw = Path(args.listraw).resolve()
    display = args.display
    plate_solve = args.plate_solve
    safe_mode = args.safe_mode

    #
    # --- SCRIPT CODE ---------------------------------------------------------
    #

    dir_dataraw_list = []
    with open(listraw, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            dir_dataraw_list.append(listraw.parent / line)

    for dir_dataraw in dir_dataraw_list:
        main(dir_dataraw, display=display, plate_solve=plate_solve, safe_mode=safe_mode)
