import pandas as pd
import os
from blood_pressure import CategoricalStats, Htn_definition
from outcome_stats import OutcomeStats
from bp_over_time_plots import build_time_series_multiplot
from build_dataframe import build_dataframe

# read exported dataset

# build outcomes tables for 3 different blood pressure cutoffs?
# alternatively, could compare all 3 somehow?

# build states for categorical differences for 3 different blood pressure cutoffs.


def main(df, htn_def):

    categorical_queries = {
        'AGE_BIN': 'multinomial',
        'SEX': 'multinomial',
        'HX_HTN': 'binomial',
        'VDAYR': 'multinomial',
        'VTIMER': 'multinomial',
        'ANTIHYPERTENSIVE_RX': 'binomial',
        'ANTIHYPERTENSIVE_GIVEN': 'binomial',
        'TYLENOL_GIVEN': 'binomial',
        'NO_TRIAGE_BP': 'binomial',
        'DIED': 'binomial',
        'PAYTYPER': 'multinomial',
        'ADMITHOS': 'binomial',
        'ARREMS': 'multinomial',
        'RACERETH': 'multinomial',
        'REGION': 'multinomial',
        'IMMEDR': 'multinomial',
        'CHEST_PAIN_VISIT': 'binomial',
        'DYSPNEA_VISIT': 'binomial',
        'ABDOMINAL_PAIN_VISIT': 'binomial',
        'ATTPHYS': 'multinomial',
        'RESINT': 'multinomial',
        'MIDLEVEL': 'binomial',
        'XRAY': 'binomial',
        'CATSCAN': 'binomial',
        'MRI': 'binomial',
        'CBC': 'binomial',
        'TROPONIN': 'binomial',
    }
    outcome_queries = [
        ['DIED', 'categorical'],
        ['ADMITHOS', 'categorical'],
        ['HTN_COMPLICATION', 'categorical'],
        ['ANTIHYPERTENSIVE_GIVEN', 'categorical'],
        ['ANTIHYPERTENSIVE_RX', 'categorical'],
        ['TYLENOL_GIVEN', 'categorical'],
        ['CBC', 'categorical'],
        ['TROPONIN', 'categorical'],
        ['XRAY', 'categorical'],
        ['CATSCAN', 'categorical'],
        ['BPSYS', 'numeric'],
        ['ED_LOS', 'numeric'],
        ['HOSP_LOS', 'numeric'],

    ]
    categorical_stats = CategoricalStats(df, categorical_queries, htn_def)
    outcome_stats = OutcomeStats(df, htn_def, outcome_queries)
    outcome_fig, _ = outcome_stats.plot_queries()
    time_series_fig = build_time_series_multiplot(df, htn_def)

    return categorical_stats.get_stats(), outcome_stats.get_stats(), outcome_fig, time_series_fig


def export_cutoff(df, sbp_cutoff, dbp_cutoff):
    # set HTN definition
    htn_def = Htn_definition(df, sbp_cutoff, dbp_cutoff)

    # build stats tables and plots
    stats = main(df, htn_def)
    categorical_stats, outcome_stats, outcome_fig, time_series_fig = stats

    # save to file
    dir_path = './outputs/stats_HTN_' + str(sbp_cutoff) + '_ ' + str(dbp_cutoff)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    stats[0].to_csv(os.path.join(dir_path, 'baseline_characteristics.csv'))
    stats[1].to_csv(os.path.join(dir_path, 'outcome_stats.csv'))
    outcome_fig.savefig(os.path.join('./outputs', 'category_by_bp.png'))
    time_series_fig.savefig(os.path.join(dir_path, 'time_series.png'))


if __name__ == "__main__":
    if os.path.exists('./outputs/working_dataframe.pkl'):
        df = pd.read_pickle('./outputs/working_dataframe.pkl')
    else:
        build_dataframe()
        df = pd.read_pickle('./outputs/working_dataframe.pkl')
    cutoffs = [
        [180, 110],
        [160, 100],
        [140, 90],
        [120, 80]
    ]

    for sbp, dbp in cutoffs:
        print(
            f'''
        ---------------------------------------------------------
        Generating baseline characteristics and outcome stats for
        exposure of blood pressure >{sbp}/{dbp}
        ---------------------------------------------------------
        ''')
        export_cutoff(df, sbp, dbp)
