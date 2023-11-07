from pytest import approx
from statsmodels.stats.weightstats import DescrStatsW
from scipy.stats import t
from numpy.testing import assert_array_equal, assert_array_almost_equal
import numpy as np
import pandas as pd
from blood_pressure import Htn_definition, CategoricalStats


def test_get_triage_htn():
    df = pd.DataFrame({
        'BPSYS': [149.0, 100.0, 200.0, 120.0, 160],
        'BPDIAS': [90.0, 40.0, 180.0, 80.0, 110],
        'BPSYSD': [149.0, 100.0, 200.0, 120.0, 160],
        'BPDIASD': [90.0, 40.0, 180.0, 80.0, 110]
    })
    expected_values = np.array([0, 0, 1, 0, 1])

    Htn_def = Htn_definition(df, sbp_cutoff=180, dbp_cutoff=100)
    triage_htn = Htn_def.get_triage_htn().astype(int).values

    assert_array_equal(triage_htn, expected_values)


def test_HTN_totals():
    df = pd.read_pickle('./outputs/working_dataframe.pkl')
    htn = (df.BPSYS > 200) | (df.BPDIAS > 120)
    cbc = df.CBC == 1
    weights = df.PATWT
    # total number of patients
    total = weights.sum() / 1e6

    # total number of patients with HTN
    total_with_HTN = weights[htn].sum() / 1e6

    # total number of patients without HTN
    total_without_HTN = weights[~htn].sum() / 1e6


def test_binomial_stat():
    df = pd.read_pickle('./outputs/working_dataframe.pkl')
    htn = (df.BPSYS > 200) | (df.BPDIAS > 120)
    cbc = df.CBC == 1
    weights = df.PATWT

    # total number of patients
    total = weights.sum() / 1e6

    # total number of patients with HTN
    total_with_HTN = weights[htn].sum() / 1e6

    # total number of patients without HTN
    total_without_HTN = weights[~htn].sum() / 1e6

    # total number of patients with CBC
    total_with_CBC = weights[cbc].sum() / 1e6

    # total number of patients with CBC and without HTN
    total_with_CBC_without_HTN = weights[cbc & ~htn].sum() / 1e6

    # total number of patients with CBC and without HTN
    total_with_CBC_with_HTN = weights[cbc & htn].sum() / 1e6

    categorical_queries = {
        'AGE_BIN': 'multinomial',
        'CBC': 'binomial',
        'TROPONIN': 'binomial',
    }
    htn_def = Htn_definition(df, 200, 120)
    categorical_stats = CategoricalStats(df, categorical_queries, htn_def)
    stats = categorical_stats.get_stats()
    row_values = stats.loc['CBC', :].values[0:6]
    expected = [
        total_with_CBC,
        total_with_CBC_without_HTN,
        total_with_CBC_with_HTN,
        total_with_CBC / total,
        total_with_CBC_without_HTN / total_without_HTN,
        total_with_CBC_with_HTN / total_with_HTN,
    ]

    assert_array_almost_equal(expected, row_values)
