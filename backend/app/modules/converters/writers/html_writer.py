"""HTML writer for universal content extraction with complete script sanitization."""

import html

from app.modules.converters.schemas import UniversalContent, UniversalTable


class HtmlWriter:
    """Generates clean, styled, semantic HTML document from UniversalContent."""

    CSS_STYLES = """
    :root {
      --bg: #ffffff;
      --text: #1f2937;
      --heading: #111827;
      --border: #e5e7eb;
      --muted: #6b7280;
      --primary: #2563eb;
      --code-bg: #f3f4f6;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #0f172a;
        --text: #e2e8f0;
        --heading: #f8fafc;
        --border: #334155;
        --muted: #94a3b8;
        --primary: #3b82f6;
        --code-bg: #1e293b;
      }
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      line-height: 1.6;
      color: var(--text);
      background-color: var(--bg);
      margin: 0;
      padding: 2rem 1rem;
    }
    .container {
      max-width: 860px;
      margin: 0 auto;
    }
    header.doc-header {
      border-bottom: 2px solid var(--border);
      padding-bottom: 1.5rem;
      margin-bottom: 2rem;
    }
    h1, h2, h3, h4, h5, h6 {
      color: var(--heading);
      font-weight: 600;
      margin-top: 1.8rem;
      margin-bottom: 0.8rem;
    }
    h1 { font-size: 2.25rem; }
    h2 { font-size: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 0.4rem; }
    h3 { font-size: 1.25rem; }
    p { margin-bottom: 1rem; }
    .meta-badge {
      display: inline-block;
      font-size: 0.85rem;
      color: var(--muted);
      background: var(--code-bg);
      padding: 0.2rem 0.6rem;
      border-radius: 4px;
      margin-right: 0.5rem;
      margin-bottom: 0.5rem;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 1.5rem 0;
      font-size: 0.95rem;
    }
    th, td {
      border: 1px solid var(--border);
      padding: 0.6rem 0.8rem;
      text-align: left;
    }
    th {
      background-color: var(--code-bg);
      color: var(--heading);
      font-weight: 600;
    }
    pre {
      background-color: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 1rem;
      overflow-x: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.9rem;
    }
    code {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      background: var(--code-bg);
      padding: 0.15rem 0.35rem;
      border-radius: 3px;
    }
    .transcript-segment {
      padding: 0.4rem 0;
      border-bottom: 1px dashed var(--border);
    }
    .timestamp {
      font-family: monospace;
      color: var(--primary);
      margin-right: 0.6rem;
      font-size: 0.9rem;
    }
    .speaker {
      font-weight: 600;
      margin-right: 0.4rem;
    }
    """

    @classmethod
    def write(cls, content: UniversalContent) -> str:
        body_parts: list[str] = []

        # Header section
        body_parts.append('<header class="doc-header">')
        title = content.title or content.source_filename
        body_parts.append(f"  <h1>{cls.escape(title)}</h1>")

        badges: list[str] = [
            f'<span class="meta-badge">Format: {cls.escape(content.source_format.upper())}</span>',
            f'<span class="meta-badge">Source: {cls.escape(content.source_filename)}</span>',
        ]
        if content.author:
            badges.append(f'<span class="meta-badge">Author: {cls.escape(content.author)}</span>')
        if content.page_count > 1:
            badges.append(f'<span class="meta-badge">Pages: {content.page_count}</span>')
        if content.word_count > 0:
            badges.append(f'<span class="meta-badge">Words: {content.word_count:,}</span>')

        body_parts.append(f"  <div class=\"meta-badges\">{''.join(badges)}</div>")
        body_parts.append("</header>")

        # Media transcripts
        if content.transcript_segments:
            body_parts.append('<section class="transcript-section">')
            body_parts.append("  <h2>Speech Transcript</h2>")
            for seg in content.transcript_segments:
                start_m, start_s = divmod(int(seg.start_seconds), 60)
                time_str = f"{start_m:02d}:{start_s:02d}"
                speaker_html = f'<span class="speaker">{cls.escape(seg.speaker)}:</span>' if seg.speaker else ""
                body_parts.append(
                    f'  <div class="transcript-segment"><span class="timestamp">[{time_str}]</span>'
                    f"{speaker_html} {cls.escape(seg.text)}</div>"
                )
            body_parts.append("</section>")

        # Sections
        if content.sections:
            for sec in content.sections:
                lvl = max(1, min(6, sec.level))
                heading_tag = f"h{lvl}"
                body_parts.append(f"<{heading_tag}>{cls.escape(sec.title)}</{heading_tag}>")
                if sec.content:
                    for para in sec.content.split("\n\n"):
                        clean_para = para.strip()
                        if clean_para:
                            body_parts.append(f"<p>{cls.escape(clean_para)}</p>")

        # Paragraphs (if no sections)
        elif content.paragraphs:
            for p in content.paragraphs:
                clean_p = p.strip()
                if clean_p:
                    body_parts.append(f"<p>{cls.escape(clean_p)}</p>")

        # Code blocks
        if content.code_blocks:
            for cb in content.code_blocks:
                caption = f"<h4>{cls.escape(cb.caption)}</h4>" if cb.caption else ""
                body_parts.append(caption)
                body_parts.append(f"<pre><code>{cls.escape(cb.code)}</code></pre>")

        # Tables
        if content.tables:
            for tbl in content.tables:
                table_html = cls._render_table(tbl)
                if table_html:
                    body_parts.append(table_html)

        # Fallback to raw text
        if not content.sections and not content.paragraphs and not content.tables and not content.code_blocks:
            if content.raw_text:
                body_parts.append(f"<pre>{cls.escape(content.raw_text)}</pre>")

        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{cls.escape(title)}</title>
  <style>
{cls.CSS_STYLES}
  </style>
</head>
<body>
  <main class="container">
{"".join(body_parts)}
  </main>
</body>
</html>
"""
        return full_html

    @classmethod
    def _render_table(cls, tbl: UniversalTable) -> str:
        """Render a UniversalTable into styled, sanitized HTML table."""
        if not tbl.rows and not tbl.headers:
            return ""

        parts: list[str] = []
        name = tbl.title or tbl.sheet_name
        if name:
            parts.append(f"<h3>{cls.escape(name)}</h3>")

        parts.append("<table>")

        if tbl.headers:
            parts.append("  <thead>\n    <tr>")
            for h in tbl.headers:
                parts.append(f"      <th>{cls.escape(str(h))}</th>")
            parts.append("    </tr>\n  </thead>")

        if tbl.rows:
            parts.append("  <tbody>")
            for row in tbl.rows:
                parts.append("    <tr>")
                for cell in row:
                    val = str(cell) if cell is not None else ""
                    parts.append(f"      <td>{cls.escape(val)}</td>")
                parts.append("    </tr>")
            parts.append("  </tbody>")

        parts.append("</table>")
        return "\n".join(parts)

    @staticmethod
    def escape(text: str) -> str:
        """Strictly escape HTML characters to prevent XSS / script execution."""
        return html.escape(str(text), quote=True)
