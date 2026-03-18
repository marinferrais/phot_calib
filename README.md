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

0. Add you telescope in setup/telescopes.py if needed:

1. Raw data structure example:
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
#2026-03-02
2026-03-03
#2026-03-05
2026-03-07
```

3. Run the pipeline (adapt '/path_to' to your case):
```bash
uv run --project /path_to/phot_calib /path_to/phot_calib/src/phot_calib/pc_run.py listraw.txt
```

or, on linux, add this to your .bashrc (adapt '/path_to' to your case):
```text
export PATH=$PATH:/path_to/src/phot_calib
export PYTHONPATH="${PYTHONPATH}:/path_to/src/phot_calib"
alias pc_run='uv run --project /path_to/phot_calib/ pc_run.py'
```
and run with:
```bash
pc_run.py listraw.txt
```

Your directory will then look like that:
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
    ├── 2026-03-09
    ├── MO_2026.log
    └── MO_mcalibs.log
```
The calibrated are in datacalib and where dataraw/MO_2026.log are logs of the raw data, datacalib/MO_2026.log the logs of the calibrated data, and datacalib/MO_mcalibs.log the logs of the master calibration frames.