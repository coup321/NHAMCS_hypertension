'''
This module contains functions that take the raw dataframe that is created
from concatenating multiple years of the NHAMCS dataset. It handles many of the
column name changes and variations/technicalities in the dataset.

It creates a specific column that indicates if a patient had a particular
cardiovascular outcome as defined the lists at the top of the module. This
is primarily based on ICD codes.

If there are issues accessing the spss files the following links to the main
ftp download server on the CDC website and the main NHAMCS site.

https://ftp.cdc.gov/pub/Health_Statistics/NCHS/dataset_documentation/nhamcs/spss
https://www.cdc.gov/nchs/ahcd/datasets_documentation_related.htm

'''
import pandas as pd
import numpy as np
import re
import glob
from antihypertensive_list import import_modified_hypertensive_list
from download_and_unzip_NHAMCS_files import FileDownloader
if __name__ == "__main__":
    from utility_functions import map_timerange, diagnosis_filter
else:
    from src.utility_functions import map_timerange, diagnosis_filter

cardiac_arrest_ICD = [
    r'^Cardiac arrest',
    r'^Cardiac arrest, cause unspecified',
    r'^STEMI & NSTEMI mocard infrc',
    r'^Acute ischemic heart disease, unspecified',
    r'^ST elevation \(STEMI\) myocardial infarction of unsp site',
    r'^Acute myocardial infarction, unspecified',
    r'^Other acute ischemic heart diseases',
    r'^Other type of myocardial infarction',
    r'^ST elevation \(STEMI\) myocardial infarction of inferior wall',
]

stroke_ICD = [
    r'^Cerebral artery occlusion, unspec, wi\.\.\.',
    r'^Cerebral infarction, unspecified',
    r'^Cerebral infarction',
    r'^Intracerebral hemorrhage',
    r'^Nontraumatic intracerebral hemorrhage, unspecified',
    r'^Nontraumatic intracerebral hemorrhage',
    r'^Cerebral artery occlusion, unspec, w\/\.\.\.',
    r'^Cerebral infrc due to unsp occls or stenosis of cerebral art',
    r'^Other cerebral infarction',
    r'^Cerebral infarction due to embolism of cerebral arteries',
    r'^Cerebral infarction due to thrombosis of cerebral arteries',
]

hypertensive_emergency_ICD = [
    r'^Malignant essential hypertension',
    r'^Hypertensive urgency',
    r'^Hypertensive emergency',
    r'^Hypertensive crisis, unspecified',
    r'^Hypertensive encephalopathy',
    r'^Hypertensive crisis'
]


def validate_data():
    expected_files = [
        'ed2015-spss.pkl', 'ed2016-spss.pkl', 'ED2017-spss.pkl',
        'ED2018-spss.pkl', 'ED2019-spss.pkl', 'ed2020-spss.pkl',
        'ed2021-spss.pkl'
    ]
    globbed_files = glob.glob('./data/pickled_files/*')
    val = True
    for file in expected_files:
        is_in_glob = False
        for gfile in globbed_files:
            if file in gfile:
                is_in_glob = True
        val = is_in_glob & val
    return val


def load_dfs(as_list=False, force_download=False):
    '''
    Load the data from the pickled files. The pickled files load and are
    processed faster than the raw spss ones - so this is mainly an efficiency
    convenience.

    If the files are not found in the directory, then they are downloaded
    and unzipped first
    '''
    if validate_data() and not force_download:
        files = glob.glob('./data/pickled_files/*')
        dfs = []
        for file in files:
            df = pd.read_pickle(file)
            df = df.dropna(axis=1, how='all')
            dfs.append(df)
        if as_list:
            return dfs
        return pd.concat(dfs, axis=0)
    else:
        # if the files don't exist, then download them and then rerun the function
        base_url = "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/dataset_documentation/nhamcs/spss/"
        files_to_download = [
            'ed2015-spss.zip', 'ed2016-spss.zip', 'ED2017-spss.zip',
            'ED2018-spss.zip', 'ED2019-spss.zip', 'ed2020-spss.zip',
            'ed2021-spss.zip'
        ]
        download_directory = './data/'

        downloader = FileDownloader(
            base_url, files_to_download, download_directory)
        downloader.run()
        return load_dfs()


def get_RFV_filter(df, regex):
    '''
    takes as input the NHAMCS dataframe and a regex that should indicate a
    diagnosis, such as back pain, and it will return a binary filter where
    this is matching over all of the reason for visit columns

    Note that this is quite an inefficient function (string searching over
    many many rows)
    '''
    return (
        df
        # get the RFV columns
        .loc[:, [col for col in df.columns if re.search(r'RFV\d+(?![^$])', col)]]
        # search strings for the regex and combine columns such that any are true
        .apply(lambda row: row.str.contains(regex, regex=True, case=False))
        .any(axis=1)
    )


def get_MED_filter(df, rx_type, med_list):
    '''
    Based on a med_list this function takes as input the NHAMCS dataset
    and returns a binary indicator about if a medication was given or
    prescribed (based on the rx_type argument ('rx' or 'given')).
    '''
    # med cols
    MED = df[[col for col in df.columns if re.search(r'^MED\d', col)]]
    # med rx/given cols
    GPMED = df[[col for col in df.columns if re.search(r'GPMED\d', col)]]
    # first figure out where each med number (e.g. MED1) was prescibed
    # or given
    # rx_filter is a boolean indicator for given/rx
    if rx_type == 'rx':
        rx_filter = (
            (GPMED == 'RX at discharge')
            |
            (GPMED == 'Both given and RX marked')
        )
    elif rx_type == 'given':
        rx_filter = (
            (GPMED == 'Given in  ED')
            |
            (GPMED == 'Both given and RX marked')
        )

    # where a med was rx/given, keep the med, otherwise change to a
    # null value ('NO ENTRY MADE')
    med_filter = np.where(rx_filter, MED, 'NO ENTRY MADE')
    F = (
        # make the dataframe
        pd.DataFrame(med_filter, index=df.index)
        # rename the columns since we used a numpy method here
        .rename(columns={x: y for x, y in enumerate(MED)})
        # return true only if the med is in the med list
        .apply(
            lambda row: row.str.contains('|'.join(med_list),
                                         case=False,
                                         regex=True),
            axis=1)
        # return the row true if the med was given for a patient/observation
        .any(axis=1)
    )

    return F


def tweak_df(df):
    # med columns (MED1-MED30)
    MED = [col for col in df.columns if re.search(r'^MED\d', col)]
    # given/prescribed indicator (GPMED1-GPMED30)
    GPMED = [col for col in df.columns if re.search(r'GPMED\d', col)]
    keep_columns = [
        'YEAR', 'VMONTH', 'VDAYR', 'ARRTIME', 'AGE', 'SEX', 'RACERETH', 'CPR',
        'ADMITHOS', 'ADISP', 'REGION', 'MSA', 'PAYTYPER', 'BPSYS', 'BPSYSD', 'PULSE',
        'BPDIAS', 'BPDIASD', 'XRAY', 'HTN', 'ARREMS', 'HDSTAT', 'DOA', 'DIEDED', 'LOS', 'LOV',
        'LUMBAR', 'MRI', 'CATSCAN', 'CBC', 'CARDENZ', 'PAINSCALE', 'IMMEDR',
        'ATTPHYS',
        'RESINT', 'NURSEPR', 'PHYSASST', 'CSTRATM', 'CPSUM', 'PATWT',
        'DIAG1', 'DIAG2', 'DIAG3', 'DIAG4', 'DIAG5', 'RFV1', 'RFV2', 'RFV3', 'RFV4', 'RFV5',
        'NOFU', 'RETRNED', 'RETREFFU', 'LEFTAMA', 'LWBS', 'TRANNH','TRANPSYC','TRANOTH','OBSHOS','OBSDIS','OTHDISP'
        ] + MED + GPMED

    # get the med list based on antihypertensive_med module
    ANTIHYPERTENSIVE_MEDS = import_modified_hypertensive_list()

    return (
        df
        .loc[:, keep_columns]
        .assign(
            # fix types and replace values as needed
            YEAR=lambda df: df.YEAR.astype(int),
            VTIME=pd.to_datetime(
                df.ARRTIME.replace({
                    'Unknown': np.NaN,
                    '12:00 Midnight': '00:00 a.m.',
                    '12:00 noon': '12:00 p.m.'}), format='mixed'),
            VTIMER=lambda df: df.VTIME.dt.hour.map(
                map_timerange).astype('category'),
            CBC=lambda df_: (df_.CBC == 'Yes').astype(int),
            TROPONIN=lambda df: (df.CARDENZ == 'Yes').astype(int),
            XRAY=lambda df_: (df_.XRAY == 'Yes').astype(int),
            MRI=lambda df_: (df_.MRI == 'Yes').astype(int),
            CATSCAN=lambda df_: (df_.CATSCAN == 'Yes').astype(int),
            ATTENDING=lambda df: (df.ATTPHYS == 'Yes').astype(int),
            RESIDENT=lambda df: (df.RESINT == 'Yes').astype(int),
            # fix categorical values in age and make dtype -> int
            AGE=lambda df: df.AGE.replace({'93 years and over': 94.0,
                                           '94 years and over': 94.0,
                                           'Under one year': 0.0,
                                           '100 years and over': 100.0})
            .pipe(pd.to_numeric),
            AGE_BIN=lambda df: pd.cut(
                df.AGE,
                bins=[17, 25, 44, 65, 110],
                labels=['Age 18-25', 'Age 26-44', 'Age 45-65', 'Age over 65']
            ).astype('category'),
            # make ADMITHOS a binary variable
            ADMITS_COMBINED=lambda df: (
                (df.ADMITHOS == 'Yes') |
                (df.TRANNH == 'Yes') |
                (df.TRANPSYC == 'Yes') |
                (df.TRANOTH == 'Yes') |
                (df.OBSHOS == 'Yes') |
                (df.OBSDIS == 'Yes')
            ),
            DISCHARGED_COMBINED = lambda df: ~df.ADMITS_COMBINED & (
                (df.NOFU == 'Yes') |
                (df.RETRNED == 'Yes') |
                (df.RETREFFU == 'Yes') |
                (df.DIEDED == 'Yes')
            ),
            LEFT_AMA = lambda df: df.LEFTAMA == 'Yes',
            LWBS = lambda df: df.LWBS == 'Yes',
            ADMITHOS=lambda df: df.ADMITHOS.replace({'Yes': 1, 'No': 0}).astype(bool),
            PULSE = lambda df: df.PULSE.replace(

                {'DOPP or DOPPLER':np.nan, 'Blank':np.nan}
            ),
            TRIAGE_TACHYCARDIA = lambda df: df.PULSE > 100,
            # replace 'Blank' values in BPSYS, BPSYSD, BPDIAS, BPDIASD, PULSE
            # also fix the type to be float
            BPSYS=lambda df: df.BPSYS.replace('Blank', np.nan).astype('float'),
            BPSYSD=lambda df: df.BPSYSD.replace(
                'Blank', np.nan).astype('float'),
            BPDIAS=lambda df: df.BPDIAS.replace({
                'Blank': np.nan,
                'P, Palp, DOP or DOPPLER': np.nan,
                'P, Palp, DOPP or DOPPLER': np.nan}).astype('float'),
            BPDIASD=lambda df: df.BPDIASD.replace({
                'Blank': np.nan,
                'P, Palp, DOP or DOPPLER': np.nan,
                'P, Palp, DOPP or DOPPLER': np.nan}).astype('float'),
            SBP_BIN=lambda df: pd.cut(
                df.BPSYS,
                bins=[59, 79, 99, 119, 139, 159, 179, 199, 219],
                labels=[
                    'SBP 60-80',
                    'SBP 80-100',
                    'SBP 100-120',
                    'SBP 120-140',
                    'SBP 140-160',
                    'SBP 160-180',
                    'SBP 180-200',
                    'SBP 200-220',
                    ]
            ).astype('category'),
            # if pt has history of hypertension
            HX_HTN=lambda df: (df.HTN == 'Yes').astype(int),
            # if the patient has a null value for triage blood pressure
            # (systolic or diastolic)
            NO_TRIAGE_BP=lambda df: df.BPSYS.isna() | df.BPDIAS.isna(),
            # CREATE CARDIOVASCULAR OUTCOME INDICATOR COLUMN
            # Create binary indicator for diagnosis of stroke, MI, or hypertensive emergency
            STROKE=lambda df: diagnosis_filter(df, '|'.join(stroke_ICD)),
            MI=lambda df: diagnosis_filter(df, '|'.join(cardiac_arrest_ICD)),
            HTNEMERGENCY=lambda df: diagnosis_filter(
                df, '|'.join(hypertensive_emergency_ICD)),
            HTN_COMPLICATION=lambda df: df.STROKE | df.MI | df.HTNEMERGENCY,
            # arrived by EMS
            ARREMS=lambda df: df.ARREMS.replace({
                'Blank': 'Unknown'
            }).fillna('Unknown').astype('category'),
            # pt died if they died in ED or died after admission
            # HDSTAT = hospital discharge status (blank, unknown, not avail,
            #     alive, dead
            # DOA = dead on arrival - removing this I don't think it's relavent
            DIED=lambda df: (df.HDSTAT == 'Dead') | (df.DIEDED == 'Yes'),
            # LOV is ED length of stay - even for admitted patients in mins
            ED_LOS=lambda df: df.LOV.replace({'Blank': np.nan}).astype(float),
            # LOS is hospital lenght of stay in days
            # replacing blank AND NA with nans. Might need to investigate further.
            HOSP_LOS=lambda df: df.LOS.replace({
                'Not Applicable': np.nan,
                'Blank': np.nan
            }),
            # combine 'NURSEPR','PHYSASST' to make midlevel filter
            MIDLEVEL=lambda df: ((df.NURSEPR == 'Yes') | (
                df.PHYSASST == 'Yes')).astype(int),
            PAYTYPER=lambda df: (
                df.PAYTYPER
                .replace({
                    'No charge/Charity': 'No charge',
                    'No charge/charity': 'No charge',
                    'All sources for payment are blank': 'Blank',
                    'All sources of payment are blank': 'Blank',
                    'Medicaid':  'Medicaid or CHIP or other state-based program',
                    'Medicaid or CHIP':  'Medicaid or CHIP or other state-based program'})
            ).astype('category'),
            IMMEDR=lambda df: (
                df.IMMEDR
                .replace({
                    '1-14 min': 'Emergent',
                    '15-60 min': 'Urgent',
                    '>1hr-2hrs': 'Semi-urgent',
                    '>2hrs-24hrs': 'Nonurgent',
                    'Blank': 'Unknown',
                    'No triage': 'Unknown',
                    'No triage for this visit but ESA does conduct triage': 'Unknown',
                    'Visit occured in ESA that does not conduct nursing triage': 'Unknown',
                    'Visit occurred in ESA that does not conduct nursing triage': 'Unknown'
                })
            ).astype('category'),

            RACERETH=lambda df: df.RACERETH.astype('category'),
            # create visit type columns
            DYSPNEA_VISIT=lambda df_: get_RFV_filter(
                df_, 'shortness of breath|dyspnea').astype(int),
            CHEST_PAIN_VISIT=lambda df_: get_RFV_filter(
                df_, 'chest pain').astype(int),
            ABDOMINAL_PAIN_VISIT=lambda df_: get_RFV_filter(
                df_, 'abdominal pain').astype(int),
            TYLENOL_GIVEN=lambda df: get_MED_filter(
                df, 'given', ['tylenol', 'acetaminophen']).astype(int),
            ANTIHYPERTENSIVE_GIVEN=lambda df: get_MED_filter(
                df, 'given', ANTIHYPERTENSIVE_MEDS).astype(int),
            ANTIHYPERTENSIVE_RX=lambda df: get_MED_filter(
                df, 'rx', ANTIHYPERTENSIVE_MEDS).astype(int),

        )
        .query('AGE >= 18')  # remove pediatric patients
        .query('YEAR >= 2015')  # remove years less than 2015
        .drop(
            ['NURSEPR', 'PHYSASST'], axis=1)
        # guarentee unique index values for future work/joins
        .reset_index(drop=True)
    )


def build_dataframe(force_download=False):
    raw_df = load_dfs(force_download=force_download)
    df = tweak_df(raw_df)
    raw_df.to_pickle('./outputs/working_raw_dataframe.pkl')
    df.to_pickle('./outputs/working_dataframe.pkl')


if __name__ == "__main__":
    raw_df = load_dfs()
    df = tweak_df(raw_df)
    print(df)
    raw_df.to_pickle('./outputs/working_raw_dataframe.pkl')
    df.to_pickle('./outputs/working_dataframe.pkl')
    # print(validate_data())
