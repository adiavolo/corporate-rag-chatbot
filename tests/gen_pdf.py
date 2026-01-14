from pypdf import PdfWriter
from io import BytesIO

def create_dummy_pdf(filename="test_doc.pdf"):
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    # Add some metadata or text if possible, but blank might be enough for simple checks. 
    # Actually, pypdf blank page is just blank. 
    # To add text, we need a library like reportlab, but it might not be installed.
    # Let's try to just use a blank pdf and rely on metadata or just the fact it parses.
    
    with open(filename, "wb") as f:
        writer.write(f)
    print(f"Created {filename}")

if __name__ == "__main__":
    create_dummy_pdf("tests/test_doc.pdf")
