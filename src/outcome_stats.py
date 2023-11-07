'''
For patients +/- hypertension, get the relative risk for outcomes
'''
import pandas as pd
from stats import weighted_relative_risk, weighted_mean_difference_and_ci
from blood_pressure import Htn_definition
from plot_category_by_bp import plot_category
import matplotlib.pyplot as plt
import numpy as np


class OutcomeQuery():
    def __init__(self, outcome, kind):
        self.outcome = outcome
        self.kind = kind


class OutcomeStats():
    '''
    Contains methods to generate the outcome statistics table and also the
    outcome vs blood pressure plots for multiple outcomes.

    Parameters:
    df = modified dataframe from the build_dataframe module
    htn_definition = class the holds bp cutoff variables and can create
    a boolean filter for if a patient has hypertension.
    queries = list of lists containing [['outcome col name',
    'categorical|numeric']]

    EXAMPLE:
    df = pd.read_pickle(
        ('./outputs/working_dataframe.pkl'))
    queries = [
        ['DIED', 'categorical'],
        ['BPSYS', 'numeric'],
    ]

    htn_definition = Htn_definition(df, sbp_cutoff=90, dbp_cutoff=50)
    stats = OutcomeStats(df, htn_definition, queries)
    fig, axes = stats.plot_queries()
    plt.show()
    print(stats())
    '''

    def __init__(self, df, htn_definition, queries):
        self.df = df
        self.htn_definition = htn_definition
        self.queries = self.build_queries(queries)
        self.stats_table = None

    def build_queries(self, queries):
        '''
        the queries are passed as a list of lists parameter, this makes them
        into query objects
        '''
        list_of_query_objects = []
        for q in queries:
            outcome, kind = q
            new_query = OutcomeQuery(outcome, kind)
            list_of_query_objects.append(new_query)
        return list_of_query_objects

    def process_categorical_query(self, query):
        '''
        process a categorical query (binomial or multinomial) and return the
        RR, LCI, UCI of the RR
        '''
        print(f'Processing outcome - {query.outcome}, {query.kind}')
        exposure = self.htn_definition.get_triage_htn()  # boolean of some HTN cutoff
        outcome = self.df[query.outcome]  # boolean of some outcome
        weights = self.df['PATWT']

        ser1 = outcome[~exposure]  # boolean outcome in NOT exposed
        ser2 = outcome[exposure]  # boolean outcome in exposed
        w1 = weights[ser1.index]
        w2 = weights[ser2.index]
        RR, LCI, UCI = weighted_relative_risk(ser1, ser2, w1, w2)

        return RR, LCI, UCI

    def process_numeric_query(self, query):
        '''
        return the weighted difference between two numeric series and
        also the CI for the difference
        '''
        print(f'Processing outcome - {query.outcome}, {query.kind}')
        exposure = self.htn_definition.get_triage_htn()  # boolean of some HTN cutoff
        outcome = self.df[query.outcome]  # numeric series of some value
        weights = self.df['PATWT']

        ser1 = outcome[~exposure].dropna()  # outcome when NOT exposed
        ser2 = outcome[exposure].dropna()  # outcome when exposed
        w1 = weights.loc[ser1.index]
        w2 = weights.loc[ser2.index]
        mean_difference, LCI, UCI = weighted_mean_difference_and_ci(
            ser1, ser2, w1, w2)
        return mean_difference, LCI, UCI

    def categorical_query_counts(self, query):
        '''
        Return the counts for a categorical query - giving the raw numbers for
        the table
        '''
        exposure = self.htn_definition.get_triage_htn()  # boolean of some HTN cutoff
        outcome = self.df[query.outcome]  # boolean series of some value
        weights = self.df['PATWT']

        n_not_exposed = sum(~exposure * weights) * 1e-6
        n_exposed = sum(exposure * weights) * 1e-6
        n_outcome_not_exposed = sum(
            outcome[~exposure] * weights[~exposure]) * 1e-6
        n_outcome_exposed = sum(outcome[exposure] * weights[exposure]) * 1e-6

        return (
            f'{n_outcome_not_exposed:.1f} ({100 * n_outcome_not_exposed / n_not_exposed:.1f}%)',
            f'{n_outcome_exposed:.1f} ({100 * n_outcome_exposed / n_exposed:.1f}%)',
        )

    def numeric_mean_values(self, query):
        '''
        Get the mean values for a numerical query
        '''
        exposure = self.htn_definition.get_triage_htn()  # boolean of some htn cutoff
        outcome = self.df[query.outcome]  # numeric series of some value
        weights = self.df['PATWT']

        exposed_mean = outcome[exposure].dropna().mean()
        not_exposed_mean = outcome[~exposure].dropna().mean()
        return f'{not_exposed_mean:.0f}', f'{exposed_mean:.0f}'

    def build_stats_table(self):
        '''
        build the stats table by making a totals row and then processing each 
        query and adding the rows
        '''

        # make htn (exposure) column from htn_definition
        exposure = self.htn_definition.get_triage_htn()

        table = pd.DataFrame({
            'KIND': '-',
            'NOT_EXPOSED': f"{sum(~exposure * self.df['PATWT']) * 1e-6:.2f}",
            'EXPOSED': f"{sum(exposure * self.df['PATWT']) * 1e-6: .2f}",
            'RR/DIFF': '-',
            'LCI': '-',
            'UCI': '-',
        }, index=['TOTAL'])
        for query in self.queries:
            if query.kind == 'categorical':
                RR_OR_DIFF, LCI, UCI = self.process_categorical_query(query)
                not_exposed_value, exposed_value = self.categorical_query_counts(
                    query)
            elif query.kind == 'numeric':
                # DIFF = mean_difference
                RR_OR_DIFF, LCI, UCI = self.process_numeric_query(query)
                not_exposed_value, exposed_value = self.numeric_mean_values(
                    query)
            else:
                return ValueError()
            new_row = pd.DataFrame({
                'KIND': query.kind,
                'NOT_EXPOSED': not_exposed_value,
                'EXPOSED': exposed_value,
                'RR/DIFF': RR_OR_DIFF,
                'LCI': LCI,
                'UCI': UCI,
            }, index=[query.outcome])
            table = pd.concat([table, new_row])
        self.stats_table = table
        return table

    def get_stats(self):
        if self.stats_table:
            return self.stats_table
        else:
            # build stats table
            self.build_stats_table()
        return self.stats_table

    def plot_queries(self):
        '''
        Plot blood pressure vs category for all the queries and put them
        all in a big multi-plot
        '''
        nrows = int(np.ceil(len(self.queries) / 4))
        fig, axes = plt.subplots(ncols=4, nrows=nrows,
                                 constrained_layout=True, figsize=(18, 10))
        axes = (x for x in axes.flatten())

        for q in self.queries:
            category = q.outcome
            ax = next(axes)
            plot_category(self.df, ax, category, q.kind)
        return fig, axes

    def __call__(self):
        return self.get_stats()


if __name__ == "__main__":
    df = pd.read_pickle(
        ('./outputs/working_dataframe.pkl'))
    queries = [
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
    htn_definition = Htn_definition(df, sbp_cutoff=90, dbp_cutoff=50)
    stats = OutcomeStats(df, htn_definition, queries)
    fig, axes = stats.plot_queries()
    plt.show()
    print(stats())
