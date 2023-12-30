import pandas as pd
from blood_pressure import Htn_definition
import matplotlib.pyplot as plt
from antihypertensive_list import import_modified_hypertensive_list

class MedCounts()
    def __init__(df, htn_def):
        self.df = df
        self.htn_def = htn_def


    def med_counts(self):
        meds = import_modified_hypertensive_list()



if __name__ == "__main__":
    df = pd.read_pickle(
        ('./outputs/working_dataframe.pkl'))
    htn_definition = Htn_definition(df, sbp_cutoff=90, dbp_cutoff=50)