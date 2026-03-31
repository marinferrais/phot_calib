# phot_calib

Calibration of astronomical images pipeline

----

Pipeline to automatically calibrate astronomical images.
Rely on [eloy](https://github.com/lgrcia/eloy) for the calibration part.


## Installation

### Prerequisites
-  Python package and project manager: [uv](https://docs.astral.sh/uv/getting-started/installation/)
```bash
pip install uv
```

### Steps

1. Clone the repository:
```bash
git clone https://github.com/marinferrais/phot_calib
cd phot_calib
```

2. Install dependencies:
```bash
uv sync
```

## Usage

0. Add your telescope setings in setup/telescopes.py if needed:

1. Raw data structure example for a telescope named myobservatory (MO):
```text
myobservatory/
├── dataraw
│   ├── 2026-03-04
│   ├── 2026-03-06
│   ├── 2026-03-07
│   ├── 2026-03-09
│   ├── listraw.txt
└── datacalib
```

2. listraw.txt contains the dates to process (lines starting with # are ignored):

```text
2026-03-04
2026-03-06
2026-03-07
#2026-03-09
```

3. Run the pipeline (change <path_to> to where phot_calib is installed):
```bash
uv run --project <path_to>/phot_calib <path_to>/phot_calib/src/phot_calib/pc_run.py listraw.txt
```

or, on linux, add this to your .bashrc (change <path_to> to where phot_calib is installed):
```text
export PATH=$PATH:<path_to>/src/phot_calib
export PYTHONPATH="${PYTHONPATH}:<path_to>/src/phot_calib"
alias pc_run='uv run --project <path_to>/phot_calib/ pc_run.py'
```
and run with:
```bash
pc_run listraw.txt
```

The directory will then look like that:
```text
myobservatory/
├── dataraw
│   ├── 2026-03-04
│   ├── 2026-03-06
│   ├── 2026-03-07
│   ├── 2026-03-09
│   ├── listraw.txt
│   └── MO_2026.log
└── datacalib
    ├── 2026-03-04
    ├── 2026-03-06
    ├── 2026-03-07
    ├── MO_2026.log
    └── MO_mcalibs.log
```
The calibrated are in datacalib and where dataraw/MO_2026.log are logs of the raw data, datacalib/MO_2026.log the logs of the calibrated data, and datacalib/MO_mcalibs.log the logs of the master calibration frames.

Options:
```text
  -d, --display       Display cablibration master frames
  -ps, --plate_solve  Enable plate-solving of calibrated images
  -sm, --safe_mode    Recompute the pixel scale, image center and update gaia catalog for each images during plate-solving (safer but slower)
```