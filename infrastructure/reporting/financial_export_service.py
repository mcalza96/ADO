"""
Financial Export Service.

Handles the generation of physical files (Excel, PDF) for financial settlements.
Dependencies: pandas, openpyxl, reportlab.
"""

import io
from typing import Dict, Any
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from domain.finance.entities.financial_reporting_dtos import SettlementResult

class FinancialExportService:
    """
    Service for generating formatted export files.
    """
    
    def generate_settlement_excel(self, settlement_data: SettlementResult) -> bytes:
        """
        Generates an Excel file with multiple sheets:
        - Resumen: Totals
        - Detalle Transportistas: Detailed costs
        - Detalle Clientes: Detailed revenues
        
        Args:
            settlement_data: The full settlement result object
            
        Returns:
            bytes: The Excel file content
        """
        output = io.BytesIO()
        
        # Prepare DataFrames
        contractor_df = settlement_data.contractor_df.copy()
        client_df = settlement_data.client_df.copy()
        
        # Create Summary DataFrame
        cycle = settlement_data.cycle_info
        summary_data = {
            'Concepto': ['Periodo', 'Valor UF', 'Inicio Ciclo', 'Fin Ciclo', 'Total Costos (UF)', 'Total Ingresos (UF)'],
            'Valor': [
                cycle['period_key'],
                cycle['uf_value'],
                cycle['start_date'],
                cycle['end_date'],
                settlement_data.total_costs_uf,
                settlement_data.total_revenue_uf
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        # Write to Excel
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='Resumen', index=False)
            contractor_df.to_excel(writer, sheet_name='Detalle Transportistas', index=False)
            client_df.to_excel(writer, sheet_name='Detalle Clientes', index=False)
            
            # Auto-adjust columns (basic)
            for sheet_name in writer.sheets:
                sheet = writer.sheets[sheet_name]
                for column in sheet.columns:
                    length = max(len(str(cell.value)) for cell in column)
                    adjusted_width = (length + 2)
                    sheet.column_dimensions[column[0].column_letter].width = adjusted_width
                    
        return output.getvalue()

    def generate_payment_cover_pdf(self, summary_data: Dict[str, Any]) -> bytes:
        """
        Generates a PDF cover sheet for payment processing.
        
        Args:
            summary_data: Dict containing summary info (Period, Totals, User)
            
        Returns:
            bytes: The PDF file content
        """
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = styles['Title']
        elements.append(Paragraph("Carátula de Estado de Pago", title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Period Info
        period_text = f"Periodo: {summary_data.get('period_key', 'N/A')}"
        elements.append(Paragraph(period_text, styles['Heading2']))
        
        date_text = f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        elements.append(Paragraph(date_text, styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Totals Table
        data = [
            ['Concepto', 'Monto (UF)', 'Monto Estimado (CLP)'],
            ['Total Costos Transporte', f"{summary_data.get('total_costs_uf', 0):,.2f}", f"{summary_data.get('total_costs_clp', 0):,.0f}"],
            ['Total Ingresos Clientes', f"{summary_data.get('total_revenue_uf', 0):,.2f}", f"{summary_data.get('total_revenue_clp', 0):,.0f}"],
            ['Margen Operacional', f"{summary_data.get('margin_uf', 0):,.2f}", f"{summary_data.get('margin_clp', 0):,.0f}"]
        ]
        
        table = Table(data, colWidths=[200, 100, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 1 * inch))
        
        # Signatures
        elements.append(Paragraph("__________________________", styles['Normal']))
        elements.append(Paragraph("Elaborado por", styles['Normal']))
        elements.append(Spacer(1, 0.5 * inch))
        
        elements.append(Paragraph("__________________________", styles['Normal']))
        elements.append(Paragraph("Aprobado por", styles['Normal']))
        
        doc.build(elements)
        return output.getvalue()
