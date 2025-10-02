import re

def check_references(text):
    issues = []
    references = re.findall(r"\[\d+\].*", text)

    if not references:
        return ["No references found. Add references section."]

    for ref in references:
        # Basic IEEE format: [1] A. Author, "Title," Journal, vol., no., pp., Year.
        if not re.match(r"\[\d+\]\s.+?,\s\".+?\",.+\d{4}", ref):
            issues.append(f"Issue with reference: {ref}")

    if not issues:
        issues.append("✅ All references appear to follow IEEE style.")

    return issues
