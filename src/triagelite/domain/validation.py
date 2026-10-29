from pydantic import ValidationError


def format_validation_errors(error: ValidationError) -> list[str]:
    """Turn Pydantic errors into short `path: message` lines, without echoing input values."""
    return [
        f"{'.'.join(str(part) for part in detail['loc']) or '<root>'}: {detail['msg']}"
        for detail in error.errors(include_url=False)
    ]
