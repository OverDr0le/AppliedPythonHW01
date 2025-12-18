import streamlit as st
import plotly.graph_objects as go
from datetime import date
import asyncio
import pandas as pd

from modules.data_load_process import df_loader, get_rolling_mean, get_statistics
from modules.Anomalies_process import AnomalyAnalyzer
from modules.requests_worker import get_async_response

async def main():

    st.set_page_config(
        page_title='Weather Analysis AI',
        page_icon=":cloud:",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Этот красивый CSS мне подсказала LLM
    st.markdown("""
    <style>
        /* Главный контейнер */
        .main {
            background-color: #f0f2f6;
        }
        /* Стиль для текста поверх баннера */
        .hero-container {
            position: relative;
            text-align: center;
            color: white;
            margin-bottom: 2rem;
        }
        .hero-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 45px !important;
            font-weight: 800;
            text-shadow: 3px 3px 15px rgba(0,0,0,0.8);
            width: 100%;
        }
        /* Улучшение видимости заголовков и меток */
        h1, h2, h3 {
            color: #1e3d59;
            font-family: 'Inter', sans-serif;
        }
        [data-testid="stMetricLabel"] p {
            font-size: 1.1rem !important;
            color: #434343 !important;
            font-weight: bold !important;
        }
        /* Карточки для контента */
        .st-emotion-cache-1r6slb0 {
            border-radius: 15px;
            border: 1px solid #e0e0e0;
            padding: 20px;
        }
    </style>
    """, unsafe_allow_html=True)


    winter_img = "https://images.pexels.com/photos/772476/pexels-photo-772476.jpeg"
    
    st.markdown(f"""
        <div class="hero-container">
            <img src="{winter_img}" style="width:100%; border-radius: 15px; height: 300px; object-fit: cover; filter: brightness(0.7);">
            <div class="hero-text">Анализ и мониторинг температур с помощью WeatherAPI</div>
        </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("Конфигурация данных")
        uploaded_file = st.file_uploader('Загрузите CSV-файл с историческими температурными данными', type=['csv'])
        st.info('Формат: city, timestamp, temperature, season')
        
        st.divider()
        api_key = st.text_input("Ключ WeatherAPI", type="password", help="Введите ваш API ключ для live-мониторинга")
        
        if uploaded_file is None:
            st.warning("Пожалуйста, загрузите CSV для полного анализа.")

    data = None
    analyser = None

    if uploaded_file is not None:
        df_loader_cached = st.cache_data(df_loader) #Кэшируем функцию для более быстрой обработки
        data = df_loader_cached(uploaded_file)
        
        if not set(['city','timestamp', 'season','temperature']).issubset(data.columns):
            st.error('Ошибка в структуре CSV! Проверьте названия колонок.')
            st.stop()
        
        data_stats = get_statistics(data)
        analyser = AnomalyAnalyzer(data_stats)

        with st.expander("Превью загруженных данных"):
            st.dataframe(data.head(10), width='stretch')

    tab1, tab2, tab3 = st.tabs(["Анализ исторических данных", "Мониторинг температуры", "Сезонные температурные профили"])

    with tab1:
        if data is not None:
            col_a, col_b = st.columns([1, 2])
            
            with col_a:
                st.subheader("Выбор города")
                city_name = st.selectbox("Город из температурных данных для анализа", data['city'].unique())
                
                if st.button(f'Рассчитать статистики по {city_name}'):
                    st.write(data[data['city']==city_name].describe())
            
            with col_b:
                st.subheader("Визуализация температурных трендов")
                if st.button('Построить графики'):
                    rolling_mean = get_rolling_mean(data, city_name)
                    anomalies_idx = analyser.get_anomalyes_indexes(data)
                    anomalies = data.iloc[anomalies_idx]
                    city_data = data[data['city'] == city_name]
                    city_anomalies = anomalies[anomalies['city'] == city_name]

                    fig = go.Figure()
                    
                    # Временной ряд температур
                    fig.add_trace(go.Scatter(
                        x=city_data['timestamp'], y=city_data['temperature'],
                        name="Температура", mode='lines', line=dict(color='blue', width=1)
                    ))
                    
                    # Скользящее среднее
                    fig.add_trace(go.Scatter(
                        x=rolling_mean['timestamp'], y=rolling_mean['temperature'],
                        name="Скользящее среднее", line=dict(color='green', width=3)
                    ))
                    
                    # Аномалии
                    fig.add_trace(go.Scatter(
                        x=city_anomalies['timestamp'], y=city_anomalies['temperature'],
                        name='Аномалии', mode='markers', marker=dict(color='red', size=8, symbol='x')
                    ))

                    fig.update_layout(
                        template="plotly_white",
                        hovermode="x unified",
                        margin=dict(l=20, r=20, t=40, b=20),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig, width='stretch')
        else:
            st.info("Загрузите CSV-файл в боковой панели, чтобы увидеть аналитику по историческим данным.")

    with tab2:
        st.subheader("Текущая погода в реальном времени")
        col_c, col_d = st.columns([1, 1])
        
        with col_c:
            any_city = st.text_input("Введите название города", placeholder="Moscow...") # Температуру можно получить для любого города
        
        if api_key and any_city:
            api_response_any = await get_async_response(any_city, api_key)
            
            if api_response_any.get('cod') == 200:
                temp = api_response_any['main']['temp']
                desc = api_response_any['weather'][0]['description']
                wind = api_response_any['wind']['speed']
                
                with col_d:
                    st.metric("Текущая температура", f"{round(temp)} °C", help=desc.capitalize())
                    st.write(f"Ветер: {wind} м/с, Погода: {desc}")

                # Аномальна ли температура?
                if data is not None and any_city in data['city'].unique():
                    is_anomaly = analyser.anomaly_check(temp, any_city, date.today())
                    if is_anomaly:
                        st.error(f"Температура {temp}°C является аномальной для данного сезона в {any_city}, будьте осторожнее!")
                    else:
                        st.success("Температура в пределах нормы для текущего сезона.")
            else:
                st.error(f"Ошибка API: {api_response_any.get('message')}")
        elif not api_key:
            st.warning("Введите API ключ в боковом меню.")

    with tab3:
        st.subheader("Анализ сезонных профилей")
        profile_city = st.text_input("Город для изучения профиля", key="profile_input")
        
        if data is not None and profile_city:
            if profile_city in data['city'].unique():
                stats = get_statistics(data[data['city']==profile_city])
                st.dataframe(
                    stats.reset_index().drop('city', axis=1).set_index('season'),
                    width='stretch'
                )
            else:
                st.error(f"Город '{profile_city}' не найден в исторических данных.")
        elif data is None:
            st.info("Требуется загрузка CSV файла.")

if __name__ == '__main__':
    asyncio.run(main())