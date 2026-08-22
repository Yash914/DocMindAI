from pathlib import Path
import sys
import json


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from method_statement.docx_generator import (
    generate_docx
)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("DOCMINDAI WORD DOCUMENT GENERATOR")
    print("=" * 70)

    # --------------------------------------------------------
    # JSON produced by previous step
    # --------------------------------------------------------

    json_path = (
        PROJECT_ROOT
        / "method_statement"
        / "method_statement_output.json"
    )

    if not json_path.exists():

        print()
        print("ERROR:")
        print(
            "method_statement_output.json was not found."
        )

        print()
        print(
            "Run this first:"
        )

        print(
            "python method_statement/test_method_statement_generator.py"
        )

        return

    # --------------------------------------------------------
    # Load JSON
    # --------------------------------------------------------

    with open(
        json_path,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(
            file
        )

    method_statement = data.get(
        "method_statement",
        {}
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    output_path = (
        PROJECT_ROOT
        / "method_statement"
        / "RCC_Method_Statement.docx"
    )

    # --------------------------------------------------------
    # Generate
    # --------------------------------------------------------

    result = generate_docx(
        method_statement_data=method_statement,

        output_path=output_path,

        team_name="DocMindAI",

        team_id="YOUR_TEAM_ID",

        team_members=[
            "Prachi Dashrath",
            "Lisha Talele",
            "Yash Madane",
            "Shubham Aher"
        ],

        source_document="S-2_sr.pdf"
    )

    print()
    print("=" * 70)
    print("WORD DOCUMENT GENERATED")
    print("=" * 70)

    print()
    print(result)

    print()
    print("=" * 70)
    print("NEXT STEP")
    print("=" * 70)

    print(
        "Open the DOCX and verify that it is within 6 pages."
    )


if __name__ == "__main__":
    main()