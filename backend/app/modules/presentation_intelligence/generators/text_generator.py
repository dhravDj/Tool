"""Plain text generator for Presentation Intelligence documents."""

from app.modules.presentation_intelligence.schemas.presentation_document import (
    ElementType,
    PresentationDocument,
)


class PresentationTextGenerator:
    """Generates clean, readable plain text from a PresentationDocument."""

    @classmethod
    def generate(cls, doc: PresentationDocument) -> str:
        """Convert PresentationDocument into plain text stream."""
        lines: list[str] = []

        title = doc.metadata.title or "Untitled Presentation"
        lines.append(title.upper())
        lines.append("=" * len(title))
        lines.append(f"Total Slides: {doc.slide_count}")
        lines.append("")

        for slide in doc.slides:
            lines.append(f"--- SLIDE {slide.slide_number}: {slide.title or 'Untitled'} ---")
            lines.append("")

            for elem in slide.elements:
                if elem.element_type in (ElementType.TITLE, ElementType.TEXT):
                    if elem.paragraphs:
                        for p in elem.paragraphs:
                            indent = "  " * p.level
                            prefix = "- " if p.bullet or p.level > 0 else ""
                            lines.append(f"{indent}{prefix}{p.text.strip()}")
                    elif elem.text:
                        lines.append(elem.text.strip())

            # Speaker Notes
            if slide.speaker_notes and slide.speaker_notes.strip():
                lines.append("")
                lines.append("[Speaker Notes]")
                lines.append(slide.speaker_notes.strip())

            lines.append("")

        return "\n".join(lines).strip() + "\n"
