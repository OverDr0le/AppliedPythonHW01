from pandas import DataFrame,read_csv
from concurrent.futures import ProcessPoolExecutor


def get_anomalies_for_city(city_df: DataFrame, statistics: DataFrame) -> list:
    '''
    Функция для вычисления температурных аномалий для определённого города
    возвращаемое значение: лист индексов в city_df
    '''
    anomalies = []

    for idx, row in city_df.iterrows():
        avg = statistics.loc[(row['city'], row['season']), 'mean']
        std = statistics.loc[(row['city'], row['season']), 'std']

        if row['temperature'] > avg + 2 * std or row['temperature'] < avg - 2 * std:
            anomalies.append(idx)

    return anomalies


class AnomalyAnalyzer():
    def __init__(self,statistics):
        self.statistics = statistics # Статистики mean,std рассчитаные для входных исторических данных по городам,сезонам
    
    def anomaly_check(self,temp, city, date):
        '''
        Функция для проверки текущей температуры на аномальность по историческим данным statistics
        '''
        month_to_season = {12: "winter", 1: "winter", 2: "winter",
                    3: "spring", 4: "spring", 5: "spring",
                    6: "summer", 7: "summer", 8: "summer",
                    9: "autumn", 10: "autumn", 11: "autumn"}
        season = month_to_season[int(date.month)]
        season_mean = self.statistics.loc[(city,season),'mean']
        season_std =  self.statistics.loc[(city,season),'std']
        if temp > season_mean+2*season_std or temp < season_mean-2*season_std:
            return True
        return False


    def get_anomalyes_indexes(self,df,n_threads=4):
        """
        Функция которая распараллеливает вычисление аномалий для всех городов в df
        Возвращаемое значение: список индексов аномалий в df
        """

        # Чтобы извлечь прирост к скорости из параллельности разобьём датасет на части по городам
        city_df_list = [
            city_df for _,city_df in df.groupby('city')
        ]

        with ProcessPoolExecutor(max_workers=n_threads) as executor:
            results = executor.map(
                get_anomalies_for_city,city_df_list,
                [self.statistics]*len(city_df_list) # дублируем статистики для корректной работы executor
                )
        
        anomalies = [idx for i in results for idx in i]
        return anomalies