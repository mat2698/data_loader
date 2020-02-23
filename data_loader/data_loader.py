# import some modules
import pandas as pd
import pandas_datareader.data as web
import datetime
import pickle


def create_returns_subset(dataset, date_range):
    return dataset[1].loc[date_range[0]:date_range[1]]


def create_returns_dataset(fund_id, asset_ids, frequency=None, allow_NA=False):
    # fund
    if (frequency == 'monthly'):
        df_price = create_data(fund_id, 'monthly')[['Adj Close']]
    else:
        df_price = create_data(fund_id)[['Adj Close']]

    df_fund_ret = df_price[['Adj Close']].pct_change()[1:]  # drops first row
    df_fund_ret = df_fund_ret.rename(columns={'Adj Close': fund_id})  # rename column

    # assets
    ids_with_na = []  # check for NA's
    df_assets_ret = None  # initialize just to be able to check in loop

    for idx, id in enumerate(asset_ids):

        if frequency == 'monthly':
            df_price = create_data(id, 'monthly')[['Adj Close']]
        else:
            df_price = create_data(id)[['Adj Close']]

        df_ret = df_price[['Adj Close']].pct_change()[1:]  # drops first row
        df_ret = df_ret.rename(columns={'Adj Close': id})  # rename column

        if df_ret.isnull().values.any():
            ids_with_na.append(id)

        # if does not exist, assign first asset return
        if df_assets_ret is None:
            df_assets_ret = df_ret
        else:
            df_assets_ret = df_assets_ret.merge(df_ret, how='left', left_index=True, right_index=True)

    if not allow_NA:
        if len(ids_with_na):
            msg = '*** ERROR *** Missing data... \n'
            msg += "  Following ids have missing data (i.e. NA's) during date range requested" + '\n'
            msg += "  {}".format(','.join(ids_with_na))
            raise Exception(msg)

    return df_fund_ret, df_assets_ret


def create_data(ticker, frequency=None):
    old_start_date_string = '1928-01'
    month = '{:02d}'.format(datetime.datetime.today().month)
    old_end_date_string = '{0}-{1}'.format(datetime.datetime.today().year, month)
    decrement_start = 2
    decrement_end = 1
    year_start = int(old_start_date_string[:-3])
    month_start = int(old_start_date_string[-2:])
    year_end = int(old_end_date_string[:-3])
    month_end = int(old_end_date_string[-2:])
    month_start = month_start - decrement_start
    month_end = month_end + decrement_end
    if month_start < 1:
        month_start = 12
        year_start = year_start - 1

    if month_end > 12:
        month_end = 1
        year_end = year_end + 1

    new_start_date = str(year_start) + '-{:02d}'.format(month_start)
    new_end_date = str(year_end) + '-{:02d}'.format(month_end)

    # Creates vector containing all dates in period
    dates = pd.date_range(new_start_date, new_end_date)
    dates = dates.to_frame()

    # Pulls historical price data for given ticker
    try:
        item_data = pickle.load(open("{}.pickle".format(ticker), "rb"))
    except (OSError, IOError) as e:
        item_data = web.DataReader(ticker, 'yahoo', '1928-01')
        pickle.dump(item_data, open("{}.pickle".format(ticker), "wb"))

    # Merges price data with full set of dates to account for missing dates.
    updated_data = dates.merge(right=item_data['Adj Close'], how='left', left_index=True, right_index=True)
    updated_data = updated_data.fillna(method='ffill')

    if frequency == 'monthly':
        month_ends = pd.date_range(new_start_date, new_end_date, freq='M')
        month_ends = month_ends.to_frame()
        updated_data = month_ends.merge(updated_data['Adj Close'], left_index=True, right_index=True)

    return updated_data


if __name__ == "__main__":
    print(" ")