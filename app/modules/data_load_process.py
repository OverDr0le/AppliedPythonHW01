from pandas import DataFrame,read_csv

def df_loader(link:str):
    if link.split('.')[1] != 'csv':
        raise ValueError('Ошибка формата ссылки, введите формат .csv')
    df = read_csv(link)
    return df


def get_rolling_mean(df:DataFrame,cityname:str) -> DataFrame:
    df_sorted = df[df.city==cityname].sort_values(by='timestamp',inplace=False,ascending=True)
    rolling_dict = {'timestamp':df_sorted['timestamp'],'temperature':df_sorted['temperature'].rolling(window=30).mean()}
    return DataFrame(rolling_dict)


def get_statistics(df:DataFrame) -> DataFrame:
    stats = df.groupby(['city','season'])['temperature'].agg(['mean','std'])
    return stats