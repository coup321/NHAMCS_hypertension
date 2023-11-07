'''
Contains many functions that calculate weighted/unweighted statistics
for the dataset.
'''
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency
from scipy.stats import t, norm
from statsmodels.stats.proportion import proportion_confint


def weighted_mean_and_ci(df):
    # calculate the weighted mean and CI for pandas dataframe
    # loc[:, 0] needs to be the series
    # loc[:, 1] needs to be the weights
    df = df.dropna()
    data = df.iloc[:, 0]
    weights = df.iloc[:, 1]
    normalized_weights = weights / sum(weights)

    # Calculate the weighted mean
    weighted_mean = np.average(data, weights=normalized_weights)

    # Calculate the weighted standard error
    # sample size is actually sum of weights, not the length of dataset
    sample_size = sum(weights)
    weighted_variance = sum(normalized_weights * (data - weighted_mean)**2)
    weighted_std = np.sqrt(weighted_variance)

    # Calculate the sample size

    # Define the desired confidence level
    confidence_level = 0.95

    # Calculate the critical value based on the t-distribution
    # critical value is how many standard errors to go out
    z = t.ppf((1 + confidence_level) / 2, df=sample_size - 1)

    # Calculate the margin of error
    SE = weighted_std / np.sqrt(sample_size)

    # Calculate the lower and upper bounds of the confidence interval
    lower_bound = weighted_mean - z*SE
    upper_bound = weighted_mean + z*SE

    return weighted_mean, lower_bound, upper_bound


def weighted_mean_and_std(ser, weights):
    ser = ser.dropna()
    weights = weights[ser.index]
    normalized_weights = weights / sum(weights)
    weighted_mean = np.average(ser, weights=normalized_weights)

    # Calculate the weighted standard deviation
    # sample size is actually sum of weights, not the length of dataset
    sample_size = sum(weights)
    weighted_variance = sum(normalized_weights * (ser - weighted_mean)**2)
    weighted_std = np.sqrt(weighted_variance)

    # Calculate the lower and upper bounds of the confidence interval

    return weighted_mean, weighted_std


def weighted_mean_difference_and_ci(ser1, ser2, weights1, weights2):
    assert len(ser1) == len(weights1)
    assert len(ser2) == len(weights2)
    normalized_weights1 = weights1 / sum(weights1)
    normalized_weights2 = weights2 / sum(weights2)
    x1 = np.average(ser1, weights=weights1)
    x2 = np.average(ser2, weights=weights2)
    n1 = sum(weights1)
    n2 = sum(weights2)
    v1 = sum(normalized_weights1 * (ser1 - x1)**2)
    v2 = sum(normalized_weights2 * (ser2 - x2)**2)
    s1 = np.sqrt(v1)
    s2 = np.sqrt(v2)

    mean_difference = x2 - x1
    SE_difference = np.sqrt(s1**2/n1 + s2**2/n2)
    LCI = mean_difference - 1.96*SE_difference
    UCI = mean_difference + 1.96*SE_difference
    return mean_difference, LCI, UCI


def calculate_proportions_and_CI(df, col):
    '''
    Returns yearly proportions of column and the CI
    '''
    # Assuming you have a DataFrame named 'df' with columns 'YEAR', col, 'PATWT'

    # Calculate the weighted sum of column for each year
    weighted_sum = df.groupby('YEAR').apply(
        lambda x: (x[col] * x['PATWT']).sum())

    # Calculate the total weight per year
    total_weight = df.groupby('YEAR')['PATWT'].sum()

    # Calculate the weighted proportion of 'HTN' per year
    weighted_proportion = weighted_sum / total_weight

    # Calculate the confidence intervals using Wilson Score Interval
    ci_lower, ci_upper = proportion_confint(
        weighted_sum, total_weight, alpha=0.05, method='wilson')

    # Create a DataFrame with the results
    result_df = pd.DataFrame({
        'Weighted_Proportion': weighted_proportion,
        'CI_lower': ci_lower,
        'CI_upper': ci_upper
    })

    return result_df


def weighted_relative_risk(ser2, ser1, w2, w1):
    a = sum(ser1 * w1)  # exposed with outcome
    b = sum(ser2 * w2)  # not_exposed with outcome
    c = sum(w1) - a    # exposed without outcome
    d = sum(w2) - b    # not_exposed without outcome
    RR = (a / (a + c)) / (b / (b + d))
    log_RR = np.log(RR)

    # gives the z value for 0.975 on the normal Z-distribution
    z = norm.ppf(0.975)  # 95% using Z-distribution
    # standard error of log relative risk
    SE = np.sqrt((1/a) - (1/(a+c)) + (1/b) - (1/(b+d)))
    log_LCI = log_RR - z*SE
    log_UCI = log_RR + z*SE
    LCI = np.exp(log_LCI)
    UCI = np.exp(log_UCI)

    return RR, LCI, UCI


def weighted_proportion(ser, weights):
    positives = sum(ser*weights)
    total = sum(weights)
    return positives / total


def contingency(ser1, ser2):
    '''
    create the unweighted contingency table between two series.
    '''
    df = pd.DataFrame({
        ser1.name + '_ser1': ser1.value_counts(sort=False),
        ser2.name + '_ser2': ser2.value_counts(sort=False)
    }).fillna(0).astype(int)
    return df


def weighted_chi2(ser1, ser2, weights):
    '''
    return the weighted chi square p value for two series with weights
    the weights series must contain all the indices of ser1 and ser2
    '''
    # Create a contingency table
    true1 = sum(ser1 * weights[ser1.index])
    false1 = sum(weights[ser1.index]) - true1
    true2 = sum(ser2*weights[ser2.index])
    false2 = sum(weights[ser2.index]) - true2

    contingency_table = [[true1, false1], [true2, false2]]

    _, p_value, _, _ = chi2_contingency(contingency_table)

    return p_value


def weighted_contingency(ser1, ser2, weights):
    '''
    create the weighted contingency table between two series
    the weights series must contain all the indices of ser1 and ser2
    '''
    assert ser1.dtype == 'category', 'ser1 must be categorical dtype'
    assert ser2.dtype == 'category', 'ser2 must be categorical dtype'
    assert ser1.index.isin(weights.index).all(
    ), "All indices of ser1 must be included in weights' index"
    assert ser2.index.isin(weights.index).all(
    ), "All indices of ser2 must be included in weights' index"
    assert (ser1.cat.categories == ser2.cat.categories).all()
    categories = ser1.cat.categories
    table = pd.DataFrame(index=categories, columns=['ser1', 'ser2']).fillna(0)

    for c in categories:
        table.loc[c, 'ser1'] = ((ser1 == c) * weights[ser1.index]).sum()
        table.loc[c, 'ser2'] = ((ser2 == c) * weights[ser2.index]).sum()
    return table
