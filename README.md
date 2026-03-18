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
├── dataraw/
│   ├── 2026-03-02/
│   ├── 2026-03-03/
│   ├── 2026-03-05/
│   ├── 2026-03-07/
│   └── listraw.txt
└── datacalib/
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