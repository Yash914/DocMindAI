from dataclasses import dataclass, field
from typing import List


@dataclass
class Page:
    page_number: int
    text: str
    source_type: str


@dataclass
class Section:
    section_number: str
    title: str
    pages: List[int] = field(default_factory=list)


@dataclass
class Document:
    filename: str
    document_type: str
    extraction_method: str
    pages: List[Page] = field(default_factory=list)
    sections: List[Section] = field(default_factory=list)