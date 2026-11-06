"""Plain text writer for universal content extraction (Mode A)."""

from app.modules.converters.schemas import UniversalContent


class TxtWriter:
    """Converts UniversalContent into clean, readable plain UTF-8 text."""

    @classmethod
    def write(cls, content: UniversalContent) -> str:
        parts: list[str] = []

        if content.title:
            parts.append(content.title)
            parts.append("=" * len(content.title))
            parts.append("")

        if content.author:
            parts.append(f"Author: {content.author}")
            parts.append("")

        # Transcript segments (audio/video)
        if content.transcript_segments:
            for seg in content.transcript_segments:
                start_m, start_s = divmod(int(seg.start_seconds), 60)
                time_str = f"[{start_m:02d}:{start_s:02d}]"
                speaker_str = f"{seg.speaker}: " if seg.speaker else ""
                parts.append(f"{time_str} {speaker_str}{seg.text}")
            parts.append("")

        # Sections
        if content.sections:
            for sec in content.sections:
                if sec.page_or_slide_number:
                    parts.append(f"--- Section {sec.page_or_slide_number}: {sec.title} ---")
                else:
                    parts.append(f"--- {sec.title} ---")
                if sec.content:
                    parts.append(sec.content.strip())
                parts.append("")

        # Paragraphs (if not already captured in sections)
        if content.paragraphs and not content.sections:
            for p in content.paragraphs:
                p_clean = p.strip()
                if p_clean:
                    parts.append(p_clean)
                    parts.append("")

        # Code blocks
        if content.code_blocks:
            for cb in content.code_blocks:
                if cb.caption:
                    parts.append(f"[{cb.language.upper() or 'CODE'}: {cb.caption}]")
                parts.append(cb.code.strip())
                parts.append("")

        # Tables
        if content.tables:
            for tbl in content.tables:
                if tbl.title or tbl.sheet_name:
                    name = tbl.title or tbl.sheet_name
                    parts.append(f"[Table: {name}]")

                if tbl.headers:
                    parts.append("\t".join(str(h) for h in tbl.headers))
                    parts.append("-" * 40)

                for row in tbl.rows:
                    parts.append("\t".join(str(c) if c is not None else "" for c in row))
                parts.append("")

        # Fallback to raw_text if nothing was structured
        if not parts and content.raw_text:
            return content.raw_text.strip() + "\n"

        result = "\n".join(parts).strip()
        return result + "\n" if result else ""
