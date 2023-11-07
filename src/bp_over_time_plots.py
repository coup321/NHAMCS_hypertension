import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gs
from stats import (
    weighted_mean_and_std,
    weighted_mean_and_ci,
    weighted_proportion
)
from blood_pressure import Htn_definition

pd.set_option('display.max_columns', None)  # None means unlimited
pd.set_option('display.width', None)


def weighted_mean_std_by_year(df, col):
    '''
    Get the weighted mean and standard deviation of a column (col)
    for each year in the dataframe, df.
    '''
    vals = df.groupby('YEAR').apply(
        lambda df: weighted_mean_and_std(df[col], df.PATWT))
    vals = vals.reset_index()
    vals['mean'] = vals.iloc[:, 1].apply(lambda ser: ser[0])
    vals['std'] = vals.iloc[:, 1].apply(lambda ser: ser[1])
    vals.drop(0, axis=1, inplace=True)

    return vals['YEAR'], vals['mean'], vals['std']


def weighted_mean_ci_by_year(df, col):
    '''
    Get the weighted mean and confidence interval of a column (col)
    for each year in the dataframe, df.
    '''
    vals = df.groupby('YEAR').apply(
        lambda df: weighted_mean_and_ci(df[[col, 'PATWT']]))
    vals = vals.reset_index()
    vals['mean'] = vals.iloc[:, 1].apply(lambda ser: ser[0])
    vals['lower'] = vals.iloc[:, 1].apply(lambda ser: ser[1])
    vals['upper'] = vals.iloc[:, 1].apply(lambda ser: ser[2])
    vals.drop(0, axis=1, inplace=True)
    return vals['YEAR'], vals['mean'], vals['lower'], vals['upper']


def plot_val_lower_upper(year, val, lower, upper, ax, **kwargs):
    '''
    Utility funciton to add a scatter and error bar plot to an ax
    based on the year, value, lower std/ci and upper std/ci
    '''

    ax.scatter(x=year, y=val, **kwargs)

    ax.errorbar(
        x=year,
        y=val,
        yerr=[lower, upper],
        fmt='none',
        capsize=5,
        ** kwargs
    )

    return ax


def plot_mean_std_over_time(df, ax):
    '''
    Show boxplots for weighted BPSYS and BPDIAS over time
    '''
    cols = ['BPSYS', 'BPDIAS']
    offsets = [-0.2, 0.2]
    colors = ['red', 'blue']
    hatchs = ['o', '^']
    for col, offset, color, hatch in zip(cols, offsets, colors, hatchs):
        year, val, std = weighted_mean_std_by_year(df, col)
        plot_val_lower_upper(
            year + offset,
            val,
            std,
            std,
            ax,
            color=color,
            marker=hatch,
            label=col
        )
    ax.set_ylim(0, 200)
    ax.set_ylabel('Blood Pressure (mmHg)')
    ax.set_title(
        'Mean and STD of systolic and diastolic BP over time', y=1.05)
    legend = ax.legend(cols, loc='upper center', bbox_to_anchor=(0.5, 1.075),
                       fancybox=True, ncol=2)
    legend.get_frame().set_edgecolor('none')
    legend.get_frame().set_zorder(1)
    return ax


def plot_mean_and_ci_over_time(df, ax):
    '''
    Show SBP, DBP - weighted over time with pointplot
    '''
    cols = ['BPSYS', 'BPDIAS']
    offsets = [-0.2, 0.2]
    colors = ['red', 'blue']
    hatchs = ['o', '^']
    for col, offset, color, hatch in zip(cols, offsets, colors, hatchs):
        year, val, lower, upper = weighted_mean_ci_by_year(df, col)
        plot_val_lower_upper(
            year + offset,
            val,
            val - lower,
            upper - val,
            ax,
            color=color,
            marker=hatch,
            label=col
        )
    ax.set_ylim(0, 200)
    ax.set_ylabel('Blood Pressure (mmHg)')
    ax.set_title(
        'Mean and CI of systolic and diastolic BP over time', y=1.05)
    legend = ax.legend(cols, loc='upper center', bbox_to_anchor=(0.5, 1.075),
                       fancybox=True, ncol=2)
    legend.get_frame().set_edgecolor('none')
    legend.get_frame().set_zorder(1)
    return ax


def plot_htn_proportion_over_time(df, htn_definition, ax):
    '''
    Show the proportion of hypertensive emergency range BP over time
    '''
    df['HAS_HTN'] = htn_definition.get_triage_htn()

    vals = df.groupby('YEAR').apply(
        lambda df: weighted_proportion(df['HAS_HTN'], df.PATWT))
    ax.plot(vals.index.astype(int), vals)
    ax.scatter(vals.index.astype(int), vals)

    ax.set_ylim(0, 0.1)

    ax.set_title(
        f'Proprtion of SBP >{htn_definition.sbp_cutoff} or DBP > {htn_definition.dbp_cutoff} over time')
    return ax


def build_time_series_multiplot(df, htn_definition):
    fig = plt.figure(figsize=(14, 10))
    gspec = gs.GridSpec(2, 2)
    ax0 = plt.subplot(gspec[0, :])
    ax1 = plt.subplot(gspec[1, 0])
    ax2 = plt.subplot(gspec[1, 1])

    plot_mean_std_over_time(df, ax0)
    plot_mean_and_ci_over_time(df, ax1)
    plot_htn_proportion_over_time(df, htn_definition, ax2)

    return fig


if __name__ == "__main__":
    df = pd.read_pickle('./outputs/working_dataframe.pkl')
    htn_definition = Htn_definition(df, sbp_cutoff=180, dbp_cutoff=110)
    build_time_series_multiplot(df, htn_definition)
    plt.show()
