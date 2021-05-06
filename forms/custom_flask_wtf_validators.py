import requests
from wtforms.validators import ValidationError

def known_location(form, field):
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

    geocoder_params = {
    "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
    "geocode": field.data,
    "format": "json"}

    response = requests.get(geocoder_api_server, params=geocoder_params)

    if not response:
        raise ValidationError("""Ошибка сервисов Яндекса, приходите позже""")

    json_response = response.json()
    try:
        # Получаем первый топоним из ответа геокодера.
        toponym = json_response["response"]["GeoObjectCollection"][
        "featureMember"][0]["GeoObject"]
    except Exception:
        raise ValidationError("""Такого адреса/организации/объекта не найдено. Уточните данные""")
    
    # Координаты центра топонима:
    toponym_coodrinates = toponym["Point"]["pos"]
    # Долгота и широта:
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")

    return toponym_longitude, toponym_lattitude
