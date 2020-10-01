import requests
import ast

def bitstamp_requests(request_parameter: str, currency_pair: str = None,
                      data: dict = None) -> dict:

    request_content = {}
    r = requests.post(
        'https://www.bitstamp.net/api/v2/' + \
        request_parameter + \
        '/' + \
        currency_pair,
        params = data
    )

    if not r.status_code == 200:
        raise Exception('Status code not 200, Error: {status_code}'.format(status_code=r.status_code))
    dict_str = r.content.decode("UTF-8")
    request_content = ast.literal_eval(dict_str)
    string_to_float(request_content)

    return(request_content)

def string_to_float(dictionary: dict) -> dict:

    for key in dictionary:
        try:
            dictionary[key] = float(dictionary[key])
        except Exception:
            pass

    return dictionary
