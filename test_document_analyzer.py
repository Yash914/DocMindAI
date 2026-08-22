from config import INPUT_DIR
from document_analyzer import analyze_pdf


pdf_files = [
    "S-1_sr.pdf",
    "S-2_sr.pdf",
    "S-3_sr.pdf"
]


for filename in pdf_files:

    print("\n" + "=" * 60)
    print(f"Analyzing: {filename}")
    print("=" * 60)

    pdf_path = INPUT_DIR / filename

    result = analyze_pdf(pdf_path)

    for key, value in result.items():
        print(f"{key}: {value}")