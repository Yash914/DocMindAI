import json
import re
import requests


# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL_NAME = "llama3"


# ============================================================
# CALL OLLAMA
# ============================================================

def generate_text(
    prompt,
    temperature=0.1
):

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temperature
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=300
    )

    response.raise_for_status()

    data = response.json()

    return data.get(
        "response",
        ""
    )


# ============================================================
# EXTRACT JSON OBJECT
# ============================================================

def _extract_json(text):

    if not text:
        raise ValueError(
            "LLM returned an empty response."
        )

    text = text.strip()

    # --------------------------------------------------------
    # Remove markdown fences
    # --------------------------------------------------------

    text = re.sub(
        r"```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"```\s*",
        "",
        text
    )

    text = text.strip()

    # --------------------------------------------------------
    # Direct JSON
    # --------------------------------------------------------

    try:

        return json.loads(
            text
        )

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Find first complete JSON object
    # --------------------------------------------------------

    start = text.find(
        "{"
    )

    if start == -1:

        raise ValueError(
            "Could not find JSON object in LLM response."
        )

    depth = 0
    in_string = False
    escaped = False

    for i in range(
        start,
        len(text)
    ):

        char = text[i]

        # --------------------------------------------
        # Handle JSON strings
        # --------------------------------------------

        if char == '"' and not escaped:

            in_string = not in_string

        if char == "\\" and not escaped:

            escaped = True

        else:

            escaped = False

        if in_string:

            continue

        # --------------------------------------------
        # Brackets
        # --------------------------------------------

        if char == "{":

            depth += 1

        elif char == "}":

            depth -= 1

            if depth == 0:

                candidate = text[
                    start:i + 1
                ]

                try:

                    return json.loads(
                        candidate
                    )

                except json.JSONDecodeError:

                    pass

    # --------------------------------------------------------
    # Nothing worked
    # --------------------------------------------------------

    raise ValueError(
        "Could not find a complete JSON object "
        "in LLM response."
    )


# ============================================================
# GENERATE JSON
# ============================================================

def generate_json(
    prompt
):

    raw_response = generate_text(
        prompt
    )

    try:

        return _extract_json(
            raw_response
        )

    except Exception as error:

        print()
        print(
            "=" * 70
        )

        print(
            "LLM JSON PARSING ERROR"
        )

        print(
            "=" * 70
        )

        print(
            "Error:",
            error
        )

        print()
        print(
            "RAW LLM RESPONSE:"
        )

        print(
            "-" * 70
        )

        print(
            raw_response
        )

        print(
            "-" * 70
        )

        raise