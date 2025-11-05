"""
Document Naming Convention Utilities.

This module provides standardized naming conventions for all documents in GAO-Dev,
ensuring consistency, discoverability, and professionalism.

Standard Pattern: {DocType}_{subject}_{date}_v{version}.{ext}
Example: PRD_user-authentication_2024-11-05_v1.0.md

Special Cases:
- ADRs: ADR-001_database-choice_2024-09-01.md
- Postmortems: Postmortem_2024-11-15_api-outage.md
- Runbooks: Runbook_kafka-cluster-restart_2024-08-01_v1.3.md
"""

import re
from datetime import datetime
from typing import Dict, Tuple, Optional


class DocumentNamingConvention:
    """
    Enforce standardized document naming convention.

    This class provides utilities for generating, parsing, and validating
    document filenames according to GAO-Dev standards.
    """

    # Standard pattern for most documents
    PATTERN = re.compile(
        r"^(?P<doctype>[A-Z]+(?:-\d+)?)_"
        r"(?P<subject>[a-z0-9-]+)_"
        r"(?P<date>\d{4}-\d{2}-\d{2})_"
        r"v(?P<version>\d+\.\d+)"
        r"\.(?P<ext>\w+)$"
    )

    # Special pattern for ADRs (Architecture Decision Records)
    ADR_PATTERN = re.compile(
        r"^ADR-(?P<number>\d+)_"
        r"(?P<subject>[a-z0-9-]+)_"
        r"(?P<date>\d{4}-\d{2}-\d{2})"
        r"\.(?P<ext>\w+)$"
    )

    # Special pattern for Postmortems
    POSTMORTEM_PATTERN = re.compile(
        r"^Postmortem_"
        r"(?P<date>\d{4}-\d{2}-\d{2})_"
        r"(?P<subject>[a-z0-9-]+)"
        r"\.(?P<ext>\w+)$"
    )

    # Special pattern for Runbooks (with version)
    RUNBOOK_PATTERN = re.compile(
        r"^Runbook_"
        r"(?P<subject>[a-z0-9-]+)_"
        r"(?P<date>\d{4}-\d{2}-\d{2})_"
        r"v(?P<version>\d+\.\d+)"
        r"\.(?P<ext>\w+)$"
    )

    @staticmethod
    def generate_filename(
        doc_type: str,
        subject: str,
        version: str = "1.0",
        ext: str = "md",
        date: Optional[str] = None,
        adr_number: Optional[int] = None,
    ) -> str:
        """
        Generate standard filename according to document type.

        Args:
            doc_type: Document type (PRD, ARCHITECTURE, ADR, POSTMORTEM, RUNBOOK, etc.)
            subject: Subject slug or description (spaces will be converted to hyphens)
            version: Version string (default: "1.0")
            ext: File extension (default: "md")
            date: Optional date string (YYYY-MM-DD). Defaults to today.
            adr_number: For ADRs only, the sequential number (e.g., 1, 2, 3)

        Returns:
            Standard filename

        Examples:
            >>> DocumentNamingConvention.generate_filename("PRD", "user authentication", "2.0")
            "PRD_user-authentication_2024-11-05_v2.0.md"

            >>> DocumentNamingConvention.generate_filename("ADR", "database choice", adr_number=1)
            "ADR-001_database-choice_2024-11-05.md"

            >>> DocumentNamingConvention.generate_filename("POSTMORTEM", "api outage")
            "Postmortem_2024-11-05_api-outage.md"

            >>> DocumentNamingConvention.generate_filename("RUNBOOK", "kafka restart", "1.3")
            "Runbook_kafka-restart_2024-11-05_v1.3.md"
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # Normalize subject: lowercase, replace spaces/underscores with hyphens
        subject_slug = (
            subject.lower()
            .replace(" ", "-")
            .replace("_", "-")
            .replace("/", "-")
            .strip("-")
        )

        # Remove any characters that aren't alphanumeric or hyphens
        subject_slug = re.sub(r"[^a-z0-9-]", "", subject_slug)

        # Collapse multiple consecutive hyphens into single hyphen
        subject_slug = re.sub(r"-+", "-", subject_slug)

        # Handle special cases
        doc_type_upper = doc_type.upper()

        if doc_type_upper == "ADR":
            if adr_number is None:
                raise ValueError("ADR requires adr_number parameter")
            return f"ADR-{adr_number:03d}_{subject_slug}_{date}.{ext}"

        elif doc_type_upper == "POSTMORTEM":
            return f"Postmortem_{date}_{subject_slug}.{ext}"

        elif doc_type_upper == "RUNBOOK":
            return f"Runbook_{subject_slug}_{date}_v{version}.{ext}"

        else:
            # Standard pattern
            return f"{doc_type_upper}_{subject_slug}_{date}_v{version}.{ext}"

    @staticmethod
    def parse_filename(filename: str) -> Dict[str, str]:
        """
        Parse filename into components.

        Args:
            filename: The filename to parse

        Returns:
            Dictionary with extracted components (doctype, subject, date, version, ext)

        Raises:
            ValueError: If filename does not match any known pattern

        Examples:
            >>> DocumentNamingConvention.parse_filename("PRD_user-auth_2024-11-05_v1.0.md")
            {'doctype': 'PRD', 'subject': 'user-auth', 'date': '2024-11-05',
             'version': '1.0', 'ext': 'md'}

            >>> DocumentNamingConvention.parse_filename("ADR-001_database-choice_2024-09-01.md")
            {'doctype': 'ADR', 'number': '001', 'subject': 'database-choice',
             'date': '2024-09-01', 'ext': 'md'}
        """
        # Try ADR pattern first
        match = DocumentNamingConvention.ADR_PATTERN.match(filename)
        if match:
            result = match.groupdict()
            result["doctype"] = "ADR"
            return result

        # Try Postmortem pattern
        match = DocumentNamingConvention.POSTMORTEM_PATTERN.match(filename)
        if match:
            result = match.groupdict()
            result["doctype"] = "POSTMORTEM"
            return result

        # Try Runbook pattern
        match = DocumentNamingConvention.RUNBOOK_PATTERN.match(filename)
        if match:
            result = match.groupdict()
            result["doctype"] = "RUNBOOK"
            return result

        # Try standard pattern
        match = DocumentNamingConvention.PATTERN.match(filename)
        if match:
            return match.groupdict()

        # No pattern matched
        raise ValueError(
            f"Filename does not match convention: {filename}\n"
            f"Expected patterns:\n"
            f"  Standard: {{DocType}}_{{subject}}_{{date}}_v{{version}}.{{ext}}\n"
            f"  ADR: ADR-{{NNN}}_{{subject}}_{{date}}.{{ext}}\n"
            f"  Postmortem: Postmortem_{{date}}_{{subject}}.{{ext}}\n"
            f"  Runbook: Runbook_{{subject}}_{{date}}_v{{version}}.{{ext}}"
        )

    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate filename against naming convention.

        Args:
            filename: The filename to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if valid, False otherwise
            - error_message: None if valid, error description if invalid

        Examples:
            >>> DocumentNamingConvention.validate_filename("PRD_user-auth_2024-11-05_v1.0.md")
            (True, None)

            >>> DocumentNamingConvention.validate_filename("invalid-filename.md")
            (False, "Filename does not match convention: invalid-filename.md...")
        """
        try:
            DocumentNamingConvention.parse_filename(filename)
            return (True, None)
        except ValueError as e:
            return (False, str(e))

    @staticmethod
    def is_special_case(doc_type: str) -> bool:
        """
        Check if document type is a special case with different naming pattern.

        Args:
            doc_type: Document type to check

        Returns:
            True if special case, False otherwise
        """
        return doc_type.upper() in ["ADR", "POSTMORTEM", "RUNBOOK"]

    @staticmethod
    def suggest_filename(current_name: str, doc_type: str, subject: str) -> str:
        """
        Suggest a properly formatted filename based on current name and metadata.

        Args:
            current_name: Current filename (possibly non-compliant)
            doc_type: Document type
            subject: Document subject

        Returns:
            Suggested compliant filename

        Example:
            >>> DocumentNamingConvention.suggest_filename("prd.md", "PRD", "User Auth")
            "PRD_user-auth_2024-11-05_v1.0.md"
        """
        # Extract extension from current name if present
        if "." in current_name:
            ext = current_name.split(".")[-1]
        else:
            ext = "md"

        # Try to parse version from current name
        version_match = re.search(r"v?(\d+\.\d+)", current_name)
        version = version_match.group(1) if version_match else "1.0"

        # Try to extract ADR number if it's an ADR
        if doc_type.upper() == "ADR":
            adr_match = re.search(r"ADR[-_]?(\d+)", current_name, re.IGNORECASE)
            if adr_match:
                return DocumentNamingConvention.generate_filename(
                    doc_type, subject, version, ext, adr_number=int(adr_match.group(1))
                )

        return DocumentNamingConvention.generate_filename(
            doc_type, subject, version, ext
        )
