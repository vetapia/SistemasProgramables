from ST7735 import TFT
from sysfont import sysfont

class DisplayManager:
    COLOR_BLUE = TFT.BLUE
    COLOR_WHITE = TFT.WHITE

    def __init__(self, spi, dc: int, reset: int, cs: int) -> None:
        self._display = TFT(spi, dc, reset, cs)

    def init_display(self, rotation: int = 0):
        self._display.initr()
        self._display.rotation(rotation)

    def text(self, cords: tuple[int, int], text: str, color = TFT.BLUE, size: int = 2, bg_color = None):
        self._display.text(cords, text, color, sysfont, size, False, bg_color) 

    def clean(self, color = TFT.WHITE):
        self._display.fill(color)

    def fill_rect(self, cords: tuple[int, int], size: tuple[int, int], color = TFT.BLUE):
        self._display.fillrect(cords, size, color)

    def draw_rect(self, cords: tuple[int, int], size: tuple[int, int], color = TFT.BLUE):
        self._display.rect(cords, size, color)

    def hline(self, cords: tuple[int, int], length: int, color = TFT.BLUE):
        self._display.hline(cords, length, color)

    def draw_login_screen(self, title: str, label: str, value: str = "", is_pin: bool = False):
        self.clean(TFT.WHITE)
        self._display.fillrect((0, 0), (160, 22), TFT.BLUE)
        self._display.text((8, 7), title[:24], TFT.WHITE, sysfont, 1, False, TFT.BLUE)

        self._display.text((10, 28), label[:24], TFT.BLUE, sysfont, 1, False, TFT.WHITE)

        self._display.rect((10, 40), (140, 24), TFT.BLUE)
        self.update_login_input(value, is_pin)

        self._display.fillrect((0, 108), (160, 20), TFT.BLUE)
        self._display.text((6, 114), "C:Sig  D:Atras  *:Bor", TFT.WHITE, sysfont, 1, False, TFT.BLUE)

    def update_login_input(self, value: str, is_pin: bool = False):
        self._display.fillrect((11, 41), (138, 22), TFT.WHITE)
        display_val = ("*" * len(value)) if is_pin else value
        if display_val:
            self._display.text((16, 44), display_val[:11], TFT.BLUE, sysfont, 2, False, TFT.WHITE)

    def show_login_error(self, message: str):
        self._display.fillrect((10, 68), (140, 36), TFT.BLUE)
        lines = message.split("\n") if "\n" in message else [message]
        y_pos = 72 if len(lines) > 1 else 80
        for line in lines[:3]:
            self._display.text((14, y_pos), line[:22], TFT.WHITE, sysfont, 1, False, TFT.BLUE)
            y_pos += 11

    def clear_login_error(self):
        self._display.fillrect((10, 68), (140, 36), TFT.WHITE)

    def show_login_status(self, message: str):
        self._display.fillrect((10, 68), (140, 36), TFT.WHITE)
        self._display.text((14, 80), message[:22], TFT.BLUE, sysfont, 1, False, TFT.WHITE)

    def draw_user_header(self, name: str, control_number: str):
        self._display.fillrect((0, 0), (160, 28), TFT.BLUE)
        display_name = f"Usr: {name}" if name else "Usuario"
        display_ctrl = f"No: {control_number}" if control_number else "No: --"
        self._display.text((4, 4), display_name[:25], TFT.WHITE, sysfont, 1, False, TFT.BLUE)
        self._display.text((4, 16), display_ctrl[:25], TFT.WHITE, sysfont, 1, False, TFT.BLUE)
        self._display.hline((0, 28), 160, TFT.WHITE)

    def draw_authenticated_base(self, name: str, control_number: str):
        self.clean(TFT.WHITE)
        self.draw_user_header(name, control_number)

    def draw_bucket_screen(self, max_buckets: int, selected_bucket: int = 0):
        self._display.text((10, 36), f"Almacen (1-{max_buckets}):", TFT.BLUE, sysfont, 1, False, TFT.WHITE)
        self._display.rect((10, 52), (140, 26), TFT.BLUE)
        self.update_bucket_selected(selected_bucket)
        self._display.fillrect((0, 108), (160, 20), TFT.BLUE)
        self._display.text((6, 114), "C:Confirmar  *:Bor", TFT.WHITE, sysfont, 1, False, TFT.BLUE)

    def update_bucket_selected(self, selected_bucket: int):
        self._display.fillrect((12, 54), (136, 22), TFT.WHITE)
        val = str(selected_bucket) if selected_bucket > 0 else "-"
        self._display.text((16, 56), val, TFT.BLUE, sysfont, 2, False, TFT.WHITE)

    def draw_materials_screen(self, bucket_id: int, items: list, selected_index: int = 0):
        self._display.fillrect((0, 29), (160, 79), TFT.WHITE)
        self._display.text((6, 31), f"Almacen {bucket_id} - Materiales:", TFT.BLUE, sysfont, 1, False, TFT.WHITE)
        self.update_materials_list(items, selected_index)
        self._display.fillrect((0, 108), (160, 20), TFT.BLUE)
        self._display.text((4, 114), "A:Abj B:Arr C:Ok D:Atr", TFT.WHITE, sysfont, 1, False, TFT.BLUE)

    def update_materials_list(self, items: list, selected_index: int = 0):
        self._display.fillrect((0, 42), (160, 64), TFT.WHITE)
        if not items:
            self._display.text((10, 66), "Sin materiales", TFT.BLUE, sysfont, 1, False, TFT.WHITE)
            return

        y_pos = 43
        for idx, item in enumerate(items[:4]):
            name = item.get("name", "Material") if isinstance(item, dict) else str(item)
            if idx == selected_index:
                self._display.fillrect((4, y_pos - 1), (152, 13), TFT.BLUE)
                self._display.text((8, y_pos + 1), f"> {name[:21]}", TFT.WHITE, sysfont, 1, False, TFT.BLUE)
            else:
                self._display.fillrect((4, y_pos - 1), (152, 13), TFT.WHITE)
                self._display.text((8, y_pos + 1), f"  {name[:21]}", TFT.BLUE, sysfont, 1, False, TFT.WHITE)
            y_pos += 15

    def draw_confirm_loan_screen(self, material_name: str, material_id: int):
        self._display.fillrect((0, 29), (160, 79), TFT.WHITE)
        self._display.text((6, 31), "Confirmar prestamo:", TFT.BLUE, sysfont, 1, False, TFT.WHITE)
        self._display.rect((8, 44), (144, 40), TFT.BLUE)
        self._display.fillrect((9, 45), (142, 38), TFT.WHITE)
        self._display.text((12, 49), "Material:", TFT.BLUE, sysfont, 1, False, TFT.WHITE)
        self._display.text((12, 60), material_name[:20], TFT.BLUE, sysfont, 1, False, TFT.WHITE)
        self._display.text((12, 71), f"ID: {material_id}", TFT.BLUE, sysfont, 1, False, TFT.WHITE)
        self._display.fillrect((0, 108), (160, 20), TFT.BLUE)
        self._display.text((6, 114), "C:Aceptar  D:Cancelar", TFT.WHITE, sysfont, 1, False, TFT.BLUE)

    def show_loan_status(self, message: str):
        self._display.fillrect((8, 88), (144, 18), TFT.WHITE)
        self._display.text((12, 92), message[:22], TFT.BLUE, sysfont, 1, False, TFT.WHITE)

    def show_loan_error(self, message: str):
        self._display.fillrect((8, 44), (144, 58), TFT.BLUE)
        lines = message.split("\n") if "\n" in message else [message]
        y_pos = 50
        for line in lines[:4]:
            self._display.text((12, y_pos), line[:22], TFT.WHITE, sysfont, 1, False, TFT.BLUE)
            y_pos += 12
        self._display.fillrect((0, 108), (160, 20), TFT.BLUE)
        self._display.text((6, 114), "D:Volver  C:Volver", TFT.WHITE, sysfont, 1, False, TFT.BLUE)

    def show_loan_success(self, material_name: str):
        self._display.fillrect((8, 44), (144, 58), TFT.BLUE)
        self._display.text((12, 50), "Prestamo exitoso!", TFT.WHITE, sysfont, 1, False, TFT.BLUE)
        self._display.text((12, 64), material_name[:20], TFT.WHITE, sysfont, 1, False, TFT.BLUE)
        self._display.text((12, 78), "Registrado con exito", TFT.WHITE, sysfont, 1, False, TFT.BLUE)
        self._display.fillrect((0, 108), (160, 20), TFT.BLUE)
        self._display.text((6, 114), "C:Finalizar", TFT.WHITE, sysfont, 1, False, TFT.BLUE)

    def test(self, user):
        self._display.fill(TFT.WHITE)          
        self._display.text((10, 50), user["name"], TFT.BLUE, sysfont, 2, False, TFT.WHITE) 
        self._display.text((10, 70), user["lastName"], TFT.BLUE, sysfont, 2, False, TFT.WHITE)
