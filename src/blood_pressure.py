import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency
from stats import weighted_proportion, weighted_chi2, weighted_contingency

pd.set_option('display.max_columns', None)  # None means unlimited
pd.set_option('display.width', None)


class CategoricalStats():
    '''
    Contains methods for generating the base characteristics tables 
    Args:
    # df - working dataframe

    # htn_definition - from Htn_definition class, gives BP cutoff values
    and has a function to get the patients with hypertension by the definition

    # queries - should be a dictionary with col_name: kind where kind is 
    'binomial' or 'multinomial' which indicates if it sa binary category or if 
    it contains more than 2 category types.

    Example use:
    df = ....
    htn_def = Htn_definition(df, 200, 120)
    stats = CategoricalStats(df, queries, htn_def)
    print(stats.get_stats())
    '''

    def __init__(self, df, query_dict, htn_definition):
        self.df = df
        self.htn_definition = htn_definition
        self.queries = self.build_queries(query_dict)
        self.stats_table = self.build_stats_table()

    def build_queries(self, query_dict):
        queries = []
        for column_name, kind in query_dict.items():
            new_query = Query(column_name, kind)
            queries.append(new_query)
        return queries

    def process_binomial_query(self, query):
        print(f'Processing query - {query.column_name}, {query.kind}')
        has_htn = self.htn_definition.get_triage_htn()
        weights = self.get_weights()

        # column to calculate stats on
        col = self.df[query.column_name]

        # make sure it's a binary column of 0/1 values
        assert set(col) == {
            0, 1}, f"{query.column_name}, does not seem to be binary"

        # patiehts with htn
        ser1 = col[has_htn]
        weights1 = weights[ser1.index]
        # patiehts without htn
        ser2 = col[~has_htn]
        weights2 = weights[ser2.index]

        # calculate p value with chi2
        # indexing weights is addressed in the weighted_chi2 function
        p_value = weighted_chi2(ser1, ser2, weights)

        # all values reported as millions or proportions
        table = pd.DataFrame({
            'n_total': sum(col * weights) / 1e6,
            'n_nohtn': sum(ser2 * weights[ser2.index]) / 1e6,
            'n_htn': sum(ser1 * weights[ser1.index]) / 1e6,
            # proportion of patients of the category
            'proportion_total': weighted_proportion(col, weights),
            # proportion of patients of the category and no HTN
            'proportion_nohtn': weighted_proportion(ser2, weights2),
            # proportion of patients of the category and WITH HTN
            'proportion_htn': weighted_proportion(ser1, weights1),
            'p_value': p_value
        }, index=[query.column_name])
        return table

    def process_multinomial_query(self, query):
        print(f'Processing query - {query.column_name}, {query.kind}')
        col = self.df[query.column_name]
        weights = self.get_weights()
        has_htn = self.htn_definition.get_triage_htn()
        # htn patients
        ser1 = self.df.loc[has_htn, query.column_name]
        weights1 = weights[ser1.index]
        # no htn patients
        ser2 = self.df.loc[~has_htn, query.column_name]
        weights2 = weights[ser2.index]
        # indexing weights is addressed in the weighted_chi2 function
        contingency_table = weighted_contingency(ser1, ser2, weights)
        _, p_value, _, _ = chi2_contingency(contingency_table)

        table = pd.DataFrame()

        for category in col.unique():
            new_row = pd.DataFrame({
                'n_total': sum((col == category) * weights) / 1e6,
                'n_nohtn': sum((ser2 == category) * weights[ser2.index]) / 1e6,
                'n_htn': sum((ser1 == category) * weights[ser1.index]) / 1e6,
                # proportion of patients of the category
                'proportion_total': weighted_proportion((col == category), weights),
                # proportion of patients of the category and WITHOUT HTN
                'proportion_nohtn': weighted_proportion((ser2 == category), weights2),
                # proportion of patients of the category and WITH HTN
                'proportion_htn': weighted_proportion((ser1 == category), weights1),
                'p_value': p_value
            }, index=[query.column_name + '_' + str(category)])
            table = pd.concat([table, new_row])
        return table

    def build_stats_table(self):
        '''
        Create a totals row that gives the sums for groups
        Go through all the queries and add them to a dataframe (binomial and
        multinomial)
        '''

        # calculate totals
        weights = self.get_weights()
        has_htn = self.htn_definition.get_triage_htn()
        total = weights.sum()
        without_htn = (weights * ~has_htn).sum()
        with_htn = (weights * has_htn).sum()

        # the first row is just the totals - not reflective of categories
        table = pd.DataFrame({
            'n_total': total / 1e6,
            'n_nohtn': without_htn / 1e6,
            'n_htn': with_htn / 1e6,
            'proportion_total': 1,
            'proportion_nohtn': without_htn / total,
            'proportion_htn': with_htn / total,
            'p_value': np.NAN
        }, index=['TOTALS'])

        for q in self.queries:
            if q.kind == 'binomial':
                new_rows = self.process_binomial_query(q)
                table = pd.concat([table, new_rows])
            else:
                new_rows = self.process_multinomial_query(q)
                table = pd.concat([table, new_rows])
        return table

    def get_stats(self):
        return self.stats_table

    def get_cvo(self):
        # return boolean indicator of cardiac outcome or not
        return self.df.HTN_COMPLICATION

    def get_weights(self):
        return self.df.PATWT


class Htn_definition():
    def __init__(self, htn_data, sbp_cutoff, dbp_cutoff):
        self.sbp_cutoff = sbp_cutoff
        self.dbp_cutoff = dbp_cutoff
        self.SBP = htn_data['BPSYS']  # triage SBP
        self.DBP = htn_data['BPDIAS']  # triage DBP
        self.SBPD = htn_data['BPSYSD']  # SBP taken after triage
        self.DBPD = htn_data['BPDIASD']  # DBP taken after triage

    def get_triage_htn(self):
        return (self.SBP > self.sbp_cutoff) | (self.DBP > self.dbp_cutoff)


class Query():
    def __init__(self, column_name, kind):
        self.column_name = column_name
        self.kind = kind


if __name__ == "__main__":
    df = pd.read_pickle(
        ('./outputs/working_dataframe.pkl'))

    queries = {
        'SEX': 'multinomial',
        'XRAY': 'binomial',
        'CBC': 'binomial',
    }
    htn_def = Htn_definition(df, 200, 120)
    stats = CategoricalStats(df, queries, htn_def)
    print(stats.get_stats())
