"""Tree view generator rendering hierarchical directory diagrams."""

from app.modules.archive_intelligence.schemas.archive_document import ArchiveHierarchyNode


class ArchiveTreeGenerator:
    """Renders ASCII / Unicode hierarchy tree diagrams for archives."""

    def generate(self, root: ArchiveHierarchyNode) -> str:
        """Render complete archive hierarchy tree as formatted string."""
        lines: list[str] = [
            f"{root.name}/ (total: {root.file_count} files, {self._format_bytes(root.total_size)})"
        ]
        self._render_node(root, prefix="", is_last=True, lines=lines)
        return "\n".join(lines)

    def _render_node(
        self,
        node: ArchiveHierarchyNode,
        prefix: str,
        is_last: bool,
        lines: list[str],
    ) -> None:
        children = node.children
        for idx, child in enumerate(children):
            child_is_last = idx == len(children) - 1
            branch = "└── " if child_is_last else "├── "
            indent = "    " if child_is_last else "│   "

            if child.is_directory:
                info = f"{child.name}/ ({child.file_count} files, {self._format_bytes(child.total_size)})"
                if child.warnings:
                    info += f" [! {len(child.warnings)} warning(s)]"
                lines.append(f"{prefix}{branch}{info}")
                self._render_node(child, prefix=prefix + indent, is_last=child_is_last, lines=lines)
            else:
                tag = " [ARCHIVE]" if child.is_nested_archive else ""
                info = f"{child.name} ({self._format_bytes(child.total_size)}){tag}"
                if child.warnings:
                    info += f" [! {len(child.warnings)} warning(s)]"
                lines.append(f"{prefix}{branch}{info}")

    @staticmethod
    def _format_bytes(size: int) -> str:
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.2f} MB"
