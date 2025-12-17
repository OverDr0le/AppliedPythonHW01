from datetime import date
import httpx

async def get_async_response(cityname,key):
    '''
    Эта функция возвращает json response и текущую дату
    '''
    url = f"http://api.openweathermap.org/data/2.5/weather?q={cityname}&appid={key}&units=metric"
    async with  httpx.AsyncClient() as client:
        response = await client.get(url)
    data = response.json()
    return data,date.today()