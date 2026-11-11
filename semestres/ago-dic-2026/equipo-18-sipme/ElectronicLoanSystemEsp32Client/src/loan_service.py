from request_manager import Request
import constants

class LoanService:
    def __init__(self, auth_service):
        self.auth_service = auth_service

    def create_student_loan(self, material_id: int):
        if self.auth_service.isAuth():
            data = {"materialId": material_id}
            return Request.post(
                f"{constants.api_base_uri}/loans/student",
                data,
                headers={"Authorization": "Bearer " + self.auth_service.getToken()}
            )
        raise Exception("No auth")
