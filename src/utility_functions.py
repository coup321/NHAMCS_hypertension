import re


def diagnosis_filter(df, pattern):
    # create a single column boolean indicator that marks if a text
    # sequence was in any of the DIAG columns
    data = df[['DIAG1', 'DIAG2', 'DIAG3', 'DIAG4', 'DIAG5']]
    indicator = data.apply(lambda col: col.str.contains(
        pattern, regex=True, case=False)).any(axis=1)
    return indicator


def unmeasured_bps(raw_df, col):
    '''
    BP columns contain blanks
    The blanks will be replaced with NANs for the analysis
    Need to quantify blanks as they likely indicate unmeasured values (I think)
    This is a function that takes
     - raw_df
     - column (must be a BP sys, dias, or sysd, or diasd) 
    Will print the relevent values and proportions
    '''

    if col not in ['BPSYS', 'BPDIAS', 'BPSYSD', 'BPDIASD']:
        return ValueError
    print(f'Total size of the {col} column: {len(raw_df[col])}')
    unmeasured = sum(raw_df[col] == "Blank")
    measured = sum(~(raw_df[col] == "Blank"))
    print(f'Number of measured: {measured}')
    print(f'Number of un-measured: {unmeasured}')
    print(f'Percent measured = {100 * measured / (measured + unmeasured)}')
    print('\n')


def get_regex_cols(df, regex, not_equal_to=None):
    """
    This function takes a dataframe and returns all the columns that match a specific
    regular expresion. not_equal_to is a list of matches to exclude
    """
    cols = []
    for col in df.columns:
        if not_equal_to is None:
            if re.search(regex, col, flags=re.IGNORECASE):
                cols.append(col)
        else:
            if re.search(regex, col, flags=re.IGNORECASE) and col not in not_equal_to:
                cols.append(col)
    return cols


def column_equivelancy(dfs, column_regex):
    # simple loop to check column equivelancy between NHAMCS years
    years = [df.YEAR.values[0] for df in dfs]
    for year, df in zip(years, dfs):
        print(year, get_regex_cols(df, column_regex))


def map_timerange(time):
    if time >= 7 and time < 15:
        return '7a-3p'
    elif time >= 15 and time < 23:
        return '3p-11p'
    else:
        return '11p-7a'
