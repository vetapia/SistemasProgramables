# ============================================
# Proyecto:  SmartClass
# Archivo:   asistencia.py
# Objetivo:  Registra la asistencia diaria en Excel y exporta la lista de asistencia
# Equipo:   Aldo Emmanuel Carrillo Gomez (23240343), Juan Daniel Torres Uribe (23240326)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# =====================================================================
"""Registro de asistencia en Excel.

Cada alumno se cuenta una sola vez por dia (su primera llegada). El historial
se guarda en datos/asistencia.xlsx. Si el archivo esta abierto en Excel, Windows
no deja guardarlo: se avisa y se reintenta en el siguiente registro.
"""
import io
import os
import threading
from datetime import datetime

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter


def _formato_encabezado(ws, ancho_columnas):
    for celda in ws[1]:
        celda.font = Font(bold=True)
    for i, ancho in enumerate(ancho_columnas, start=1):
        ws.column_dimensions[get_column_letter(i)].width = ancho


class Asistencia:
    def __init__(self, ruta):
        self.ruta = ruta
        self._lock = threading.RLock()
        self._registros = []    # {"fecha","hora","nombre","id"}
        self._indice = {}       # (fecha, id) -> hora
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        self._cargar()

    def _cargar(self):
        if not os.path.exists(self.ruta):
            return
        try:
            wb = load_workbook(self.ruta)
            if "Historial" not in wb.sheetnames:
                return
            for fila in wb["Historial"].iter_rows(min_row=2, values_only=True):
                if fila and fila[0] and len(fila) >= 4:
                    fecha, hora, nombre, alumno_id = (str(x) for x in fila[:4])
                    self._registros.append(
                        {"fecha": fecha, "hora": hora, "nombre": nombre, "id": alumno_id})
                    self._indice[(fecha, alumno_id)] = hora
        except Exception as e:
            print("Aviso: no se pudo leer el Excel de asistencia:", e)

    def _volcar(self):
        wb = Workbook()
        ws = wb.active
        ws.title = "Historial"
        ws.append(["Fecha", "Hora de llegada", "Alumno", "ID"])
        for r in self._registros:
            ws.append([r["fecha"], r["hora"], r["nombre"], r["id"]])
        _formato_encabezado(ws, [14, 16, 32, 12])
        tmp = self.ruta + ".tmp"
        try:
            wb.save(tmp)
            os.replace(tmp, self.ruta)
            return True
        except OSError as e:
            print("Aviso: no se pudo guardar asistencia.xlsx (cierra el archivo si lo tienes abierto):", e)
            try:
                os.remove(tmp)
            except OSError:
                pass
            return False

    def registrar(self, alumno_id, nombre, ahora=None):
        """Devuelve (es_nueva, hora_de_llegada). Solo cuenta la primera llegada del dia."""
        ahora = ahora or datetime.now()
        fecha = ahora.strftime("%Y-%m-%d")
        hora = ahora.strftime("%H:%M:%S")
        with self._lock:
            previa = self._indice.get((fecha, alumno_id))
            if previa:
                return False, previa
            self._registros.append({"fecha": fecha, "hora": hora, "nombre": nombre, "id": alumno_id})
            self._indice[(fecha, alumno_id)] = hora
            self._volcar()
            return True, hora

    def borrar_dia(self, fecha=None):
        """Borra los registros de asistencia de un dia (por defecto hoy). Devuelve cuantos borro."""
        fecha = fecha or datetime.now().strftime("%Y-%m-%d")
        with self._lock:
            antes = len(self._registros)
            self._registros = [r for r in self._registros if r["fecha"] != fecha]
            self._indice = {k: v for k, v in self._indice.items() if k[0] != fecha}
            self._volcar()
            return antes - len(self._registros)

    def hoy(self, fecha=None):
        fecha = fecha or datetime.now().strftime("%Y-%m-%d")
        with self._lock:
            lista = [{"nombre": r["nombre"], "hora": r["hora"]}
                     for r in self._registros if r["fecha"] == fecha]
        return sorted(lista, key=lambda x: x["hora"])

    def exportar_lista(self, alumnos, fecha=None):
        """Excel descargable: todos los alumnos registrados, con su hora de llegada de hoy."""
        fecha = fecha or datetime.now().strftime("%Y-%m-%d")
        with self._lock:
            llegadas = {a["id"]: self._indice.get((fecha, a["id"])) for a in alumnos}
            historial = list(self._registros)

        wb = Workbook()
        ws = wb.active
        ws.title = "Lista de hoy"
        ws.append([f"Lista de asistencia - {fecha}"])
        ws["A1"].font = Font(bold=True, size=13)
        ws.append([])
        ws.append(["Alumno", "Estado", "Hora de llegada"])
        for celda in ws[3]:
            celda.font = Font(bold=True)
        for a in sorted(alumnos, key=lambda x: x["nombre"].lower()):
            hora = llegadas.get(a["id"])
            ws.append([a["nombre"], "Presente" if hora else "Ausente", hora or "-"])
        for i, ancho in enumerate([32, 12, 16], start=1):
            ws.column_dimensions[get_column_letter(i)].width = ancho

        hist = wb.create_sheet("Historial")
        hist.append(["Fecha", "Hora de llegada", "Alumno"])
        for r in historial:
            hist.append([r["fecha"], r["hora"], r["nombre"]])
        for celda in hist[1]:
            celda.font = Font(bold=True)
        for i, ancho in enumerate([14, 16, 32], start=1):
            hist.column_dimensions[get_column_letter(i)].width = ancho

        salida = io.BytesIO()
        wb.save(salida)
        salida.seek(0)
        return salida
