# NHAMCS Hypertension

## The NHAMCS Survey

The National Health Ambulatory Medical Care Survey (NHMACS) is an annual
national dataset representative of ED visits and resulting hospitalization.
Each year the National Center for Health Statistics develops the NHAMCS
data collection form. Trained staff then abstract data from patient charts.
Using a multi-stage probability sampling design, the dataset captures a
representative sample of ALL visits to non-federal hospitals in the United
States (US).

## Hypertension

Hypertension is independently identifed as a risk factor for cardiovascular
disease. Furthermore, acute hypertension can cause immediate life threatening end organ
damage, such as, pulmonary edema, cardiac ischemia, intracranial hemorrhage,
posterior reversible encephalopathy syndrome, or acute kidney injury. This
is referred to as hypertensive emergency. Alternatively, chronic, poorly
controlled hypertension can result is significant blood pressure elevation
without end organ injury; e.g. asymptomatic hypertension.

## Analysis

The goal of this analysis was to evaluate the charcteristics of patients
presenting to United States hospitals and to evaluate specific outcomes
for patients with this presentation.

For each observation in the NHAMCS dataset a triage blood pressure is recorded.
We used this to evaluate characeristics and outcomes for patients with
hypertension above a specified value.

Variables of interest included but are not limited to the following:

*   Age, sex, race, insurance status, arrival mode, antihypertensive administration,
    and use of diagnostic tests (labs and imaging).
*   Risk of combined cardiovascular outcomes (stroke, MI, hypertensive emergency),
    mortality, and admission to the hospitals

## How to use this package

### Data outputs

For convenience, all the statistical and plotting ouputs are reserved
in the repository and can be found in the outputs.

Furthermore, the modified dataset saved as pickle files in the ouptuts folder.

There is a notebook in the 'notebooks' folder that can be used as is to
load and review the dataset.

### Installation

If you want to re-run the analysis or make your own modified analysis then
consider the following steps.

#### Clone the repository

```
git clone https://github.com/coup321/NHAMCS_hypertension
```

#### Create a new virtual environment

```
# make sure virtualenv is installed in your base python environment
pip install virtualenv

# create new venv named nhamcs
virtualenv nhamcs

# activate the nhamcs venv
# Windows
.\nhamcs\Scripts\activate

# Mac/Linux
source nhamcs/bin/activate
```

#### Install the package and dependencies into the virtual environment

```
pip install -r requirements.txt
```

#### Re-downloading/running the analysis

By default, you can run the package and it will use the dataset in the folder
'./outputs/working\_dataset.pkl' and create all of the tables and plots in the
outputs folder.

```
python NHAMCS_hypertension
```
If you would like to download the data from the
[https://ftp.cdc.gov/pub/Health\_Statistics/NCHS/dataset\_documentation/nhamcs/spss/](CDC FTP servers)
then run the package with the force flag. This behavior is also created if the
working\_dataset.pkl file is somehow missing.

```
python NHAMCS_hypertension force
```

Keep in mind that it can take 3-5 minutes to download, unzip, and pickle the
files. Furthermore, building the working dataset from the raw data involves
multiple large boolean filters over 80,000 x 30 dataframes, so it can take up
to 10 minutes to run. This is primarily for medication and 'reason for visit'
regular expression filtering.

## Comments and advice for adapting this analysis for other NHAMCS projects

### Data changes over the years of data collection
- RACEETH changes to RACERETH in 2008 and there are some associated coding 
changes
- IMMED (ESI level) changes to IMMEDR in 2008 and there are some associated 
coding changes
- PAYTYPE changes to PAYTYPER in 2008 and there are some associated 
coding changes

### Working with medications
Medications are stored in MED1 through MED30 columns. For each medication 1-30
there are associated columnss with info about them.
- GPMED1-30 - indicates if the medication was given, prescribed, or both
- Medication category info as defined in documentation (where # is 1-30)
    - RX#CAT1',
    - RX#CAT2',
    - RX#CAT3',
    - RX#CAT4',
    - RX#V1C1',
    - RX#V1C2',
    - RX#V1C3',
    - RX#V1C4',
    - RX#V2C1',
    - RX#V2C2',
    - RX#V2C3',
    - RX#V2C4',
    - RX#V3C1',
    - RX#V3C2',
    - RX#V3C3',
    - RX#V3C4',

What worked for me is to create a boolean filter over the medication info I was
interested in, then use that to filter the medications (1-30). If I was just 
looking for a row that indicated medication was given, for example, then I would
reduce the Nx30 filter to 1x30 with an 'any' method on the column axis.
