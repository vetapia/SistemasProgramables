from request_manager import Request
import constants

class BucketService:
    def __init__(self, auth_service):
        self._auth_service = auth_service

    def get_count_bucekts(self):
        if self._auth_service.isAuth():
            return Request.get(f"{constants.api_base_uri}/bucket/count", headers={
                "Authorization": "Bearer " + self._auth_service.getToken()
                })
        raise Exception("No auth")

    def get_materials(self, bucket_id: int, page: int = 1, size: int = 4):
        if self._auth_service.isAuth():
            return Request.get(
                f"{constants.api_base_uri}/bucket/{bucket_id}/materials?page={page}&size={size}",
                headers={
                    "Authorization": "Bearer " + self._auth_service.getToken()
                }
            )
        raise Exception("No auth")
