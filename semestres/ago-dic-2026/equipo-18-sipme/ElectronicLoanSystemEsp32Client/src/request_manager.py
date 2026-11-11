import requests
import json

class Request:
    json_headers = {
        "Content-Type": "application/json"
    }
    
    @staticmethod
    def post(url: str = "", data: dict = {}, headers: dict = {}):
        data_to_json = Request._stringify(data)
        h = {"Content-Type": "application/json"}
        if headers:
            h.update(headers)
        return requests.post(url, data=data_to_json, headers=h)

    @staticmethod
    def get(url: str = "", headers: dict = {}):
        h = {"Content-Type": "application/json"}
        if headers:
            h.update(headers)
        return requests.get(url, headers=h)

    @staticmethod
    def _stringify(data):
        return json.dumps(data)
