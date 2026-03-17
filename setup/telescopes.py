trappist_south_param = {
    "telescope": "TRAPPIST",  # telescope keyword
    "instrument": "FLI-New",  # instrument keyword
    "observatory_name": "TRAPPIST-South",  # observatory denomination
    "observatory_code": "I40",  # MPC observatory code
    "observatory_abbrv": "TS",  # observatory abbreviation
    "image_type": "IMAGETYP",  # image type kw
    "trimB1": [16, 32, 24, 0],  # image trim B1 [x1,x2,y1,y2]
    "trimB2": [8, 16, 11, 0],  # image trim B2 [x1,x2,y1,y2]
    "saturated": 52000,  # saturation level in ADU
    "px_scale": 0.64,  # pixel size (arcsec) in binning 1x1
    "binning": ("XBINNING", "YBINNING"),
    # binning in x/y, '_blankN' denotes that both axes
    # are listed in one keyword, sep. by blanks
    "extent": ("NAXIS1", "NAXIS2"),  # N_pixels in x/y
    "ra": "RA",  # telescope pointing, RA
    "dec": "DEC",  # telescope pointin, Dec
    "radec_separator": " ",  # RA/Dec hms separator, use 'XXX' if already in degrees
    "date_obs": "DATE-OBS",  # obs date/time keyword
    "object": "OBJECT",  # object name keyword
    "filter": "FILTER",  # filter keyword
    "exptime": "EXPTIME",  # exposure time keyword (s)
    "airmass": "AIRMASS",  # airmass keyword
    "ccd_temp": "CCD-TEMP",  # ccd temperatrue keyword
    "readoutm": "READOUTM",  # readout mode kw
}


trappist_north_param = {
    "telescope": "ACP->NTM",  # telescope keyword
    "instrument": "Andor Tech",  # instrument keyword
    "observatory_name": "TRAPPIST-North",  # observatory denomination
    "observatory_code": "Z53",  # MPC observatory code
    "observatory_abbrv": "TN",  # observatory abbreviation
    "image_type": "IMAGETYP",  # image type kw
    "trimB1": [3, 0, 21, 21],  # image trim B1 [x1,x2,y1,y2]
    "trimB2": [1, 0, 10, 11],  # image trim B2 [x1,x2,y1,y2]
    "saturated": 52000,  # saturation level in ADU
    "px_scale": 0.60,  # pixel size (arcsec) in binning 1x1
    "binning": ("XBINNING", "YBINNING"),
    # binning in x/y, '_blankN' denotes that both axes
    # are listed in one keyword, sep. by blanks
    "extent": ("NAXIS1", "NAXIS2"),  # N_pixels in x/y
    "ra": "RA",  # telescope pointing, RA
    "dec": "DEC",  # telescope pointin, Dec
    "radec_separator": " ",  # RA/Dec hms separator, use 'XXX' if already in degrees
    "date_obs": "DATE-OBS",  # obs date/time keyword
    "object": "OBJECT",  # object name keyword
    "filter": "FILTER",  # filter keyword
    "exptime": "EXPTIME",  # exposure time keyword (s)
    "airmass": "AIRMASS",  # airmass keyword
    "ccd_temp": "CCD-TEMP",  # ccd temperatrue keyword
}


robinson_param = {
    "telescope": "RCOS",  # telescope keyword
    "instrument": "ZWO ASI2600MM Pro",  # instrument keyword
    "observatory_name": "Robinson Observatory",  # observatory denomination
    "observatory_code": "W39",  # MPC observatory code
    "observatory_abbrv": "RO",  # observatory abbreviation
    "image_type": "IMAGETYP",  # image type kw
    #'trim' : [11,1034,1,1024], # image trim (python indexing), to not trim use None
    "px_scale": 0.186,  # pixel size (arcsec) in binning 1x1
    "saturated": 52000,  # saturation level in ADU
    "binning": ("XBINNING", "YBINNING"),
    # binning in x/y, '_blankN' denotes that both axes
    # are listed in one keyword, sep. by blanks
    "extent": ("NAXIS1", "NAXIS2"),  # N_pixels in x/y
    "ra": "RA",  # telescope pointing, RA
    "dec": "DEC",  # telescope pointin, Dec
    "radec_separator": "XXX",  # RA/Dec hms separator, use 'XXX' if already in degrees
    "date_obs": "DATE-OBS",  # obs date/time keyword
    "object": "OBJECT",  # object name keyword
    "filter": "FILTER",  # filter keyword
    "exptime": "EXPTIME",  # exposure time keyword (s)
    "airmass": "AIRMASS",  # airmass keyword
    "ccd_temp": "CCD-TEMP",  # ccd temperatrue keyword
}

#
telescope_parameters = {
    "TRAPPIST FLI-New": trappist_south_param,
    "ACP->NTM Andor Tech": trappist_north_param,
    " Andor Tech": trappist_north_param,  # TN calibs frame have empty telescope kw
    "RCOS ZWO ASI2600MM Pro": robinson_param,
}
