import fitz
import os

def create_pdf(path, pages_text):
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((50, 50), text)
    doc.save(path)
    doc.close()

os.makedirs("data/test_pdfs", exist_ok=True)

# 1. Finance PDF
# Page 1 has general info, Page 2 has specific risks
create_pdf("data/test_pdfs/finance.pdf", [
    "Page 1: Inflation is defined as the rate of increase in prices. The repo rate was held at 6.5%.",
    "Page 2: The primary inflation risks include food price volatility and rising global oil prices. Growth remains stable."
])

# 2. Biology PDF
create_pdf("data/test_pdfs/biology.pdf", [
    "The growth rate of bacteria is influenced by the concentration of nutrients in the agar.",
    "Bacterial growth follows a logarithmic scale under ideal conditions."
])

# 3. Cooking PDF
create_pdf("data/test_pdfs/cooking.pdf", [
    "Boil the water at a steady rate. High heat risks burning the delicate sauce.",
    "The risk of clumping is reduced by stirring the pasta continuously."
])

print("Enhanced Test PDFs created.")
