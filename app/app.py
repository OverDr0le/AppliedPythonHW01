import streamlit as st
import os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go

from modules.data_load_process import df_loader,get_rolling_mean,get_statistics
from modules.Anomalies_process import AnomalyAnalyzer,get_anomalies_for_city
from modules.requests_worker import get_async_response

load_dotenv()
API_KEY = os.getenv("API_KEY") # Загружаем апи ключ из переменных окружения


