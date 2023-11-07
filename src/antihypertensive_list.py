'''
1) build antihypertensive list from dataset
2) manually pick out medications
3) create a importable csv or text file for other scripts
'''
from utility_functions import get_regex_cols
import pandas as pd
import numpy as np
import re


def build_cardiovascular_med_filter(raw_df):
    '''
    Returns a boolean filter for cardovascular meds
    with shape len(raw_df) x 30 
    '''
    # for each of the 30 med cols, check if it is a cv med
    num_rows, num_cols = len(raw_df), 30
    CV_regex = r'Cardiovascular agents|Cardiovas agents'
    category_cols = [
        r'RX\d*CAT1',
        r'RX\d*CAT2',
        r'RX\d*CAT3',
        r'RX\d*CAT4',
        r'RX\d*V1C1',
        r'RX\d*V1C2',
        r'RX\d*V1C3',
        r'RX\d*V1C4',
        r'RX\d*V2C1',
        r'RX\d*V2C2',
        r'RX\d*V2C3',
        r'RX\d*V2C4',
        r'RX\d*V3C1',
        r'RX\d*V3C2',
        r'RX\d*V3C3',
        r'RX\d*V3C4',
    ]
    # start with a filter that is all False
    F = np.full((num_rows, num_cols), False)
    for rx_col in category_cols:
        # each regex 'rx_col' is going to match 30 columns (for each med)
        # category_cols contains all the different category options
        # for each medication
        cols = get_regex_cols(raw_df, rx_col)
        rx_df = raw_df[cols]  # get the cols for this category (30 of them)
        bool_df = rx_df.apply(lambda ser: ser.str.contains(
            CV_regex, regex=True), axis=1).to_numpy()
        F = bool_df | F
    return F


def export_antihypertensive_list(raw_df):
    '''
    Exports excel list that can be manually reviewed
    '''
    F = build_cardiovascular_med_filter(raw_df)
    med_cols = get_regex_cols(raw_df, r'^MED\d+$')
    med_list = raw_df[med_cols].where(F).melt(
        value_name='meds').dropna().meds.value_counts()
    med_list.to_excel('./outputs/antihypertensive_list.xlsx')
    return med_list


def import_modified_hypertensive_list():
    '''
    returns a LIST object with antihypertensive medication names
    '''
    excel_frame = pd.read_excel('./outputs/antihypertensive_list.xlsx')
    return excel_frame.dropna().Name.values


def get_drug_info(raw_df, drug_name):
    '''
    # HELPER FUNCTION
    this function exists to help determine what the database RX categories
    are for a medication. Enter the DF and a drug name and it will return
    the RX info for that drug. 
    '''
    meds = raw_df[get_regex_cols(raw_df, r'^MED\d+$')]
    F = meds.apply(lambda ser: ser.str.contains(
        drug_name, regex=True, flags=re.IGNORECASE), axis=1)
    F_filtered = F[F.any(axis=1)]
    row_idx = F_filtered.index[0]
    col_idx = F_filtered.loc[row_idx].idxmax()
    med_number = col_idx[3:]  # intentially left a string
    empty_category_cols = [
        r'RX_CAT1',
        r'RX_CAT2',
        r'RX_CAT3',
        r'RX_CAT4',
        r'RX_V1C1',
        r'RX_V1C2',
        r'RX_V1C3',
        r'RX_V1C4',
        r'RX_V2C1',
        r'RX_V2C2',
        r'RX_V2C3',
        r'RX_V2C4',
        r'RX_V3C1',
        r'RX_V3C2',
        r'RX_V3C3',
        r'RX_V3C4',
    ]

    category_cols = [col.replace('_', med_number)
                     for col in empty_category_cols]

    return raw_df.loc[row_idx, category_cols]


if __name__ == "__main__":
    # raw_df = pd.read_pickle(
    #     ('./outputs/working_raw_dataframe.pkl'))
    # raw_df = raw_df.query("YEAR >= 2015")
    # export_antihypertensive_list(raw_df)
    print(import_modified_hypertensive_list())
