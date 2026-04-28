import fitz
import os

upload_dir = "data/uploads"
os.makedirs(upload_dir, exist_ok=True)
pdf_path = os.path.join(upload_dir, "test_text.pdf")

doc = fitz.open()
for i in range(3):
    page = doc.new_page()
    page.insert_text((50, 50), f"This is page {i+1} of a sample text-based PDF.")
    page.insert_text((50, 80), "It contains multiple lines of text.")
    page.insert_text((50, 110), "This should be extractable as blocks by PyMuPDF.")

doc.save(pdf_path)
doc.close()
print(f"Created {pdf_path}")
