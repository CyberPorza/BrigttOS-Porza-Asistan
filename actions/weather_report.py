# actions/weather_report.py
# CyberPorza Weather Report Module

import webbrowser
from urllib.parse import quote_plus


def weather_action(
    parameters: dict,
    player=None,
    session_memory=None
):
    """
    Weather report action.
    Opens a Google weather search and gives a short spoken confirmation.
    """

    city = parameters.get("city")
    time_val = parameters.get("time")
    if not city or not isinstance(city, str):
        msg = "Hava durumu için şehri belirtmen lazım kankam."
        _speak_and_log(msg, player)
        return msg

    city = city.strip()

    if not time_val or not isinstance(time_val, str):
        time_val = "bugün"
    else:
        time_val = time_val.strip()

    search_query = f"{city} hava durumu {time_val}"
    encoded_query = quote_plus(search_query)
    url = f"https://www.google.com/search?q={encoded_query}"

    try:
        webbrowser.open(url)
    except Exception:
        msg = "Hava durumunu göstermek için tarayıcıyı açamadım kankam."
        _speak_and_log(msg, player)
        return msg

    msg = f"{city} için {time_val} hava durumunu ekrana getiriyorum kankam."
    _speak_and_log(msg, player)

    if session_memory:
        try:
            session_memory.set_last_search(
                query=search_query,
                response=msg
            )
        except Exception:
            pass  

    return msg


def _speak_and_log(message: str, player=None):
    print(f"[PORZA-WEATHER] ☁️ {message}")
    if player:
        try:
            player.write_log(f"CYBER-WEATHER: {message}")
        except Exception:
            pass