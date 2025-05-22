import json
import re
from typing import Dict, Optional


def load_flow_content(path: str, replacements: Optional[Dict[str, str]] = None) -> str:
    """
    Load the template file and handle replacements
    To replace `${LambdaFunctionARN}` placeholder in the template, pass in {'LambdaFunctionARN': 'string'}

    Args:
        path: Path to the flow content file
        replacements: Dictionary of replacements where key is the placeholder name
                      and value is the replacement string

    Returns:
        JSON string with replacements applied

    Raises:
        Exception: If there are unreplaced ARNs or placeholders in the template
    """
    # Read the file content
    with open(path, 'r') as file:
        flow_content = file.read()

    # Check for unreplaced ARNs
    arn_pattern = r'"arn:aws:.+:.+:[0-9]+:.+"'
    arns = [
        arn for arn in re.findall(arn_pattern, flow_content) if '${Token[' not in arn
    ]

    if arns:
        raise Exception(f'Found unreplaced arns ({", ".join(arns)}) in path: {path}')

    # Apply replacements if provided
    if replacements:
        for find, replace in replacements.items():
            flow_content = re.sub(r'\$\{' + find + r'\}', replace, flow_content)

    # Check for unreplaced placeholders
    placeholder_pattern = r'\$\{.*\}'
    placeholders = [
        p for p in re.findall(placeholder_pattern, flow_content) if '${Token[' not in p
    ]

    if placeholders:
        raise Exception(
            f'Found unreplaced placeholders ({", ".join(placeholders)}) in path: {path}'
        )

    # Verify it parses and remove line breaks
    return json.dumps(json.loads(flow_content))
