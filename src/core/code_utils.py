import logging


def normalize_code(code: str) -> str:
    """Normalize code for consistent diffing."""
    # Debug: Log original line endings
    crlf_count = code.count("\r\n")
    lf_count = code.count("\n") - crlf_count
    cr_count = code.count("\r") - crlf_count
    logging.debug(
        f"Original line endings - CRLF: {crlf_count}, LF: {lf_count}, CR: {cr_count}"
    )

    # Convert all line endings to \n
    code = code.replace("\r\n", "\n").replace("\r", "\n")

    # Debug: Log whitespace
    lines = code.split("\n")
    for i, line in enumerate(lines):
        if line.rstrip() != line:
            logging.debug(f"Line {i+1} has trailing whitespace: {repr(line)}")

    # Split into lines while preserving empty lines
    normalized_lines = []
    for line in lines:
        # Preserve empty lines
        if not line.strip():
            normalized_lines.append("")
            continue

        # Remove trailing whitespace but preserve indentation
        indent = len(line) - len(line.lstrip())
        content = line.rstrip()
        normalized_lines.append(" " * indent + content)

    result = "\n".join(normalized_lines)
    lf_count_result = result.count("\n")
    logging.debug(f"Final line endings - LF: {lf_count_result}")
    return result
