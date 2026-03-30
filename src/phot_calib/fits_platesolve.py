#!/usr/bin/env -S uv run --script

"""FITS_PLATESOLVE - Plate solve FITS images

creation : MAR 2026
"""

#
# --- IMPORTS -----------------------------------------------------------------
#

import argparse
from pathlib import Path
from tqdm.auto import tqdm

# FITS manipulation
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u

# Plotting
import matplotlib.pyplot as plt

import numpy as np

# eloy
from eloy import detection, viz
from twirl import compute_wcs, gaia_radecs
from twirl.geometry import sparsify

import contextlib
import os

# pipeline-specific imports
import sys

sys.path.append(str(Path(__file__).parents[2] / "setup"))
from telescopes import telescope_parameters  # type: ignore

#
# --- FUNCTIONS ---------------------------------------------------------------
#


@contextlib.contextmanager
def suppress_output():
    with (
        contextlib.redirect_stdout(open(os.devnull, "w")),
        contextlib.redirect_stderr(open(os.devnull, "w")),
    ):
        yield


def fits_platesolve(
    filenames, nstars=15, safe_mode=False, verbose=False, display=False
):
    """

    Parameters
    ----------

    Returns
    -------

    """
    file = filenames[len(filenames) // 2]
    with fits.open(file) as hdul:
        data = hdul[0].data
        header = hdul[0].header
        # get telescope specific params dict
        obsparam = telescope_parameters[f"{header["TELESCOP"]} {header["INSTRUME"]}"]
        # get pixel scale in degree
        pixel_scale = header[obsparam["binning"][0]] * obsparam["px_scale"] / 3600
        # size of the field-of-view
        fov = data.shape[1] * pixel_scale
        # RA/Dec coordinates of the image
        ra = header[obsparam["ra"]]
        dec = header[obsparam["dec"]]
        if obsparam["radec_separator"] == "XXX":
            center = SkyCoord(ra, dec, unit=("deg", "deg"))
        else:
            center = SkyCoord(ra, dec, unit=("h", "deg"))
        if verbose:
            print(f"Image center : {center.to_string('hmsdms')}")
        all_radecs = gaia_radecs(center, 1.5 * fov)
        # we only keep stars 0.01 degree apart from each other
        all_radecs = sparsify(all_radecs, 0.01)

    for file in tqdm(filenames, desc="Plate-solving ..."):
        if verbose:
            tqdm.write(f"Plate-solving {file} ...")
        with fits.open(file, mode="update") as hdul:
            # read image data and header
            data = hdul[0].data
            header = hdul[0].header

            if safe_mode:
                # get telescope specific params dict
                obsparam = telescope_parameters[
                    f"{header["TELESCOP"]} {header["INSTRUME"]}"
                ]
                # get pixel scale in degree
                pixel_scale = (
                    header[obsparam["binning"][0]] * obsparam["px_scale"] / 3600
                )
                # size of the field-of-view
                fov = data.shape[1] * pixel_scale
                # RA/Dec coordinates of the image
                ra = header[obsparam["ra"]]
                dec = header[obsparam["dec"]]
                if obsparam["radec_separator"] == "XXX":
                    center = SkyCoord(ra, dec, unit=("deg", "deg"))
                else:
                    center = SkyCoord(ra, dec, unit=("h", "deg"))
                if verbose:
                    tqdm.write(f"Image center : {center.to_string('hmsdms')}")
                all_radecs = gaia_radecs(center, 1.5 * fov)
                # we only keep stars 0.01 degree apart from each other
                all_radecs = sparsify(all_radecs, 0.01)

            # detect stars coordinates
            regions = detection.stars_detection(data, threshold=20, opening=2)
            regions = sorted(
                regions, key=lambda x: x.image_intensity.sum(), reverse=True
            )
            coords = np.array([r.centroid_weighted[::-1] for r in regions])[0:nstars]

            # compute WCS
            try:
                with suppress_output():
                    wcs = compute_wcs(coords, all_radecs[0:nstars], tolerance=10)
            except Exception as e:
                if verbose:
                    tqdm.write(f"Error occurred while plate-solving {file}: {e}")
                continue
            if wcs is None:
                if verbose:
                    tqdm.write(f"Plate-solving failed for {file}")
                continue

            # save as FITS
            hdul[0].header.update(wcs.to_header())
            hdul.flush()  # write changes to disk

            if display:
                # TODO : display the plate-solved image
                radecs_xy = np.array(wcs.world_to_pixel_values(all_radecs))[0:300]
                fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": wcs})
                ax.imshow(viz.z_scale(data), cmap="Greys_r", origin="lower")
                # Plot catalog stars
                viz.plot_marks(*radecs_xy.T, color="y")
                # Add coordinate grid
                ax.coords.grid(True, color="white", alpha=0.2, linestyle="--")
                fig.suptitle(file)
                ax.set_xlabel("RA")
                ax.set_ylabel("Dec")
                # Format tick labels
                ra = ax.coords["ra"]
                dec = ax.coords["dec"]
                ra.set_format_unit("hourangle")
                dec.set_format_unit("deg")
                ra.set_major_formatter("hh:mm:ss")
                dec.set_major_formatter("dd:mm:ss")
                # Tick spacing
                ra.set_ticks(spacing=1 * u.arcmin)
                dec.set_ticks(spacing=1 * u.arcmin)
                fig.tight_layout()
                plt.show()

            if verbose:
                tqdm.write("Plate-solving done")


#
# --- ARGS PARSER -------------------------------------------------------------
#
if __name__ == "__main__":
    # command line arguments
    parser = argparse.ArgumentParser(description="Trim fits images")

    parser.add_argument("filenames", help="list of fits files", nargs="+")
    parser.add_argument(
        "-n", "--nstars", help="Number of catalog stars to use", type=int, default=15
    )
    parser.add_argument(
        "-sm",
        "--safe_mode",
        help="Recompute the pixel scale, image center and get update gaia catalog for each images (safer but slower)",
        action="store_true",
    )
    parser.add_argument("-v", "--verbose", help="Verbose mode", action="store_true")
    parser.add_argument(
        "-d", "--display", help="Display plate-solved image", action="store_true"
    )

    args = parser.parse_args()

    filenames = sorted(args.filenames)
    nstars = args.nstars
    safe_mode = args.safe_mode
    verbose = args.verbose
    display = args.display

    #
    # --- SCRIPT CODE ---------------------------------------------------------
    #
    if ("*" in filenames[0]) or "?" in filenames[0]:
        filename = Path(filenames[0])
        filenames = sorted(Path(filename.parent).glob(filename.name))
    if len(filenames) == 0:
        print("No file found with the given pattern")
        exit(1)
    fits_platesolve(
        filenames, nstars=nstars, safe_mode=safe_mode, verbose=verbose, display=display
    )
