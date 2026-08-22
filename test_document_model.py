from document_model import Page, Section, Document


page = Page(
    page_number=1,
    text="Example page text",
    source_type="native_text"
)

section = Section(
    section_number="3.2",
    title="Cement",
    pages=[1]
)

document = Document(
    filename="S-2_sr.pdf",
    document_type="text",
    extraction_method="native_text",
    pages=[page],
    sections=[section]
)


print("Document:", document.filename)
print("Type:", document.document_type)
print("Pages:", len(document.pages))
print("Sections:", len(document.sections))

print("\nFirst page:")
print(document.pages[0])

print("\nFirst section:")
print(document.sections[0])
