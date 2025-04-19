from .base import ContentProcessor
import re


class IndentedBulletPointsProcessor(ContentProcessor):
    """
    Process indented bullet points with tabs and convert them to a format compatible with Reflect.

    1. Removes one level of tab indentation from bullet points directly under headings
    2. Preserves the hierarchical structure of nested bullet points
    3. Ensures proper indentation levels are maintained throughout bullet hierarchies
    4. Preserves indentation for list items that contain headings with tasks
    """

    def process(
        self,
        content,
        parent_is_heading=False,
        heading_child_level=None,
        heading_root=False,
        heading_root_level=0,
    ):
        # --- Tree Node definition ---
        class Node:
            def __init__(self, line, indent):
                self.line = line
                self.indent = indent
                self.children = []

        # --- Parse lines into a tree ---
        def parse_tree(lines):
            root = Node(None, -1)
            stack = [root]
            for line in lines:
                indent = 0
                for char in line:
                    if char == "\t":
                        indent += 1
                    else:
                        break
                node = Node(line.lstrip("\t"), indent)
                # Find parent
                while stack and stack[-1].indent >= indent:
                    stack.pop()
                stack[-1].children.append(node)
                stack.append(node)
            return root

        # --- Process the tree recursively ---
        def process_node(
            node, parent_is_heading=False, heading_root=False, heading_root_level=0
        ):
            output = []
            for child in node.children:
                trimmed = child.line.lstrip()
                is_section_heading = child.line.strip().startswith("#")
                is_bullet = trimmed.startswith("- ")
                # No more bullet promotion logic
                if is_section_heading:
                    output.append(child.line)
                    # For children, set heading_root=True and heading_root_level=1
                    output.extend(
                        process_node(
                            child,
                            parent_is_heading=False,
                            heading_root=True,
                            heading_root_level=1,
                        )
                    )
                elif heading_root and is_bullet:
                    # Bullet child of a section, output with (indent - heading_root_level) tabs
                    bullet_indent = max(child.indent - heading_root_level, 0)
                    output.append(("\t" * bullet_indent) + trimmed)
                    output.extend(
                        process_node(
                            child,
                            parent_is_heading=False,
                            heading_root=True,
                            heading_root_level=heading_root_level,
                        )
                    )
                elif heading_root and not is_bullet:
                    # Non-bullet child of a section, output with (indent - heading_root_level) tabs
                    prop_indent = max(child.indent - heading_root_level, 0)
                    output.append(("\t" * prop_indent) + child.line)
                    output.extend(
                        process_node(
                            child,
                            parent_is_heading=False,
                            heading_root=True,
                            heading_root_level=heading_root_level,
                        )
                    )
                else:
                    # For all other lines, preserve original indentation
                    output.append(("\t" * child.indent) + child.line)
                    output.extend(
                        process_node(
                            child,
                            parent_is_heading=False,
                            heading_root=False,
                            heading_root_level=0,
                        )
                    )
            return output

        lines = content.split("\n") if content else []
        tree = parse_tree(lines)
        processed_lines = process_node(
            tree,
            parent_is_heading=parent_is_heading,
            heading_root=heading_root,
            heading_root_level=heading_root_level,
        )
        new_content = "\n".join(processed_lines)
        return new_content, new_content != content
