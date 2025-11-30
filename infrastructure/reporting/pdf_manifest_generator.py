from fpdf import FPDF
from domain.interfaces.manifest_generator import ManifestGenerator
from models.operations.load import Load
import io

class PdfManifestGenerator(ManifestGenerator):
    def generate(self, load: Load, load_data: dict) -> bytes:
        pdf = FPDF()
        pdf.add_page()
        
        # --- Header ---
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "MANIFIESTO DE CARGA - BIOSÓLIDOS", align="C", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 10, f"ID Carga: {load.id} | Fecha Emisión: {load.created_at}", align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        # --- Section 1: Origin ---
        self._section_title(pdf, "1. ORIGEN (GENERADOR)")
        self._key_value(pdf, "Planta:", load_data.get('origin_name', 'N/A'))
        self._key_value(pdf, "Dirección:", "Calle Industrial 123, Región Metropolitana") # Mock address
        self._key_value(pdf, "Fecha/Hora Salida:", str(load.dispatch_time or "N/A"))
        pdf.ln(5)
        
        # --- Section 2: Transport ---
        self._section_title(pdf, "2. TRANSPORTE")
        self._key_value(pdf, "Transportista:", load_data.get('driver_name', 'N/A')) # Assuming driver name implies contractor for now
        self._key_value(pdf, "Chofer:", load_data.get('driver_name', 'N/A'))
        self._key_value(pdf, "Patente Camión:", load_data.get('vehicle_plate', 'N/A'))
        pdf.ln(5)
        
        # --- Section 3: Load Data ---
        self._section_title(pdf, "3. DATOS DE LA CARGA")
        self._key_value(pdf, "Tipo de Lodo:", "Biosólido Deshidratado")
        self._key_value(pdf, "Clasificación:", "Clase B")
        self._key_value(pdf, "Lote (Batch ID):", str(load.batch_id or "N/A"))
        pdf.ln(5)
        
        # --- Section 3.5: Agronomic Data (Sprint 3) ---
        self._section_title(pdf, "3.5. INFORMACIÓN AGRONÓMICA (CUMPLIMIENTO)")
        self._key_value(pdf, "PAN (N Disponible):", f"{load_data.get('pan_value', 'N/A')} kg/ton")
        self._key_value(pdf, "Tasa Aplicación:", f"{load_data.get('agronomic_rate', 'N/A')} kg N/ha")
        self._key_value(pdf, "Total N Aplicado:", f"{load_data.get('applied_nitrogen_kg', 'N/A')} kg")
        pdf.ln(5)
        
        # --- Section 4: Weighing ---
        self._section_title(pdf, "4. PESAJE (Kg)")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(60, 8, f"Peso Bruto: {load_data.get('weight_gross', 'Pendiente')}", border=1)
        pdf.cell(60, 8, f"Tara: {load_data.get('weight_tare', 'Pendiente')}", border=1)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(60, 8, f"Peso Neto: {load.weight_net or 0}", border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        # --- Section 5: Destination ---
        self._section_title(pdf, "5. DESTINO (DISPOSICIÓN FINAL)")
        self._key_value(pdf, "Predio:", load_data.get('dest_name', 'N/A'))
        self._key_value(pdf, "Coordenadas GPS:", load.disposal_coordinates or "N/A")
        self._key_value(pdf, "Fecha/Hora Recepción:", str(load.arrival_time or "N/A"))
        self._key_value(pdf, "Fecha/Hora Disposición:", str(load.disposal_time or "N/A"))
        pdf.ln(10)
        
        # --- Footer: Signatures ---
        pdf.set_y(-60)
        pdf.set_font("Helvetica", "I", 8)
        pdf.multi_cell(0, 5, "Certifico que la información entregada en este documento es verídica y que la carga ha sido manejada de acuerdo a la normativa vigente (DS4).")
        pdf.ln(10)
        
        y_sig = pdf.get_y()
        pdf.line(20, y_sig, 70, y_sig)
        pdf.line(80, y_sig, 130, y_sig)
        pdf.line(140, y_sig, 190, y_sig)
        
        pdf.set_xy(20, y_sig + 2)
        pdf.cell(50, 5, "Firma Generador", align="C")
        pdf.set_xy(80, y_sig + 2)
        pdf.cell(50, 5, "Firma Transportista", align="C")
        pdf.set_xy(140, y_sig + 2)
        pdf.cell(50, 5, "Firma Destinatario", align="C")
        
        return bytes(pdf.output())

    def _section_title(self, pdf, title):
        pdf.set_fill_color(200, 200, 200)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, title, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    
    def _key_value(self, pdf, key, value):
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(50, 6, key, border=0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, str(value), border=0, new_x="LMARGIN", new_y="NEXT")
