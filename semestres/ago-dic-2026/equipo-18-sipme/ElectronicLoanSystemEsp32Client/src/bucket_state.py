from bucket_service import BucketService
from loan_service import LoanService

class BucketState:
    PAGE_SIZE = 4

    def __init__(self, auth_service, display, keypad, mqtt):
        self._bucket_selected = 0
        self._material_selected = None
        self._loan_result = None
        self._step = 0
        self._materials = []
        self._selected_index = 0
        self._current_page = 1
        self._has_next = False
        self._has_previous = False
        self._auth_service = auth_service
        self._bucket_service = BucketService(auth_service)
        self._loan_service = LoanService(auth_service)
        self._display = display
        self._keypad = keypad
        self._mqtt = mqtt

    def start(self):
        try:
            while True:
                if self._step == 0:
                    self._step_one()
                elif self._step == 1:
                    self._step_two()
                elif self._step == 2:
                    self._step_three()
                else:
                    return self._loan_result
        except Exception as e:
            raise e

    def _draw_base(self):
        user = self._auth_service.get_user()
        user_name = f"{user.get('name', '')} {user.get('lastName', '')}".strip() if isinstance(user, dict) else "Usuario"
        control_number = self._auth_service.get_control_number()
        self._display.draw_authenticated_base(user_name, control_number)

    def _step_one(self):
        self._draw_base()
        buckets_resp = self._get_count_buckets().json()
        max_buckets = int(buckets_resp) if isinstance(buckets_resp, (int, str)) and str(buckets_resp).isdigit() else 1

        self._display.draw_bucket_screen(max_buckets, self._bucket_selected)

        while True:
            key = self._keypad.get_key()
            if key is not None:
                if key == "C":
                    if 0 < self._bucket_selected <= max_buckets:
                        self._step = 1
                        return
                elif key == "*":
                    self._bucket_selected = 0
                    self._display.update_bucket_selected(self._bucket_selected)
                elif key.isdigit():
                    digit = int(key)
                    new_val = self._bucket_selected * 10 + digit if self._bucket_selected > 0 else digit
                    if new_val <= max_buckets:
                        self._bucket_selected = new_val
                    else:
                        self._bucket_selected = digit
                    self._display.update_bucket_selected(self._bucket_selected)

    def _step_two(self):
        self._draw_base()
        self._materials = []
        self._selected_index = 0
        self._current_page = 1
        self._has_next = False
        self._has_previous = False
        self._load_materials_page(1)
        self._display.draw_materials_screen(self._bucket_selected, self._materials, self._selected_index)

        while True:
            key = self._keypad.get_key()
            if key is not None:
                if key == "A":
                    if self._selected_index < len(self._materials) - 1:
                        self._selected_index += 1
                        self._display.update_materials_list(self._materials, self._selected_index)
                    elif self._has_next:
                        if self._load_materials_page(self._current_page + 1):
                            self._selected_index = 0
                            self._display.update_materials_list(self._materials, self._selected_index)
                elif key == "B":
                    if self._selected_index > 0:
                        self._selected_index -= 1
                        self._display.update_materials_list(self._materials, self._selected_index)
                    elif self._has_previous and self._current_page > 1:
                        if self._load_materials_page(self._current_page - 1):
                            self._selected_index = max(0, len(self._materials) - 1)
                            self._display.update_materials_list(self._materials, self._selected_index)
                elif key == "C":
                    if self._materials and 0 <= self._selected_index < len(self._materials):
                        self._material_selected = self._materials[self._selected_index]
                        self._step = 2
                        return
                elif key == "D":
                    self._step = 0
                    return

    def _step_three(self):
        mat_name = self._material_selected.get("name", "Material") if isinstance(self._material_selected, dict) else "Material"
        mat_id = self._material_selected.get("id", 0) if isinstance(self._material_selected, dict) else 0
        self._display.draw_confirm_loan_screen(mat_name, mat_id)

        while True:
            key = self._keypad.get_key()
            if key is not None:
                if key == "D":
                    self._step = 1
                    return
                elif key == "C":
                    self._display.show_loan_status("Creando prestamo...")
                    success, result = self._execute_loan(mat_id)
                    if success:
                        self._mqtt.publish(b"/buckets", b"/1/open")
                        self._loan_result = result
                        self._display.show_loan_success(mat_name)
                        while True:
                            k = self._keypad.get_key()
                            if k == "C":
                                self._step = 3
                                return
                    else:
                        error_text = "! Error al prestar\n" + result
                        self._display.show_loan_error(error_text)
                        while True:
                            k = self._keypad.get_key()
                            if k in ("C", "D"):
                                self._step = 1
                                return

    def _execute_loan(self, material_id: int):
        return True, ""
        try:
            resp = self._loan_service.create_student_loan(material_id)
            if hasattr(resp, "status_code"):
                if 200 <= resp.status_code < 300:
                    return True, resp.json()
                elif resp.status_code == 409:
                    return False, "Material en prestamo"
                else:
                    return False, f"Error {resp.status_code}"
            return True, resp.json()
        except Exception:
            return False, "Fallo de conexion"

    def _load_materials_page(self, page: int):
        response = self._bucket_service.get_materials(self._bucket_selected, page, self.PAGE_SIZE)
        data = response.json()
        if isinstance(data, dict):
            new_items = data.get("items", [])
            if new_items or page == 1:
                self._materials = new_items
                self._current_page = data.get("currentPage", page)
                self._has_next = bool(data.get("hasNext", False))
                self._has_previous = bool(data.get("hasPrevious", page > 1))
                return True
        return False

    def _get_count_buckets(self):
        return self._bucket_service.get_count_bucekts()
