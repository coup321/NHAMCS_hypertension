from stats import (weighted_contingency, weighted_mean_and_ci, weighted_chi2,
                   weighted_mean_difference_and_ci, weighted_relative_risk)
from pandas.api.types import CategoricalDtype
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency


def test_weighted_mean_and_ci():
    vals = [1, 2, 3, 4, 5]
    weights = [10, 20, 15, 45, 20]
    weighted_mean = 3.40909091
    lower_bound = 3.0818216986434552
    upper_bound = 3.644837843063975

    df = pd.DataFrame({
        'vals': vals,
        'weights': weights
    })
    output = weighted_mean_and_ci(df)
    assert abs(output[0] - weighted_mean) < 0.1
    assert abs(output[1] - lower_bound) < 0.1
    assert abs(output[2] - upper_bound) < 0.1


def test_weighted_mean_difference_and_ci():
    ser1 = pd.Series([1, 2, 3, 4, 5])
    ser2 = pd.Series([6, 7, 8, 9, 10])
    w1 = pd.Series([1, 1, 1, 1, 1])
    w2 = pd.Series([1, 1, 1, 1, 1])

    mean_difference, LCI, UCI = weighted_mean_difference_and_ci(
        ser1, ser2, w1, w2)

    expected_mean_difference = 5
    expected_SE = 0.89
    expected_LCI = 5 - 1.96 * expected_SE
    expected_UCI = 5 + 1.96 * expected_SE

    assert abs(expected_mean_difference - mean_difference) < 0.1
    assert abs(expected_LCI - LCI) < 0.1
    assert abs(expected_UCI - UCI) < 0.1


def test_weighted_mean_difference_and_ci2():
    ser1 = pd.Series([1, 2, 3, 4, 5])
    ser2 = pd.Series([6, 7, 8, 9, 10])
    w1 = pd.Series([1, 1, 4, 1, 1])
    w2 = pd.Series([1, 3, 1, 1, 1])

    mean_difference, LCI, UCI = weighted_mean_difference_and_ci(
        ser1, ser2, w1, w2)

    expected_mean_difference = 4.7143
    expected_SE = 0.62
    expected_LCI = expected_mean_difference - 1.96 * expected_SE
    expected_UCI = expected_mean_difference + 1.96 * expected_SE

    assert abs(expected_mean_difference - mean_difference) < 0.1
    assert abs(expected_LCI - LCI) < 0.1
    assert abs(expected_UCI - UCI) < 0.1


test_weighted_mean_difference_and_ci2()


def test_weighted_contingency():
    cat_dtype = CategoricalDtype(
        categories=['South', 'West', 'Midwest', 'Northeast'])

    ser1 = pd.Series({55653: 'South',
                      70412: 'West',
                      61906: 'Midwest',
                      59346: 'South',
                      68716: 'West',
                      69728: 'West',
                      56835: 'South',
                      69685: 'West',
                      62747: 'Midwest',
                      57798: 'South'}).astype(cat_dtype)

    ser2 = pd.Series({50848: 'South',
                      48744: 'South',
                      43337: 'Northeast',
                      55066: 'Midwest',
                      45001: 'West',
                      44515: 'Northeast',
                      43897: 'Northeast',
                      54699: 'Midwest',
                      43832: 'Northeast',
                      48824: 'South'}).astype(cat_dtype)

    weights = pd.Series({55653: 1,
                         70412: 1,
                         61906: 500,
                         59346: 1,
                         68716: 1,
                         69728: 1,
                         56835: 1,
                         69685: 1,
                         62747: 1,
                         57798: 1,
                         50848: 1,
                         48744: 1,
                         43337: 1,
                         55066: 1,
                         45001: 100,
                         44515: 1,
                         43897: 1,
                         54699: 1,
                         43832: 1,
                         48824: 1})
    calculated = weighted_contingency(ser1, ser2, weights)

    expected = pd.DataFrame(
        {'ser1': {'South': 4, 'West': 4, 'Midwest': 501, 'Northeast': 0},
         'ser2': {'South': 3, 'West': 100, 'Midwest': 2, 'Northeast': 4}}
    )
    assert (calculated == expected).all(skipna=False).all(skipna=False)


def test_weighted_relative_risk():
    # test when weights are normal (unweighted)
    ser1 = pd.Series({
        'f': 1,
        'g': 0,
        'h': 0,
        'i': 0,
        'j': 0
    })

    ser2 = pd.Series({
        'a': 1,
        'b': 1,
        'c': 1,
        'd': 0,
        'e': 0
    })

    w1 = pd.Series({
        'f': 1,
        'g': 1,
        'h': 1,
        'i': 1,
        'j': 1
    })

    w2 = pd.Series({
        'a': 1,
        'b': 1,
        'c': 1,
        'd': 1,
        'e': 1
    })

    RR, LCI, UCI = weighted_relative_risk(ser1, ser2, w1, w2)
    expected_RR = 3.0
    expected_LCI = 0.4516
    expected_UCI = 19.9285

    assert abs(RR - expected_RR) < 0.1
    assert abs(LCI - expected_LCI) < 0.1
    assert abs(UCI - expected_UCI) < 0.1


def test_weighted_chi2():
    # test when all weights are 1
    ser1 = pd.Series([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
    ser2 = pd.Series([0, 0, 0, 1, 1, 1, 1, 1, 1, 1])
    weights = pd.Series([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    expected = 0.368688  # with yates correction
    calculated = weighted_chi2(ser1, ser2, weights)
    assert abs(expected - calculated) < 0.05


def test_weighted_chi2_2():
    # tests the weighting component
    # 3 + 10 = 13 1's and 6 0's
    ser1 = pd.Series([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
    # 2 + 10 = 12 0's and 7 1's
    ser2 = pd.Series([0, 0, 0, 1, 1, 1, 1, 1, 1, 1])
    # contingency is
    # [[13, 6], [7, 12]]
    weights = pd.Series([1, 10, 1, 1, 1, 1, 1, 1, 1, 1])
    expected = 0.104276  # with yates correction
    calculated = weighted_chi2(ser1, ser2, weights)
    assert abs(expected - calculated) < 0.05
