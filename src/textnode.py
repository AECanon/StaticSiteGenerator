from enum import Enum
from htmlnode import HTMLNode, LeafNode, ParentNode
import re

class TextType(Enum):
    TEXT = "text"
    BOLD = "bold"
    ITALIC = "italic"
    CODE = "code"
    LINK = "link"
    IMAGE = "image"

class BlockType(Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    CODE = "code"
    QUOTE = "quote"
    UNORDERED_LIST = "unordered_list"
    ORDERED_LIST = "ordered_list"

class TextNode:
    def __init__(self, text, text_type, url=None):
        self.text = text
        self.text_type = text_type
        self.url = url

    def __eq__(self, other):
        if not isinstance(other, TextNode):
            return False
        return (
            self.text == other.text and
            self.text_type == other.text_type and
            self.url == other.url
        )

    def __repr__(self):
        return f"TextNode({self.text!r}, {self.text_type.value!r}, {self.url!r})"

def markdown_to_blocks(markdown):
    blocks = markdown.split("\n\n")
    processed_blocks = []
    for block in blocks:
        stripped = block.strip()
        if stripped != "":
            processed_blocks.append(stripped)
    return processed_blocks

def block_to_block_type(block: str) -> BlockType:
    lines = block.split('\n')
    
    # Check for heading (1-6 # followed by space)
    if len(lines) == 1 and re.match(r'^#{1,6} ', lines[0]):
        return BlockType.HEADING
    
    # Check for code block
    if len(lines) >= 1:
        first_line = lines[0].strip()
        last_line = lines[-1].strip()
        if first_line.startswith('```'):
            if len(lines) == 1:
                if block.strip().startswith('```') and block.strip().endswith('```') and len(block.strip()) > 6:
                    return BlockType.CODE
                return BlockType.PARAGRAPH
            elif last_line.startswith('```'):
                return BlockType.CODE
            else:
                return BlockType.PARAGRAPH
    
    # Check for quote block (every line starts with >)
    if all(line.startswith('>') for line in lines):
        return BlockType.QUOTE
    
    # Check for unordered list (every line starts with - )
    if all(line.startswith('- ') for line in lines):
        return BlockType.UNORDERED_LIST
    
    # Check for ordered list (1. 2. 3. etc.)
    ordered_list_valid = True
    for i, line in enumerate(lines, start=1):
        if not re.match(rf'^{i}\. ', line):
            ordered_list_valid = False
            break
    if ordered_list_valid and len(lines) > 0:
        return BlockType.ORDERED_LIST
    
    return BlockType.PARAGRAPH

def extract_markdown_images(text):
    return re.findall(r"!\[([^\[\]]*)\]\(([^\(\)]*)\)", text)

def extract_markdown_links(text):
    return re.findall(r"(?<!!)\[([^\[\]]*)\]\(([^\(\)]*)\)", text)

def text_node_to_html_node(text_node):
    if not isinstance(text_node, TextNode):
        raise ValueError("Input must be a TextNode")
    
    if text_node.text_type == TextType.TEXT:
        return LeafNode(None, text_node.text)
    elif text_node.text_type == TextType.BOLD:
        return LeafNode("b", text_node.text)
    elif text_node.text_type == TextType.ITALIC:
        return LeafNode("i", text_node.text)
    elif text_node.text_type == TextType.CODE:
        return LeafNode("code", text_node.text)
    elif text_node.text_type == TextType.LINK:
        if not text_node.url:
            raise ValueError("Link TextNode requires a url")
        return LeafNode("a", text_node.text, {"href": text_node.url})
    elif text_node.text_type == TextType.IMAGE:
        if not text_node.url:
            raise ValueError("Image TextNode requires a url")
        return LeafNode("img", "", {"src": text_node.url, "alt": text_node.text})
    else:
        raise ValueError(f"Invalid text type: {text_node.text_type}")

def split_nodes_delimiter(old_nodes, delimiter, text_type):
    new_nodes = []
    for node in old_nodes:
        if not isinstance(node, TextNode) or node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        
        parts = node.text.split(delimiter)
        if len(parts) % 2 == 0:
            raise ValueError(f"Unmatched delimiter {delimiter} in text")
        
        for i, part in enumerate(parts):
            if not part:
                continue
            if i % 2 == 0:
                new_nodes.append(TextNode(part, TextType.TEXT))
            else:
                new_nodes.append(TextNode(part, text_type))
    
    return new_nodes

def split_nodes_image(old_nodes):
    new_nodes = []
    for node in old_nodes:
        if not isinstance(node, TextNode) or node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        
        text = node.text
        if not text:  # Skip empty text nodes
            continue
            
        images = extract_markdown_images(text)
        if not images:
            new_nodes.append(node)
            continue
        
        remaining_text = text
        for alt_text, url in images:
            parts = remaining_text.split(f"![{alt_text}]({url})", 1)
            if parts[0]:
                new_nodes.append(TextNode(parts[0], TextType.TEXT))
            new_nodes.append(TextNode(alt_text, TextType.IMAGE, url))
            remaining_text = parts[1] if len(parts) > 1 else ""
        
        if remaining_text:
            new_nodes.append(TextNode(remaining_text, TextType.TEXT))
    
    return new_nodes

def split_nodes_link(old_nodes):
    new_nodes = []
    for node in old_nodes:
        if not isinstance(node, TextNode) or node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        
        text = node.text
        if not text:  # Skip empty text nodes
            continue
            
        links = extract_markdown_links(text)
        if not links:
            new_nodes.append(node)
            continue
        
        remaining_text = text
        for link_text, url in links:
            parts = remaining_text.split(f"[{link_text}]({url})", 1)
            if parts[0]:
                new_nodes.append(TextNode(parts[0], TextType.TEXT))
            new_nodes.append(TextNode(link_text, TextType.LINK, url))
            remaining_text = parts[1] if len(parts) > 1 else ""
        
        if remaining_text:
            new_nodes.append(TextNode(remaining_text, TextType.TEXT))
    
    return new_nodes

def text_to_textnodes(text):
    nodes = [TextNode(text, TextType.TEXT)]
    nodes = split_nodes_image(nodes)
    nodes = split_nodes_link(nodes)
    nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "*", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "_", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
    return nodes

def text_to_children(text):
    """Convert a string with inline Markdown to a list of HTMLNode objects."""
    text_nodes = text_to_textnodes(text)
    return [text_node_to_html_node(node) for node in text_nodes]

def heading_block_to_html(block):
    """Convert a heading block to an HTMLNode (h1-h6)."""
    match = re.match(r'^(#{1,6}) ', block)
    if not match:
        raise ValueError("Invalid heading format")
    level = len(match.group(1))
    content = block.lstrip('# ').strip()
    children = text_to_children(content)
    return ParentNode(f"h{level}", children)

def paragraph_block_to_html(block):
    """Convert a paragraph block to an HTMLNode (p)."""
    children = text_to_children(block)
    if not children:
        children = [LeafNode(None, "")]
    return ParentNode("p", children)

def code_block_to_html(block):
    """Convert a code block to an HTMLNode (pre > code)."""
    # Remove leading/trailing whitespace
    block = block.strip()
    # Remove ``` delimiters
    content = block.removeprefix('```').removesuffix('```').strip()
    # Split into lines to handle language specifier
    lines = content.split('\n')
    # Skip the first line if it's a language specifier (alphanumeric)
    if len(lines) > 1 and re.match(r'^[a-zA-Z0-9_-]+$', lines[0].strip()):
        content = '\n'.join(lines[1:]).strip()
    # Create the HTML node with the content
    code_node = text_node_to_html_node(TextNode(content, TextType.TEXT))
    return ParentNode("pre", [ParentNode("code", [code_node])])

def quote_block_to_html(block):
    """Convert a quote block to an HTMLNode (blockquote)."""
    # Remove '>' from each line and join
    content = '\n'.join(line.lstrip('>').strip() for line in block.split('\n') if line.strip())
    children = text_to_children(content)
    return ParentNode("blockquote", children)

def unordered_list_block_to_html(block):
    """Convert an unordered list block to an HTMLNode (ul)."""
    items = block.split('\n')
    children = []
    for item in items:
        if item.strip():
            content = item.lstrip('- ').strip()
            item_children = text_to_children(content)
            children.append(ParentNode("li", item_children))
    return ParentNode("ul", children)

def ordered_list_block_to_html(block):
    """Convert an ordered list block to an HTMLNode (ol)."""
    items = block.split('\n')
    children = []
    for item in items:
        if item.strip():
            content = re.sub(r'^\d+\.\s+', '', item).strip()
            item_children = text_to_children(content)
            children.append(ParentNode("li", item_children))
    return ParentNode("ol", children)

def strip_block_prefix(block, block_type):
    """Strip block-specific prefixes (e.g., #, >, -, 1.) from block content."""
    if block_type == BlockType.HEADING:
        return block.lstrip('# ').strip()
    elif block_type == BlockType.QUOTE:
        return '\n'.join(line.lstrip('>').strip() for line in block.split('\n') if line.strip())
    elif block_type == BlockType.UNORDERED_LIST:
        return '\n'.join(line.lstrip('- ').strip() for line in block.split('\n') if line.strip())
    elif block_type == BlockType.ORDERED_LIST:
        return '\n'.join(re.sub(r'^\d+\.\s+', '', line).strip() for line in block.split('\n') if line.strip())
    elif block_type == BlockType.CODE:
        lines = block.strip().split('\n')
        if len(lines) == 1:
            # Single-line code block
            return lines[0].removeprefix('```').removesuffix('```').strip()
        # Multi-line code block: exclude first and last lines
        return '\n'.join(lines[1:-1]).strip()
    return block

def markdown_to_html_node(markdown):
    """Convert a Markdown document to a single parent HTMLNode (div)."""
    blocks = markdown_to_blocks(markdown)
    block_nodes = []
    
    for block in blocks:
        block_type = block_to_block_type(block)
        if block_type == BlockType.HEADING:
            block_node = heading_block_to_html(block)
        elif block_type == BlockType.PARAGRAPH:
            block_node = paragraph_block_to_html(block)
        elif block_type == BlockType.CODE:
            block_node = code_block_to_html(block)
        elif block_type == BlockType.QUOTE:
            block_node = quote_block_to_html(block)
        elif block_type == BlockType.UNORDERED_LIST:
            block_node = unordered_list_block_to_html(block)
        elif block_type == BlockType.ORDERED_LIST:
            block_node = ordered_list_block_to_html(block)
        else:
            raise ValueError(f"Unknown block type: {block_type}")
        block_nodes.append(block_node)
    
    if not block_nodes:
        return ParentNode("div", [LeafNode(None, "")])
    return ParentNode("div", block_nodes)

def extract_title(markdown):
    """
    Extract the h1 header from a Markdown string.
    
    Args:
        markdown (str): The Markdown text to parse.
    
    Returns:
        str: The text of the h1 header, stripped of '#' and whitespace.
    
    Raises:
        ValueError: If no h1 header (single '#') is found.
    """
    lines = markdown.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('# ') and not line.startswith('##'):
            return line.lstrip('# ').strip()
    raise ValueError("No h1 header found in Markdown")