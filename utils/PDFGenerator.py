from fpdf import FPDF

class PDFGenerator:
    def __init__(self, title="Document"):
        self.title = title

    def parse_string_to_pdf(self, content: str, output_path: str):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_title(self.title)
        pdf.set_font("Arial", size=12)
        
        # Split content into lines and add each line to the PDF
        for line in content.split('\n'):
            pdf.cell(0, 10, txt=line, ln=1)
        
        pdf.output(output_path)

