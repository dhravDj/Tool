"""Hierarchy builder for normalized archive tree representation."""

from app.modules.archive_intelligence.schemas.archive_document import (
    ArchiveEntry,
    ArchiveHierarchyNode,
)


class ArchiveHierarchyBuilder:
    """Constructs a normalized folder/file tree from a list of archive entries."""

    @classmethod
    def build_tree(
        cls,
        archive_name: str,
        entries: list[ArchiveEntry],
    ) -> ArchiveHierarchyNode:
        """Construct hierarchical directory tree from flat entry records."""
        root = ArchiveHierarchyNode(
            id="root",
            name=archive_name,
            path="",
            is_directory=True,
            is_nested_archive=False,
            children=[],
            file_count=0,
            total_size=0,
            warnings=[],
        )

        # Map full normalized folder path to node
        dir_map: dict[str, ArchiveHierarchyNode] = {"": root}

        # Track seen names per directory to detect duplicates and case collisions
        seen_case_sensitive: dict[str, set[str]] = {"": set()}
        seen_case_insensitive: dict[str, dict[str, str]] = {"": {}}

        # First pass: sort entries so parent directories are processed before files
        sorted_entries = sorted(entries, key=lambda e: e.normalized_path)

        for entry in sorted_entries:
            norm_path = entry.normalized_path.strip("/")
            if not norm_path or norm_path == ".":
                continue

            parts = norm_path.split("/")
            # Ensure all ancestor directory nodes exist
            curr_path = ""
            parent_node = root

            for part in parts[:-1]:
                curr_path = f"{curr_path}/{part}".lstrip("/")
                if curr_path not in dir_map:
                    dir_node = ArchiveHierarchyNode(
                        id=f"dir_{curr_path.replace('/', '_')}",
                        name=part,
                        path=curr_path,
                        is_directory=True,
                        is_nested_archive=False,
                        children=[],
                        file_count=0,
                        total_size=0,
                        warnings=[],
                    )
                    dir_map[curr_path] = dir_node
                    parent_node.children.append(dir_node)
                    seen_case_sensitive[curr_path] = set()
                    seen_case_insensitive[curr_path] = {}
                parent_node = dir_map[curr_path]

            leaf_name = parts[-1]
            parent_dir_path = "/".join(parts[:-1])

            # Check collisions in parent
            cs_set = seen_case_sensitive.setdefault(parent_dir_path, set())
            ci_map = seen_case_insensitive.setdefault(parent_dir_path, {})
            node_warnings: list[str] = []

            if leaf_name in cs_set:
                node_warnings.append(f"Duplicate entry name detected: '{leaf_name}'")
            else:
                cs_set.add(leaf_name)

            lower_leaf = leaf_name.lower()
            if lower_leaf in ci_map and ci_map[lower_leaf] != leaf_name:
                node_warnings.append(
                    f"Case collision detected with existing entry: '{ci_map[lower_leaf]}' vs '{leaf_name}'"
                )
            else:
                ci_map[lower_leaf] = leaf_name

            if entry.is_directory:
                dir_path = norm_path
                if dir_path not in dir_map:
                    dir_node = ArchiveHierarchyNode(
                        id=f"dir_{dir_path.replace('/', '_')}",
                        name=leaf_name,
                        path=dir_path,
                        is_directory=True,
                        is_nested_archive=False,
                        entry_id=entry.entry_id,
                        children=[],
                        file_count=0,
                        total_size=entry.uncompressed_size,
                        warnings=node_warnings,
                    )
                    dir_map[dir_path] = dir_node
                    parent_node.children.append(dir_node)
                    seen_case_sensitive[dir_path] = set()
                    seen_case_insensitive[dir_path] = {}
            else:
                # File node
                file_node = ArchiveHierarchyNode(
                    id=f"file_{entry.entry_id}",
                    name=leaf_name,
                    path=norm_path,
                    is_directory=False,
                    is_nested_archive=entry.is_nested_archive,
                    entry_id=entry.entry_id,
                    children=[],
                    file_count=1,
                    total_size=entry.uncompressed_size,
                    warnings=node_warnings,
                )
                parent_node.children.append(file_node)

        # Bottom-up rollup of file_count and total_size
        cls._rollup(root)
        return root

    @classmethod
    def _rollup(cls, node: ArchiveHierarchyNode) -> tuple[int, int]:
        """Recursively calculate file_count and total_size for directory nodes."""
        if not node.is_directory:
            return 1, node.total_size

        total_files = 0
        total_size = 0
        for child in node.children:
            c_files, c_size = cls._rollup(child)
            total_files += c_files
            total_size += c_size

        node.file_count = total_files
        node.total_size = total_size

        # Sort children: directories first, then alphabetical by name
        node.children.sort(key=lambda n: (0 if n.is_directory else 1, n.name.lower()))
        return total_files, total_size
