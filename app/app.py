import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import asyncio

from modules.data_load_process import df_loader,get_rolling_mean,get_statistics
from modules.Anomalies_process import AnomalyAnalyzer
from modules.requests_worker import get_async_response



async def main():
    st.set_page_config(
    page_title='Анализ и мониторинг температурных данных с помощью WeatherApi',
    page_icon=":cloud:",
    layout="wide",
    initial_sidebar_state="expanded"
    )

    st.header(
        "Загрузка исторических температурных данных"
    )
    uploaded_file = st.file_uploader('Выберите CSV-файл', type =['csv'])
    st.caption('Убедитесь, что в загружаемой таблице есть поля **city, timestamp, temperature, season**')
    if uploaded_file is not None:
        df_loader_cached = st.cache_data(df_loader)
        data = df_loader_cached(uploaded_file) # Cashing loading func
        if set(data.columns) != set(['city','timestamp', 'season','temperature']):
            st.error('Названия колонок не совпадают, пожалуйста, загрузите корректный CSV-файл')
            st.stop() 
        st.write('Превью загруженных данных:')
        st.dataframe(data)
        data_stats = get_statistics(data)
        analyser = AnomalyAnalyzer(data_stats)
    else:
        st.write('Пожалуйста, загрузите CSV-файл')

    if uploaded_file is not None:
        st.header('Выбор города')
        city_name = st.selectbox("Выберите город из списка",data['city'].unique())
        if city_name is not None:
            if st.button(f'Получить описательные статистики по {city_name}'):
                with st.expander('Развернуть'):
                    st.dataframe(data[data['city']==city_name].describe())
            


            st.header(f"Анализ температурного временного ряда для {city_name}")

            if st.button('Построить исторические температурные графики'):
                rolling_mean = get_rolling_mean(data,city_name)
                anomalies = data.iloc[analyser.get_anomalyes_indexes(data)]

                
                fig = go.Figure()
                anomalies = data.iloc[analyser.get_anomalyes_indexes(data)]

                fig.add_trace(
                    trace=go.Scatter(
                    x=anomalies[anomalies['city']==city_name]['timestamp'],
                    y=anomalies[anomalies['city']==city_name]['temperature'],
                    mode = 'markers',
                    name = 'Аномальные температуры',
                    line = dict(color = 'red',width=1)
                    )
                )
                fig.add_trace(
                    trace=go.Scatter(
                        x=data[data['city']==city_name]['timestamp'],
                        y=data[data['city']==city_name]['temperature'],
                        name = "Температура",
                        mode = 'lines'
                    )
                )
                fig.add_trace(
                    trace=go.Scatter(
                        x=rolling_mean['timestamp'],
                        y=rolling_mean['temperature'],
                        name="Скользящее среднее",
                        mode = 'lines',
                        line=dict(color="green", width=3)
                    )
                )

                fig.update_layout(
                    title = 'Температурный временной ряд',
                    xaxis_title= 'Дата',
                    yaxis_title = 'Температура, °C'
                )
                st.plotly_chart(figure_or_data=fig)

    st.header("Мониторинг температуры воздуха")
    api_key = st.text_input("Введите API ключ WeatherAPI")
    st.write("Вы можете **не загружать CSV файл**. Получить температуру воздуха можно для **любого** города, но без анализа на аномальность.")
    if api_key != "":
        any_city=st.text_input("Введите название любого существующего города") # Дополнительный функционал для мониторинга температуры воздуха в любом городе
        st.caption("Если вы загрузили CSV файл, то при условии, что этот город есть в нём, вы можете также получить анализ на аномальность.")
        if any_city != '':
            api_response_any = await get_async_response(any_city,api_key)
            if api_response_any['cod'] == 200:
                temperature = api_response_any['main']['temp']
                st.write(f"Текущая температура воздуха {round(temperature)} °C, {api_response_any['weather'][0]['description']}, скорость ветра {api_response_any['wind']['speed']} м\с")
            else:
                st.error(api_response_any)

            if api_response_any['cod'] == 200 and uploaded_file is not None:
                if any_city in data['city'].unique():
                    if analyser.anomaly_check(temperature,any_city,date.today()):
                        st.write("Текущая температура воздуха является **аномальной**, будте осторожны!")
                    else:
                        st.write("Текущая температура воздуха находится в пределах нормы.")
                else:
                    st.write('По данному городу нет исторических данных')
        
    
    st.header("Сезонные температурные профили")
    profile_city = st.text_input("Введите название города")
    st.caption(f"Пожалуйста, убедитесь, что город представлен в загруженном CSV файле")
    if uploaded_file is not None:
        if profile_city is not "":
            if profile_city in data['city'].unique():
                with st.expander("Развернуть"):
                    st.dataframe(get_statistics(data[data['city']==profile_city]).reset_index().drop('city',axis=1).set_index('season'))
            else:
                st.error(f"{profile_city} не находится в загруженном CSV файле")
    else:
        st.write("Загрузите датасет!")
    




if __name__ == '__main__':
    asyncio.run(main())   
    


