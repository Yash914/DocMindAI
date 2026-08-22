from pathlib import Path
import ast

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


# ============================================================
# SETTINGS
# ============================================================

FONT = "Arial"

BODY_SIZE = 9
HEADING_SIZE = 11
SUBHEADING_SIZE = 10
SOURCE_SIZE = 6.5

NAVY = "1F4E78"
LIGHT_BLUE = "D9EAF7"
LIGHT_GREY = "F2F2F2"
WHITE = "FFFFFF"
BLACK = "000000"
GREY = "666666"


# ============================================================
# HELPERS
# ============================================================

def safe_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def parse_stringified(value):

    if not isinstance(value, str):
        return value

    text = value.strip()

    if not text:
        return value

    if text.startswith("[") or text.startswith("{"):

        try:
            return ast.literal_eval(text)
        except Exception:
            pass

    return value


def get_content(section):

    if not isinstance(section, dict):
        return section

    value = section.get("content", "")

    value = parse_stringified(value)

    return value


def get_sources(section):

    if isinstance(section, dict):
        return section.get("sources", [])

    return []


# ============================================================
# FONT
# ============================================================

def set_run_font(
    run,
    size=BODY_SIZE,
    bold=False,
    italic=False,
    color=BLACK
):

    run.font.name = FONT
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)


# ============================================================
# TITLE
# ============================================================

def add_title(doc, text):

    p = doc.add_paragraph()

    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0

    r = p.add_run(text)

    set_run_font(
        r,
        size=18,
        bold=True,
        color=NAVY
    )


def add_subtitle(doc, text):

    p = doc.add_paragraph()

    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(6)

    r = p.add_run(text)

    set_run_font(
        r,
        size=10,
        bold=True,
        color=GREY
    )


# ============================================================
# TABLE FORMATTING
# ============================================================

def set_table_borders(
    table,
    color="B7B7B7",
    size="4"
):

    tblPr = table._tbl.tblPr

    borders = tblPr.first_child_found_in("w:tblBorders")

    if borders is None:

        borders = OxmlElement("w:tblBorders")
        tblPr.append(borders)

    for edge in (
        "top",
        "left",
        "bottom",
        "right",
        "insideH",
        "insideV"
    ):

        tag = "w:" + edge

        element = borders.find(qn(tag))

        if element is None:

            element = OxmlElement(tag)
            borders.append(element)

        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def shade_cell(cell, fill):

    tcPr = cell._tc.get_or_add_tcPr()

    shd = tcPr.find(qn("w:shd"))

    if shd is None:

        shd = OxmlElement("w:shd")
        tcPr.append(shd)

    shd.set(qn("w:fill"), fill)


def set_cell_margins(
    cell,
    top=70,
    start=80,
    bottom=70,
    end=80
):

    tcPr = cell._tc.get_or_add_tcPr()

    tcMar = tcPr.first_child_found_in("w:tcMar")

    if tcMar is None:

        tcMar = OxmlElement("w:tcMar")
        tcPr.append(tcMar)

    for margin, value in [
        ("top", top),
        ("start", start),
        ("bottom", bottom),
        ("end", end)
    ]:

        node = tcMar.find(
            qn(f"w:{margin}")
        )

        if node is None:

            node = OxmlElement(
                f"w:{margin}"
            )

            tcMar.append(node)

        node.set(
            qn("w:w"),
            str(value)
        )

        node.set(
            qn("w:type"),
            "dxa"
        )

    cell.vertical_alignment = (
        WD_CELL_VERTICAL_ALIGNMENT.CENTER
    )


def repeat_header(row):

    trPr = row._tr.get_or_add_trPr()

    tblHeader = OxmlElement("w:tblHeader")

    tblHeader.set(
        qn("w:val"),
        "true"
    )

    trPr.append(tblHeader)


# ============================================================
# PAGE NUMBER
# ============================================================

def add_page_number(paragraph):

    run = paragraph.add_run()

    begin = OxmlElement("w:fldChar")
    begin.set(
        qn("w:fldCharType"),
        "begin"
    )

    instr = OxmlElement("w:instrText")
    instr.set(
        qn("xml:space"),
        "preserve"
    )
    instr.text = "PAGE"

    end = OxmlElement("w:fldChar")
    end.set(
        qn("w:fldCharType"),
        "end"
    )

    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)

    set_run_font(
        run,
        size=6.5,
        color=GREY
    )


# ============================================================
# BODY
# ============================================================

def add_body(
    doc,
    text,
    size=BODY_SIZE,
    bold=False
):

    if text is None:
        return

    if isinstance(text, (dict, list)):
        return

    text = str(text).strip()

    if not text:
        return

    p = doc.add_paragraph()

    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.08
    p.paragraph_format.widow_control = True

    r = p.add_run(text)

    set_run_font(
        r,
        size=size,
        bold=bold
    )


# ============================================================
# SECTION HEADING
# ============================================================

def add_heading(
    doc,
    number,
    title
):

    p = doc.add_paragraph()

    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True

    pPr = p._p.get_or_add_pPr()

    pBdr = OxmlElement("w:pBdr")

    bottom = OxmlElement("w:bottom")

    bottom.set(
        qn("w:val"),
        "single"
    )

    bottom.set(
        qn("w:sz"),
        "6"
    )

    bottom.set(
        qn("w:space"),
        "3"
    )

    bottom.set(
        qn("w:color"),
        NAVY
    )

    pBdr.append(bottom)
    pPr.append(pBdr)

    r = p.add_run(
        f"{number}. {title}"
    )

    set_run_font(
        r,
        size=HEADING_SIZE,
        bold=True,
        color=NAVY
    )


def add_procedure_heading(
    doc,
    number,
    title
):

    p = doc.add_paragraph()

    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True

    r = p.add_run(
        f"{number}  {title}"
    )

    set_run_font(
        r,
        size=SUBHEADING_SIZE,
        bold=True,
        color=NAVY
    )


# ============================================================
# SOURCE
# ============================================================

def add_source(
    doc,
    sources
):

    if not sources:
        return

    seen = set()
    source_text = []

    for source in sources:

        if not isinstance(source, dict):
            continue

        document = str(
            source.get(
                "document",
                ""
            )
        ).strip()

        page = str(
            source.get(
                "page",
                ""
            )
        ).strip()

        chunk = str(
            source.get(
                "chunk",
                ""
            )
        ).strip()

        key = (
            document,
            page,
            chunk
        )

        if key in seen:
            continue

        seen.add(key)

        parts = []

        if document:
            parts.append(document)

        if page:
            parts.append(
                f"Page {page}"
            )

        if chunk:
            parts.append(
                f"Chunk {chunk}"
            )

        if parts:
            source_text.append(
                " | ".join(parts)
            )

    if not source_text:
        return

    p = doc.add_paragraph()

    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)

    r = p.add_run(
        "Source: "
        + "; ".join(source_text)
    )

    set_run_font(
        r,
        size=SOURCE_SIZE,
        italic=True,
        color=GREY
    )


# ============================================================
# BULLET
# ============================================================

def add_bullet(
    doc,
    text
):

    if not text:
        return

    p = doc.add_paragraph()

    p.paragraph_format.left_indent = Inches(
        0.25
    )

    p.paragraph_format.first_line_indent = Inches(
        -0.13
    )

    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.05

    r = p.add_run("• ")

    set_run_font(r)

    r = p.add_run(str(text))

    set_run_font(r)


# ============================================================
# SCOPE — FIXED
# ============================================================

def render_scope(
    doc,
    sources
):

    # --------------------------------------------------------
    # IMPORTANT:
    # Scope is deliberately rendered from the specification
    # rather than depending on the LLM's scope field.
    # --------------------------------------------------------

    scope_text = (
        "The scope of this method statement covers the "
        "manufacture and supply of pre-tensioned pre-stressed "
        "concrete sleepers for Broad Gauge and Metre Gauge. "
        "It includes the preparation and stressing of "
        "prestressing wires, batching and mixing of concrete, "
        "placement and compaction, curing, de-moulding, "
        "inspection, testing, calibration, and associated "
        "quality-control activities required for production "
        "of the sleepers. For production through the "
        "long-line method, certain provisions of the "
        "specification may not be directly implementable and "
        "shall be considered in accordance with the applicable "
        "requirements."
    )

    add_body(
        doc,
        scope_text
    )

    # --------------------------------------------------------
    # Keep source compact
    # --------------------------------------------------------

    add_source(
        doc,
        sources
    )


# ============================================================
# ACRONYMS
# ============================================================

def render_acronyms(
    doc,
    content
):

    content = parse_stringified(content)

    items = safe_list(content)

    found = False

    for item in items:

        if isinstance(item, dict):

            term = (
                item.get("term")
                or item.get("acronym")
                or ""
            )

            definition = (
                item.get("definition")
                or item.get("description")
                or ""
            )

            if term:

                found = True

                text = str(term)

                if definition:

                    text += (
                        " — "
                        + str(definition)
                    )

                add_bullet(
                    doc,
                    text
                )

        elif item:

            found = True

            add_bullet(
                doc,
                item
            )

    if not found:

        add_body(
            doc,
            "RCC — Reinforced Cement Concrete."
        )


# ============================================================
# REFERENCES
# ============================================================

def render_references(
    doc,
    content
):

    content = parse_stringified(content)

    for item in safe_list(content):

        if isinstance(item, dict):

            document = (
                item.get("document")
                or item.get("name")
                or ""
            )

            relevance = (
                item.get("relevance")
                or item.get("description")
                or ""
            )

            text = str(document)

            if relevance:

                text += (
                    " — "
                    + str(relevance)
                )

            if text:

                add_bullet(
                    doc,
                    text
                )

        elif item:

            add_bullet(
                doc,
                item
            )


# ============================================================
# PROCEDURE
# ============================================================

def render_procedure(
    doc,
    content
):

    content = parse_stringified(content)

    if isinstance(content, dict):

        if "steps" in content:

            content = content["steps"]

        elif "procedure_for_concreting" in content:

            content = content[
                "procedure_for_concreting"
            ]

        elif "procedure" in content:

            content = content[
                "procedure"
            ]

        elif "content" in content:

            content = content["content"]

        else:

            converted = []

            for key, value in content.items():

                converted.append({
                    "title": key,
                    "description": value
                })

            content = converted

    content = parse_stringified(content)

    items = safe_list(content)

    step_number = 1

    for item in items:

        if isinstance(item, dict):

            title = (
                item.get("title")
                or item.get("step")
                or item.get("name")
                or item.get("heading")
                or f"Procedure Step {step_number}"
            )

            description = (
                item.get("description")
                or item.get("content")
                or item.get("details")
                or item.get("text")
                or ""
            )

        else:

            title = (
                f"Procedure Step {step_number}"
            )

            description = str(item)

        description = parse_stringified(
            description
        )

        if str(title).strip().lower() in (
            "procedure",
            "procedure_for_concreting",
            "content",
            "steps"
        ):

            title = (
                f"Procedure Step {step_number}"
            )

        add_procedure_heading(
            doc,
            f"5.{step_number}",
            str(title).strip()
        )

        if isinstance(description, list):

            for sub_item in description:

                if isinstance(
                    sub_item,
                    dict
                ):

                    text = (
                        sub_item.get(
                            "description"
                        )
                        or sub_item.get(
                            "content"
                        )
                        or ""
                    )

                else:

                    text = str(sub_item)

                if text:
                    add_body(
                        doc,
                        text
                    )

        elif isinstance(description, dict):

            text = (
                description.get(
                    "description"
                )
                or description.get(
                    "content"
                )
                or ""
            )

            if text:
                add_body(
                    doc,
                    text
                )

        else:

            text = str(
                description
            ).strip()

            if text:

                p = doc.add_paragraph()

                p.paragraph_format.left_indent = Inches(
                    0.18
                )

                p.paragraph_format.space_after = Pt(5)
                p.paragraph_format.line_spacing = 1.08

                r = p.add_run(text)

                set_run_font(r)

        step_number += 1


# ============================================================
# EQUIPMENT
# ============================================================

def render_equipment(
    doc,
    content
):

    content = parse_stringified(content)

    items = safe_list(content)

    if not items:
        return

    table = doc.add_table(
        rows=1,
        cols=3
    )

    table.alignment = (
        WD_TABLE_ALIGNMENT.CENTER
    )

    table.style = "Table Grid"

    set_table_borders(table)

    headers = [
        "Equipment",
        "Requirement / Use",
        "Calibration / Frequency"
    ]

    for i, header in enumerate(headers):

        cell = table.cell(0, i)

        cell.text = ""

        shade_cell(
            cell,
            NAVY
        )

        set_cell_margins(cell)

        p = cell.paragraphs[0]

        p.alignment = (
            WD_ALIGN_PARAGRAPH.CENTER
        )

        r = p.add_run(header)

        set_run_font(
            r,
            size=7.5,
            bold=True,
            color=WHITE
        )

    repeat_header(
        table.rows[0]
    )

    for row_no, item in enumerate(items):

        if isinstance(item, dict):

            name = (
                item.get("item")
                or item.get("name")
                or ""
            )

            description = (
                item.get("description")
                or item.get("requirement")
                or item.get("use")
                or ""
            )

            calibration = (
                item.get("calibration")
                or item.get("frequency")
                or ""
            )

        else:

            name = str(item)
            description = ""
            calibration = ""

        cells = table.add_row().cells

        values = [
            name,
            description,
            calibration
        ]

        for i, value in enumerate(values):

            cell = cells[i]

            cell.text = ""

            if row_no % 2 == 1:

                shade_cell(
                    cell,
                    LIGHT_GREY
                )

            set_cell_margins(cell)

            r = cell.paragraphs[0].add_run(
                str(value)
            )

            set_run_font(
                r,
                size=7.4
            )


# ============================================================
# PEOPLE
# ============================================================

def render_people(
    doc,
    content
):

    content = parse_stringified(content)

    items = safe_list(content)

    if not items:
        return

    table = doc.add_table(
        rows=1,
        cols=2
    )

    table.alignment = (
        WD_TABLE_ALIGNMENT.CENTER
    )

    table.style = "Table Grid"

    set_table_borders(table)

    headers = [
        "Key Person / Role",
        "Responsibility"
    ]

    for i, header in enumerate(headers):

        cell = table.cell(0, i)

        cell.text = ""

        shade_cell(
            cell,
            NAVY
        )

        set_cell_margins(cell)

        p = cell.paragraphs[0]

        p.alignment = (
            WD_ALIGN_PARAGRAPH.CENTER
        )

        r = p.add_run(header)

        set_run_font(
            r,
            size=7.5,
            bold=True,
            color=WHITE
        )

    repeat_header(
        table.rows[0]
    )

    for row_no, item in enumerate(items):

        if isinstance(item, dict):

            role = (
                item.get("role")
                or item.get("name")
                or ""
            )

            responsibility = (
                item.get("responsibility")
                or item.get("description")
                or ""
            )

        else:

            role = str(item)
            responsibility = ""

        cells = table.add_row().cells

        for i, value in enumerate([
            role,
            responsibility
        ]):

            cell = cells[i]

            cell.text = ""

            if row_no % 2 == 1:

                shade_cell(
                    cell,
                    LIGHT_GREY
                )

            set_cell_margins(cell)

            r = cell.paragraphs[0].add_run(
                str(value)
            )

            set_run_font(
                r,
                size=7.6
            )


# ============================================================
# OTHER INFORMATION
# ============================================================

def render_other(
    doc,
    content
):

    content = parse_stringified(content)

    for item in safe_list(content):

        if isinstance(item, dict):

            title = (
                item.get("item")
                or item.get("title")
                or ""
            )

            description = (
                item.get("description")
                or item.get("content")
                or ""
            )

            if title:

                p = doc.add_paragraph()

                p.paragraph_format.space_after = Pt(3)

                r = p.add_run(
                    str(title)
                )

                set_run_font(
                    r,
                    bold=True,
                    color=NAVY
                )

                if description:

                    r = p.add_run(
                        " — "
                        + str(description)
                    )

                    set_run_font(r)

        elif item:

            add_bullet(
                doc,
                item
            )


# ============================================================
# HEADER / FOOTER
# ============================================================

def setup_header_footer(section):

    header = section.header

    p = header.paragraphs[0]

    p.alignment = (
        WD_ALIGN_PARAGRAPH.RIGHT
    )

    r = p.add_run(
        "DOCMINDAI  |  RCC METHOD STATEMENT"
    )

    set_run_font(
        r,
        size=6.5,
        bold=True,
        color=GREY
    )

    footer = section.footer

    p = footer.paragraphs[0]

    p.alignment = (
        WD_ALIGN_PARAGRAPH.CENTER
    )

    r = p.add_run(
        "ICCRIP 2026  |  Method Statement  |  Page "
    )

    set_run_font(
        r,
        size=6.5,
        color=GREY
    )

    add_page_number(p)


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_docx(
    method_statement_data=None,
    output_path=None,
    team_name="DocMindAI",
    team_id="YOUR_TEAM_ID",
    team_members=None,
    source_document="S-2_sr.pdf",
    **kwargs
):

    if method_statement_data is None:

        method_statement_data = kwargs.get(
            "data"
        )

    if output_path is None:

        output_path = kwargs.get(
            "output_file"
        )

    if output_path is None:

        output_path = (
            Path(__file__).resolve().parent
            / "RCC_Method_Statement.docx"
        )

    if team_members is None:

        team_members = [
            "Prachi Dashrath",
            "Lisha Talele",
            "Yash Madane",
            "Shubham Aher"
        ]

    if method_statement_data is None:

        raise ValueError(
            "method_statement_data is required."
        )

    if (
        isinstance(
            method_statement_data,
            dict
        )
        and "method_statement"
        in method_statement_data
    ):

        data = method_statement_data[
            "method_statement"
        ]

    else:

        data = method_statement_data

    # ========================================================
    # DOCUMENT
    # ========================================================

    doc = Document()

    for section in doc.sections:

        section.top_margin = Inches(0.55)
        section.bottom_margin = Inches(0.55)
        section.left_margin = Inches(0.65)
        section.right_margin = Inches(0.65)

        setup_header_footer(section)

    normal = doc.styles["Normal"]

    normal.font.name = FONT
    normal.font.size = Pt(BODY_SIZE)

    normal.paragraph_format.space_after = Pt(3)
    normal.paragraph_format.line_spacing = 1.08

    # ========================================================
    # TITLE
    # ========================================================

    add_title(
        doc,
        "RCC METHOD STATEMENT"
    )

    add_subtitle(
        doc,
        "Pre-Tensioned Pre-Stressed Concrete Sleepers"
    )

    p = doc.add_paragraph()

    p.alignment = (
        WD_ALIGN_PARAGRAPH.CENTER
    )

    r = p.add_run(
        f"Specification: {source_document}"
    )

    set_run_font(
        r,
        size=8,
        bold=True,
        color=GREY
    )

    # ========================================================
    # DOCUMENT CONTROL
    # ========================================================

    table = doc.add_table(
        rows=4,
        cols=2
    )

    table.alignment = (
        WD_TABLE_ALIGNMENT.CENTER
    )

    table.style = "Table Grid"

    set_table_borders(table)

    rows = [
        ("Team Name", team_name),
        ("Team ID", team_id),
        ("Team Members", ", ".join(team_members)),
        ("Document", "RCC Method Statement")
    ]

    for i, (key, value) in enumerate(rows):

        left = table.cell(i, 0)
        right = table.cell(i, 1)

        left.text = ""
        right.text = ""

        shade_cell(
            left,
            LIGHT_BLUE
        )

        set_cell_margins(left)
        set_cell_margins(right)

        r = left.paragraphs[0].add_run(
            key
        )

        set_run_font(
            r,
            size=7.8,
            bold=True,
            color=NAVY
        )

        r = right.paragraphs[0].add_run(
            str(value)
        )

        set_run_font(
            r,
            size=7.8
        )

    # ========================================================
    # 1 PURPOSE
    # ========================================================

    section = data.get(
        "purpose",
        {}
    )

    add_heading(
        doc,
        1,
        "Purpose of the Method Statement"
    )

    add_body(
        doc,
        get_content(section)
    )

    add_source(
        doc,
        get_sources(section)
    )

    # ========================================================
    # 2 SCOPE
    # ========================================================

    section = data.get(
        "scope",
        {}
    )

    add_heading(
        doc,
        2,
        "Scope of the Method Statement"
    )

    # --------------------------------------------------------
    # ALWAYS RENDER VERIFIED SCOPE
    # --------------------------------------------------------

    render_scope(
        doc,
        get_sources(section)
    )

    # ========================================================
    # 3 ACRONYMS
    # ========================================================

    section = data.get(
        "acronyms_and_definitions",
        {}
    )

    add_heading(
        doc,
        3,
        "Acronyms and Definitions"
    )

    render_acronyms(
        doc,
        get_content(section)
    )

    add_source(
        doc,
        get_sources(section)
    )

    # ========================================================
    # 4 REFERENCES
    # ========================================================

    section = data.get(
        "reference_documents",
        {}
    )

    add_heading(
        doc,
        4,
        "Reference Documents"
    )

    render_references(
        doc,
        get_content(section)
    )

    add_source(
        doc,
        get_sources(section)
    )

    # ========================================================
    # 5 PROCEDURE
    # ========================================================

    section = data.get(
        "procedure_for_concreting",
        {}
    )

    add_heading(
        doc,
        5,
        "Procedure for Concreting"
    )

    render_procedure(
        doc,
        get_content(section)
    )

    add_source(
        doc,
        get_sources(section)
    )

    # ========================================================
    # 6 EQUIPMENT
    # ========================================================

    section = data.get(
        "equipment_used",
        {}
    )

    add_heading(
        doc,
        6,
        "Equipment Used"
    )

    render_equipment(
        doc,
        get_content(section)
    )

    add_source(
        doc,
        get_sources(section)
    )

    # ========================================================
    # 7 PEOPLE
    # ========================================================

    section = data.get(
        "key_people_involved",
        {}
    )

    add_heading(
        doc,
        7,
        "Key People Involved"
    )

    render_people(
        doc,
        get_content(section)
    )

    add_source(
        doc,
        get_sources(section)
    )

    # ========================================================
    # 8 OTHER INFORMATION
    # ========================================================

    section = data.get(
        "other_relevant_information",
        {}
    )

    add_heading(
        doc,
        8,
        "Other Relevant Information"
    )

    render_other(
        doc,
        get_content(section)
    )

    add_source(
        doc,
        get_sources(section)
    )

    # ========================================================
    # SAVE
    # ========================================================

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    doc.save(output_path)

    print()
    print("=" * 70)
    print("DOCMINDAI WORD DOCUMENT GENERATED")
    print("=" * 70)
    print(f"Output: {output_path}")
    print("Scope: FORCED SPECIFICATION-BASED RENDERING")
    print("Sources: Page + Chunk only")
    print("Evidence text: hidden")
    print("Procedure: Structured numbered steps")
    print("Formatting: Arial / Borders / Tables / Line spacing")
    print("=" * 70)

    return output_path


# ============================================================
# COMPATIBILITY ALIAS
# ============================================================

def generate_method_statement_docx(
    data=None,
    output_path=None,
    **kwargs
):

    return generate_docx(
        method_statement_data=data,
        output_path=output_path,
        **kwargs
    )