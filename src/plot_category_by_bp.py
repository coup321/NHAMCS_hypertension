'''
Contains methods to plot the category by blood pressure for different
categories. Used the OutcomeStats class in the outcome_stats module.
'''
import pandas as pd
from blood_pressure import Htn_definition
import matplotlib.pyplot as plt
import numpy as np


def weighted_average(df, category):
    vals = df[category].dropna()
    weights = df.PATWT[vals.index]
    return np.average(vals, weights=weights)


def plot_category(df, ax, category, kind):
    bins = [60, 80, 100, 120, 140, 160, 180, 200, 220, 300]
    binned_sbp = pd.cut(df.BPSYS, bins)
    G = df.groupby(binned_sbp)

    if kind == 'categorical':
        numerator = G.apply(lambda df: sum(df[category] * df.PATWT))
        denominator = G.PATWT.sum()
        binned_category = numerator/denominator
    elif kind == 'numeric':
        binned_category = G.apply(lambda df: weighted_average(df, category))
    else:
        raise ValueError

    bars = ax.bar(binned_category.index.astype(str),
                  binned_category.values, color='skyblue')

    ax.set_title(
        f'{category} Proportion by Systolic Blood Pressure Bins', fontsize=8)
    ax.set_xticks(range(len(binned_category.index)))
    ax.set_xticklabels(labels=binned_category.index.astype(
        str), rotation=45, fontsize=8)

    for bar in bars:
        height = bar.get_height()
        label_x_pos = bar.get_x() + bar.get_width() / 2
        ax.text(label_x_pos, height,
                s=f'{height:.3f}', ha='center', va='bottom', fontsize=6)


if __name__ == "__main__":
    df = pd.read_pickle(
        ('./outputs/working_dataframe.pkl'))
    fig, ax = plt.subplots(figsize=(12, 6))
    plot_category(df, ax, 'ED_LOS', 'numeric')
    plt.tight_layout()
    plt.show()
