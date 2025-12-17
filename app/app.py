import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from modules.data_load_process import df_loader,get_rolling_mean,get_statistics
from modules.Anomalies_process import AnomalyAnalyzer
from modules.requests_worker import get_async_response



def main():
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
            data_stats = get_statistics(data)
            if st.button('Построить исторические температурные графики'):
                rolling_mean = get_rolling_mean(data,city_name)
                analyser = AnomalyAnalyzer(data_stats)
                anomalies = data.iloc[analyser.get_anomalyes_indexes(data)]

                
                fig = go.Figure()

                analyser = AnomalyAnalyzer(data_stats)
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


            


                
            api_key = st.text_input("Введите свой API-key")




if __name__ == '__main__':
    main()   
    


