import constants
from request_manager import Request

class AuthService:
    STATIC_CONTROL_NUMBER = "21210001"

    def __init__(self):
        self._token = ""
        self._isAuth = False
        self._user = None
        
    def login(self, email: str, password: str):
        if not self._isAuth:
            data = {
                "email": email,
                "password": password
            }

            response = Request.post(f"{constants.api_base_uri}/auth/login/esp", data)
            response_json = response.json()
            self._token = response_json["token"]
            self._user = response_json["user"]

    def loginWithNumberAndPin(self, controlNumber: str, pin: str):
        if not self._isAuth:
            data = {
                "controlNumber": controlNumber,
                "nip": pin
            }

            response = Request.post(f"{constants.api_base_uri}/auth/login/esp", data)
            response_json = response.json()
            self._token = response_json["token"]
            self._user = response_json["user"]
            self._isAuth = True

    def isAuth(self):
        return self._isAuth

    def getToken(self):
        return self._token 

    def get_user(self):
        return self._user

    def get_control_number(self):
        return self.STATIC_CONTROL_NUMBER
