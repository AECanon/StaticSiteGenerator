import unittest
from textnode import (
    TextNode,
    TextType,
    split_nodes_delimiter,
    split_nodes_image,
    split_nodes_link,
    extract_markdown_images,
    extract_markdown_links,
    text_node_to_html_node,
    text_to_textnodes,
    markdown_to_blocks,
    block_to_block_type,
    BlockType,
    markdown_to_html_node,
    text_to_children,
    heading_block_to_html,
    paragraph_block_to_html,
    code_block_to_html,
    quote_block_to_html,
    unordered_list_block_to_html,
    ordered_list_block_to_html,
    strip_block_prefix,
    extract_title,  # Added for new tests
)
from htmlnode import HTMLNode, LeafNode, ParentNode


class TestTextNode(unittest.TestCase):
    def test_eq_simple(self):
        node = TextNode("This is a text node", TextType.BOLD)
        node2 = TextNode("This is a text node", TextType.BOLD)
        self.assertEqual(node, node2)

    def test_eq_url_none_vs_missing(self):
        node1 = TextNode("Text", TextType.TEXT)
        node2 = TextNode("Text", TextType.TEXT, None)
        self.assertEqual(node1, node2)

    def test_extract_markdown_images(self):
        # Single image
        matches = extract_markdown_images(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png)"
        )
        self.assertEqual([("image", "https://i.imgur.com/zjjcJKZ.png")], matches)

        # Multiple images
        matches = extract_markdown_images(
            "![first](https://first.com) text ![second](https://second.com)"
        )
        self.assertEqual([
            ("first", "https://first.com"),
            ("second", "https://second.com"),
        ], matches)

        # No images
        matches = extract_markdown_images("Just plain text")
        self.assertEqual([], matches)

        # Image with special characters
        matches = extract_markdown_images(
            "![special $%& chars](https://example.com/image_$%&.png)"
        )
        self.assertEqual([("special $%& chars", "https://example.com/image_$%&.png")], matches)

    def test_extract_markdown_links(self):
        # Single link
        matches = extract_markdown_links(
            "This is text with a [link](https://boot.dev)"
        )
        self.assertEqual([("link", "https://boot.dev")], matches)

        # Multiple links
        matches = extract_markdown_links(
            "[first](https://first.com) text [second](https://second.com)"
        )
        self.assertEqual([
            ("first", "https://first.com"),
            ("second", "https://second.com"),
        ], matches)

        # No links
        matches = extract_markdown_links("Just plain text")
        self.assertEqual([], matches)

        # Link with special characters
        matches = extract_markdown_links(
            "[special $%& chars](https://example.com/page_$%&)"
        )
        self.assertEqual([("special $%& chars", "https://example.com/page_$%&")], matches)

        # Should ignore images
        matches = extract_markdown_links(
            "![image](image.png) [link](url.com) ![another](img.png)"
        )
        self.assertEqual([("link", "url.com")], matches)


class TestLeafNode(unittest.TestCase):
    def test_to_html_no_tag(self):
        node = LeafNode(None, "Just raw text")
        self.assertEqual(node.to_html(), "Just raw text")

    def test_to_html_simple_tag(self):
        node = LeafNode("p", "This is a paragraph")
        self.assertEqual(node.to_html(), "<p>This is a paragraph</p>")

    def test_to_html_with_props(self):
        node = LeafNode("a", "Click me!", {"href": "https://google.com", "target": "_blank"})
        self.assertEqual(
            node.to_html(),
            '<a href="https://google.com" target="_blank">Click me!</a>'
        )

    def test_to_html_empty_value(self):
        node = LeafNode("span", "")
        self.assertEqual(node.to_html(), "<span></span>")

    def test_to_html_no_value_raises_error(self):
        with self.assertRaises(ValueError):
            node = LeafNode("p", None)
            node.to_html()

    def test_repr(self):
        node = LeafNode("div", "Hello", {"class": "container"})
        self.assertEqual(repr(node), "LeafNode('div', 'Hello', {'class': 'container'})")

    def test_props_to_html_inherited(self):
        node = LeafNode("a", "link", {"href": "#", "title": "Home"})
        self.assertEqual(node.props_to_html(), ' href="#" title="Home"')

    def test_nested_props(self):
        props = {
            "data-id": "123",
            "onclick": "alert('hello')",
            "aria-label": "Information"
        }
        node = LeafNode("button", "Info", props)
        expected = '<button data-id="123" onclick="alert(\'hello\')" aria-label="Information">Info</button>'
        self.assertEqual(node.to_html(), expected)

    def test_void_element(self):
        node = LeafNode("img", "", {"src": "image.jpg", "alt": "An image"})
        self.assertEqual(node.to_html(), '<img src="image.jpg" alt="An image">')

    def test_multiple_props_order(self):
        node1 = LeafNode("a", "link", {"a": "1", "b": "2"})
        node2 = LeafNode("a", "link", {"b": "2", "a": "1"})
        self.assertEqual(node1.to_html().count('a="1"'), 1)
        self.assertEqual(node1.to_html().count('b="2"'), 1)


class TestHTMLNode(unittest.TestCase):
    def test_props_to_html_empty(self):
        node = HTMLNode()
        self.assertEqual(node.props_to_html(), "")

    def test_props_to_html_single(self):
        node = HTMLNode(props={"class": "highlight"})
        self.assertEqual(node.props_to_html(), ' class="highlight"')

    def test_props_to_html_multiple(self):
        node = HTMLNode(props={"id": "main", "data-value": "42"})
        result = node.props_to_html()
        self.assertIn('id="main"', result)
        self.assertIn('data-value="42"', result)

    def test_repr(self):
        node = HTMLNode("div", "Hello", ["child"], {"class": "container"})
        self.assertEqual(repr(node), "HTMLNode('div', 'Hello', ['child'], {'class': 'container'})")


class TestSplitNodesDelimiter(unittest.TestCase):
    def test_split_code_delimiter(self):
        node = TextNode("This is `code` example", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        expected = [
            TextNode("This is ", TextType.TEXT),
            TextNode("code", TextType.CODE),
            TextNode(" example", TextType.TEXT),
        ]
        self.assertEqual(new_nodes, expected)

    def test_split_bold_delimiter(self):
        node = TextNode("This is **bold** text", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "**", TextType.BOLD)
        expected = [
            TextNode("This is ", TextType.TEXT),
            TextNode("bold", TextType.BOLD),
            TextNode(" text", TextType.TEXT),
        ]
        self.assertEqual(new_nodes, expected)

    def test_split_italic_delimiter(self):
        node = TextNode("This is *italic* text", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "*", TextType.ITALIC)
        expected = [
            TextNode("This is ", TextType.TEXT),
            TextNode("italic", TextType.ITALIC),
            TextNode(" text", TextType.TEXT),
        ]
        self.assertEqual(new_nodes, expected)

    def test_split_multiple_delimiters(self):
        node = TextNode("This has `code` and **bold**", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        new_nodes = split_nodes_delimiter(new_nodes, "**", TextType.BOLD)
        expected = [
            TextNode("This has ", TextType.TEXT),
            TextNode("code", TextType.CODE),
            TextNode(" and ", TextType.TEXT),
            TextNode("bold", TextType.BOLD),
        ]
        self.assertEqual(new_nodes, expected)

    def test_split_no_delimiter(self):
        node = TextNode("No delimiters here", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(new_nodes, [node])

    def test_split_unmatched_delimiter_raises_error(self):
        node = TextNode("This has `unmatched delimiter", TextType.TEXT)
        with self.assertRaises(ValueError):
            split_nodes_delimiter([node], "`", TextType.CODE)

    def test_split_empty_text(self):
        node = TextNode("", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(new_nodes, [])

    def test_split_non_text_node_passthrough(self):
        node1 = TextNode("Normal text", TextType.TEXT)
        node2 = TextNode("Already bold", TextType.BOLD)
        new_nodes = split_nodes_delimiter([node1, node2], "`", TextType.CODE)
        expected = [
            TextNode("Normal text", TextType.TEXT),
            TextNode("Already bold", TextType.BOLD),
        ]
        self.assertEqual(new_nodes, expected)

    def test_split_multiple_matches(self):
        node = TextNode("`code1` and `code2`", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        expected = [
            TextNode("code1", TextType.CODE),
            TextNode(" and ", TextType.TEXT),
            TextNode("code2", TextType.CODE),
        ]
        self.assertEqual(new_nodes, expected)

    def test_split_adjacent_delimiters(self):
        node = TextNode("**bold****bold2**", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "**", TextType.BOLD)
        expected = [
            TextNode("bold", TextType.BOLD),
            TextNode("bold2", TextType.BOLD),
        ]
        self.assertEqual(new_nodes, expected)

    def test_split_delimiter_at_start(self):
        node = TextNode("`code` at start", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        expected = [
            TextNode("code", TextType.CODE),
            TextNode(" at start", TextType.TEXT),
        ]
        self.assertEqual(new_nodes, expected)

    def test_split_delimiter_at_end(self):
        node = TextNode("Ends with `code`", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        expected = [
            TextNode("Ends with ", TextType.TEXT),
            TextNode("code", TextType.CODE),
        ]
        self.assertEqual(new_nodes, expected)


class TestSplitNodesImage(unittest.TestCase):
    def test_split_single_image(self):
        node = TextNode(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            [
                TextNode("This is text with an ", TextType.TEXT),
                TextNode("image", TextType.IMAGE, "https://i.imgur.com/zjjcJKZ.png"),
            ],
            new_nodes,
        )

    def test_split_multiple_images(self):
        node = TextNode(
            "![first](https://first.com) text ![second](https://second.com)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            [
                TextNode("first", TextType.IMAGE, "https://first.com"),
                TextNode(" text ", TextType.TEXT),
                TextNode("second", TextType.IMAGE, "https://second.com"),
            ],
            new_nodes,
        )

    def test_split_no_images(self):
        node = TextNode("Just plain text", TextType.TEXT)
        new_nodes = split_nodes_image([node])
        self.assertListEqual([node], new_nodes)

    def test_split_image_at_start(self):
        node = TextNode(
            "![start](start.png) and then some text",
            TextType.TEXT,
        )
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            [
                TextNode("start", TextType.IMAGE, "start.png"),
                TextNode(" and then some text", TextType.TEXT),
            ],
            new_nodes,
        )

    def test_split_image_at_end(self):
        node = TextNode(
            "Text before ![end](end.png)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            [
                TextNode("Text before ", TextType.TEXT),
                TextNode("end", TextType.IMAGE, "end.png"),
            ],
            new_nodes,
        )

    def test_split_adjacent_images(self):
        node = TextNode(
            "![one](one.png)![two](two.png)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            [
                TextNode("one", TextType.IMAGE, "one.png"),
                TextNode("two", TextType.IMAGE, "two.png"),
            ],
            new_nodes,
        )

    def test_split_image_with_special_chars(self):
        node = TextNode(
            "![special $%& chars](image_$%&.png)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            [
                TextNode("special $%& chars", TextType.IMAGE, "image_$%&.png"),
            ],
            new_nodes,
        )

    def test_split_non_text_node_passthrough(self):
        node1 = TextNode("Normal text", TextType.TEXT)
        node2 = TextNode("Already image", TextType.IMAGE, "url.png")
        new_nodes = split_nodes_image([node1, node2])
        expected = [
            TextNode("Normal text", TextType.TEXT),
            TextNode("Already image", TextType.IMAGE, "url.png"),
        ]
        self.assertEqual(new_nodes, expected)

    def test_split_multiple_text_nodes(self):
        node1 = TextNode("First ![one](1.png)", TextType.TEXT)
        node2 = TextNode("Second ![two](2.png)", TextType.TEXT)
        new_nodes = split_nodes_image([node1, node2])
        expected = [
            TextNode("First ", TextType.TEXT),
            TextNode("one", TextType.IMAGE, "1.png"),
            TextNode("Second ", TextType.TEXT),
            TextNode("two", TextType.IMAGE, "2.png"),
        ]
        self.assertEqual(new_nodes, expected)

    def test_split_empty_text(self):
        node = TextNode("", TextType.TEXT)
        new_nodes = split_nodes_image([node])
        self.assertEqual(new_nodes, [])


class TestSplitNodesLink(unittest.TestCase):
    def test_split_single_link(self):
        node = TextNode(
            "This is text with a [link](https://boot.dev)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_link([node])
        self.assertListEqual(
            [
                TextNode("This is text with a ", TextType.TEXT),
                TextNode("link", TextType.LINK, "https://boot.dev"),
            ],
            new_nodes,
        )

    def test_split_multiple_links(self):
        node = TextNode(
            "[first](https://first.com) text [second](https://second.com)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_link([node])
        self.assertListEqual(
            [
                TextNode("first", TextType.LINK, "https://first.com"),
                TextNode(" text ", TextType.TEXT),
                TextNode("second", TextType.LINK, "https://second.com"),
            ],
            new_nodes,
        )

    def test_split_no_links(self):
        node = TextNode("Just plain text", TextType.TEXT)
        new_nodes = split_nodes_link([node])
        self.assertListEqual([node], new_nodes)

    def test_split_link_at_start(self):
        node = TextNode(
            "[start](start.com) and then some text",
            TextType.TEXT,
        )
        new_nodes = split_nodes_link([node])
        self.assertListEqual(
            [
                TextNode("start", TextType.LINK, "start.com"),
                TextNode(" and then some text", TextType.TEXT),
            ],
            new_nodes,
        )

    def test_split_link_at_end(self):
        node = TextNode(
            "Text before [end](end.com)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_link([node])
        self.assertListEqual(
            [
                TextNode("Text before ", TextType.TEXT),
                TextNode("end", TextType.LINK, "end.com"),
            ],
            new_nodes,
        )

    def test_split_adjacent_links(self):
        node = TextNode(
            "[one](one.com)[two](two.com)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_link([node])
        self.assertListEqual(
            [
                TextNode("one", TextType.LINK, "one.com"),
                TextNode("two", TextType.LINK, "two.com"),
            ],
            new_nodes,
        )

    def test_split_link_with_special_chars(self):
        node = TextNode(
            "[special $%& chars](page_$%&.html)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_link([node])
        self.assertListEqual(
            [
                TextNode("special $%& chars", TextType.LINK, "page_$%&.html"),
            ],
            new_nodes,
        )

    def test_split_ignore_images(self):
        node = TextNode(
            "![image](image.png) [link](link.com)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_link([node])
        self.assertListEqual(
            [
                TextNode("![image](image.png) ", TextType.TEXT),
                TextNode("link", TextType.LINK, "link.com"),
            ],
            new_nodes,
        )

    def test_split_non_text_node_passthrough(self):
        node1 = TextNode("Normal text", TextType.TEXT)
        node2 = TextNode("Already link", TextType.LINK, "url.com")
        new_nodes = split_nodes_link([node1, node2])
        expected = [
            TextNode("Normal text", TextType.TEXT),
            TextNode("Already link", TextType.LINK, "url.com"),
        ]
        self.assertEqual(new_nodes, expected)

    def test_split_multiple_text_nodes(self):
        node1 = TextNode("First [one](1.com)", TextType.TEXT)
        node2 = TextNode("Second [two](2.com)", TextType.TEXT)
        new_nodes = split_nodes_link([node1, node2])
        expected = [
            TextNode("First ", TextType.TEXT),
            TextNode("one", TextType.LINK, "1.com"),
            TextNode("Second ", TextType.TEXT),
            TextNode("two", TextType.LINK, "2.com"),
        ]
        self.assertEqual(new_nodes, expected)

    def test_split_empty_text(self):
        node = TextNode("", TextType.TEXT)
        new_nodes = split_nodes_link([node])
        self.assertEqual(new_nodes, [])


class TestTextToTextNodes(unittest.TestCase):
    def test_text_to_textnodes_basic(self):
        text = "This is **bold** and *italic* text"
        nodes = text_to_textnodes(text)
        expected = [
            TextNode("This is ", TextType.TEXT),
            TextNode("bold", TextType.BOLD),
            TextNode(" and ", TextType.TEXT),
            TextNode("italic", TextType.ITALIC),
            TextNode(" text", TextType.TEXT),
        ]
        self.assertEqual(nodes, expected)

    def test_text_to_textnodes_with_all_types(self):
        text = "This is **bold**, *italic*, `code`, ![image](img.png), and [link](url.com)"
        nodes = text_to_textnodes(text)
        expected = [
            TextNode("This is ", TextType.TEXT),
            TextNode("bold", TextType.BOLD),
            TextNode(", ", TextType.TEXT),
            TextNode("italic", TextType.ITALIC),
            TextNode(", ", TextType.TEXT),
            TextNode("code", TextType.CODE),
            TextNode(", ", TextType.TEXT),
            TextNode("image", TextType.IMAGE, "img.png"),
            TextNode(", and ", TextType.TEXT),
            TextNode("link", TextType.LINK, "url.com"),
        ]
        self.assertEqual(nodes, expected)

    def test_text_to_textnodes_multiple_bold(self):
        text = "**First** and **Second** bold words"
        nodes = text_to_textnodes(text)
        expected = [
            TextNode("First", TextType.BOLD),
            TextNode(" and ", TextType.TEXT),
            TextNode("Second", TextType.BOLD),
            TextNode(" bold words", TextType.TEXT),
        ]
        self.assertEqual(nodes, expected)

    def test_text_to_textnodes_nested_formatting(self):
        text = "Text with **bold *and* italic** inside"
        nodes = text_to_textnodes(text)
        expected = [
            TextNode("Text with ", TextType.TEXT),
            TextNode("bold *and* italic", TextType.BOLD),
            TextNode(" inside", TextType.TEXT),
        ]
        self.assertEqual(nodes, expected)

    def test_text_to_textnodes_empty(self):
        text = ""
        nodes = text_to_textnodes(text)
        self.assertEqual(nodes, [])

    def test_text_to_textnodes_only_bold(self):
        text = "**only bold**"
        nodes = text_to_textnodes(text)
        expected = [TextNode("only bold", TextType.BOLD)]
        self.assertEqual(nodes, expected)

    def test_text_to_textnodes_only_image(self):
        text = "![only image](img.png)"
        nodes = text_to_textnodes(text)
        expected = [TextNode("only image", TextType.IMAGE, "img.png")]
        self.assertEqual(nodes, expected)

    def test_text_to_textnodes_adjacent_formats(self):
        text = "**bold**_italic_`code`"
        nodes = text_to_textnodes(text)
        expected = [
            TextNode("bold", TextType.BOLD),
            TextNode("italic", TextType.ITALIC),
            TextNode("code", TextType.CODE),
        ]
        self.assertEqual(nodes, expected)

    def test_text_to_textnodes_complex_combination(self):
        text = "Hello **world**, this is `code` and ![image](img.png) with [link](url.com) and _italic_."
        nodes = text_to_textnodes(text)
        expected = [
            TextNode("Hello ", TextType.TEXT),
            TextNode("world", TextType.BOLD),
            TextNode(", this is ", TextType.TEXT),
            TextNode("code", TextType.CODE),
            TextNode(" and ", TextType.TEXT),
            TextNode("image", TextType.IMAGE, "img.png"),
            TextNode(" with ", TextType.TEXT),
            TextNode("link", TextType.LINK, "url.com"),
            TextNode(" and ", TextType.TEXT),
            TextNode("italic", TextType.ITALIC),
            TextNode(".", TextType.TEXT),
        ]
        self.assertEqual(nodes, expected)

    def test_text_to_textnodes_underscore_italic(self):
        text = "This _should_ be italic"
        nodes = text_to_textnodes(text)
        expected = [
            TextNode("This ", TextType.TEXT),
            TextNode("should", TextType.ITALIC),
            TextNode(" be italic", TextType.TEXT),
        ]
        self.assertEqual(nodes, expected)

    def test_text_to_textnodes_mixed_italic_syntax(self):
        text = "*star* and _underscore_ italic"
        nodes = text_to_textnodes(text)
        expected = [
            TextNode("star", TextType.ITALIC),
            TextNode(" and ", TextType.TEXT),
            TextNode("underscore", TextType.ITALIC),
            TextNode(" italic", TextType.TEXT),
        ]
        self.assertEqual(nodes, expected)

    def test_text_to_textnodes_image_before_link(self):
        text = "![first](img.png) and [second](url.com)"
        nodes = text_to_textnodes(text)
        expected = [
            TextNode("first", TextType.IMAGE, "img.png"),
            TextNode(" and ", TextType.TEXT),
            TextNode("second", TextType.LINK, "url.com"),
        ]
        self.assertEqual(nodes, expected)

    def test_text_to_textnodes_special_chars(self):
        text = "**bold $%&** and `code $%&` with ![image $%&](img_$%&.png)"
        nodes = text_to_textnodes(text)
        expected = [
            TextNode("bold $%&", TextType.BOLD),
            TextNode(" and ", TextType.TEXT),
            TextNode("code $%&", TextType.CODE),
            TextNode(" with ", TextType.TEXT),
            TextNode("image $%&", TextType.IMAGE, "img_$%&.png"),
        ]
        self.assertEqual(nodes, expected)


class TestMarkdownToBlocks(unittest.TestCase):
    def test_basic_case(self):
        markdown = """# This is a heading

This is a paragraph of text. It has some **bold** and _italic_ words inside of it.

- This is the first list item in a list block
- This is a list item
- This is another list item"""
        blocks = markdown_to_blocks(markdown)
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0], "# This is a heading")
        self.assertEqual(blocks[1], "This is a paragraph of text. It has some **bold** and _italic_ words inside of it.")
        self.assertEqual(blocks[2], "- This is the first list item in a list block\n- This is a list item\n- This is another list item")

    def test_multiple_newlines(self):
        markdown = """First block


Second block


Third block"""
        blocks = markdown_to_blocks(markdown)
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0], "First block")
        self.assertEqual(blocks[1], "Second block")
        self.assertEqual(blocks[2], "Third block")

    def test_leading_and_trailing_newlines(self):
        markdown = """


First block


Second block


Third block


"""
        blocks = markdown_to_blocks(markdown)
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0], "First block")
        self.assertEqual(blocks[1], "Second block")
        self.assertEqual(blocks[2], "Third block")

    def test_single_block(self):
        markdown = "Just a single block of text"
        blocks = markdown_to_blocks(markdown)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0], "Just a single block of text")

    def test_empty_string(self):
        markdown = ""
        blocks = markdown_to_blocks(markdown)
        self.assertEqual(len(blocks), 0)

    def test_whitespace_only(self):
        markdown = "   \n\n   \n\t\n   "
        blocks = markdown_to_blocks(markdown)
        self.assertEqual(len(blocks), 0)

    def test_mixed_whitespace(self):
        markdown = "   First block   \n\n  Second block \t\n\nThird block   "
        blocks = markdown_to_blocks(markdown)
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0], "First block")
        self.assertEqual(blocks[1], "Second block")
        self.assertEqual(blocks[2], "Third block")

    def test_blocks_with_internal_newlines(self):
        markdown = """Block with\ninternal newlines

Another block\nwith\nmultiple\nlines"""
        blocks = markdown_to_blocks(markdown)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0], "Block with\ninternal newlines")
        self.assertEqual(blocks[1], "Another block\nwith\nmultiple\nlines")

    def test_code_block_preservation(self):
        markdown = "```python\ndef function():\n    return 42\n```\n\nRegular text block\n\n```\ncode block\n```"
        blocks = markdown_to_blocks(markdown)
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0], "```python\ndef function():\n    return 42\n```")
        self.assertEqual(blocks[1], "Regular text block")
        self.assertEqual(blocks[2], "```\ncode block\n```")


class TestBlockToBlockType(unittest.TestCase):
    def test_heading(self):
        # Test all heading levels
        for i in range(1, 7):
            block = f"{'#' * i} Heading level {i}"
            self.assertEqual(block_to_block_type(block), BlockType.HEADING)
        
        # Not headings (missing space after #)
        self.assertNotEqual(block_to_block_type("##No space"), BlockType.HEADING)
        self.assertNotEqual(block_to_block_type("#Heading"), BlockType.HEADING)
        
        # Too many # (7+)
        self.assertNotEqual(block_to_block_type("####### Too many"), BlockType.HEADING)

    def test_code(self):
        # Single line code block
        block = "```code```"
        self.assertEqual(block_to_block_type(block), BlockType.CODE)
        
        # Multi-line code block
        block = "```\nmulti\nline\ncode\n```"
        self.assertEqual(block_to_block_type(block), BlockType.CODE)
        
        # Not code blocks
        self.assertNotEqual(block_to_block_type("``not enough ticks``"), BlockType.CODE)
        self.assertNotEqual(block_to_block_type("```unmatched"), BlockType.CODE)
        self.assertNotEqual(block_to_block_type("unmatched```"), BlockType.CODE)
        self.assertNotEqual(block_to_block_type("``````"), BlockType.CODE)  # Empty code block
        self.assertNotEqual(block_to_block_type("```"), BlockType.CODE)    # Single ```

    def test_quote(self):
        # Single line quote
        block = "> This is a quote"
        self.assertEqual(block_to_block_type(block), BlockType.QUOTE)
        
        # Multi-line quote
        block = "> Line 1\n> Line 2\n> Line 3"
        self.assertEqual(block_to_block_type(block), BlockType.QUOTE)
        
        # Not quotes
        self.assertNotEqual(block_to_block_type(">Missing angle bracket on\nthis line"), BlockType.QUOTE)
        self.assertNotEqual(block_to_block_type("Not a quote"), BlockType.QUOTE)

    def test_unordered_list(self):
        # Single item list
        block = "- Item 1"
        self.assertEqual(block_to_block_type(block), BlockType.UNORDERED_LIST)
        
        # Multi-item list
        block = "- Item 1\n- Item 2\n- Item 3"
        self.assertEqual(block_to_block_type(block), BlockType.UNORDERED_LIST)
        
        # Not unordered lists
        self.assertNotEqual(block_to_block_type("-Missing space"), BlockType.UNORDERED_LIST)
        self.assertNotEqual(block_to_block_type("Not a list"), BlockType.UNORDERED_LIST)
        self.assertNotEqual(block_to_block_type("* Different bullet"), BlockType.UNORDERED_LIST)

    def test_ordered_list(self):
        # Single item list
        block = "1. First item"
        self.assertEqual(block_to_block_type(block), BlockType.ORDERED_LIST)
        
        # Multi-item list
        block = "1. Item 1\n2. Item 2\n3. Item 3"
        self.assertEqual(block_to_block_type(block), BlockType.ORDERED_LIST)
        
        # Not ordered lists
        self.assertNotEqual(block_to_block_type("1. Item 1\n3. Item 2"), BlockType.ORDERED_LIST)  # Wrong numbering
        self.assertNotEqual(block_to_block_type("1. Item 1\n2.Item 2"), BlockType.ORDERED_LIST)  # Missing space after .
        self.assertNotEqual(block_to_block_type("1.Item 1"), BlockType.ORDERED_LIST)  # Missing space after .
        self.assertNotEqual(block_to_block_type("A. Not numbered"), BlockType.ORDERED_LIST)
        self.assertNotEqual(block_to_block_type("Not a list"), BlockType.ORDERED_LIST)

    def test_paragraph(self):
        # Regular paragraphs
        self.assertEqual(block_to_block_type("Just regular text"), BlockType.PARAGRAPH)
        self.assertEqual(block_to_block_type("Text with **markdown** but no block type"), BlockType.PARAGRAPH)
        self.assertEqual(block_to_block_type("Multiple\nlines\nof text"), BlockType.PARAGRAPH)
        
        # Failed block type attempts
        self.assertEqual(block_to_block_type("#Not a heading"), BlockType.PARAGRAPH)
        self.assertEqual(block_to_block_type(">Partial quote\nNot quote"), BlockType.PARAGRAPH)
        self.assertEqual(block_to_block_type("-Missing space"), BlockType.PARAGRAPH)
        self.assertEqual(block_to_block_type("1.Missing space"), BlockType.PARAGRAPH)

    def test_edge_cases(self):
        # Empty block (shouldn't happen due to markdown_to_blocks)
        self.assertEqual(block_to_block_type(""), BlockType.PARAGRAPH)
        
        # Whitespace only (shouldn't happen due to markdown_to_blocks)
        self.assertEqual(block_to_block_type("   \n  \t"), BlockType.PARAGRAPH)
        
        # Mixed content that doesn't match any block type
        mixed_block = "> Some quote\nBut not all lines are quotes"
        self.assertEqual(block_to_block_type(mixed_block), BlockType.PARAGRAPH)
        
        # Almost ordered list but wrong numbering
        almost_ordered = "1. First\n3. Third\n2. Second"
        self.assertEqual(block_to_block_type(almost_ordered), BlockType.PARAGRAPH)

    def test_code_block_with_language(self):
        block = "```python\nprint('Hello')\n```"
        self.assertEqual(block_to_block_type(block), BlockType.CODE)

    def test_nested_ordered_list(self):
        block = "1. First\n2. Second\n    1. Nested\n    2. Also nested\n3. Third"
        # This should fail as nested lists aren't supported in basic markdown
        self.assertEqual(block_to_block_type(block), BlockType.PARAGRAPH)

    def test_complex_quote(self):
        block = "> Quote line 1\n> > Nested quote\n> Quote line 2"
        # We only check that all lines start with >
        self.assertEqual(block_to_block_type(block), BlockType.QUOTE)


class TestMarkdownToHTMLNode(unittest.TestCase):
    def test_text_to_children_basic(self):
        text = "This is **bold** and *italic*"
        nodes = text_to_children(text)
        expected = [
            LeafNode(None, "This is "),
            LeafNode("b", "bold"),
            LeafNode(None, " and "),
            LeafNode("i", "italic"),
        ]
        self.assertEqual(len(nodes), len(expected))
        for node, exp in zip(nodes, expected):
            self.assertEqual(node.to_html(), exp.to_html())

    def test_text_to_children_with_image_and_link(self):
        text = "See ![image](img.png) and [link](url.com)"
        nodes = text_to_children(text)
        expected = [
            LeafNode(None, "See "),
            LeafNode("img", "", {"src": "img.png", "alt": "image"}),
            LeafNode(None, " and "),
            LeafNode("a", "link", {"href": "url.com"}),
        ]
        self.assertEqual(len(nodes), len(expected))
        for node, exp in zip(nodes, expected):
            self.assertEqual(node.to_html(), exp.to_html())

    def test_text_to_children_empty(self):
        text = ""
        nodes = text_to_children(text)
        self.assertEqual(nodes, [])

    def test_heading_block_to_html(self):
        block = "## Heading **bold**"
        node = heading_block_to_html(block)
        expected = ParentNode("h2", [
            LeafNode(None, "Heading "),
            LeafNode("b", "bold"),
        ])
        self.assertEqual(node.to_html(), expected.to_html())

    def test_heading_block_to_html_invalid(self):
        block = "##Invalid"
        with self.assertRaises(ValueError):
            heading_block_to_html(block)

    def test_paragraph_block_to_html(self):
        block = "This is a **bold** paragraph"
        node = paragraph_block_to_html(block)
        expected = ParentNode("p", [
            LeafNode(None, "This is a "),
            LeafNode("b", "bold"),
            LeafNode(None, " paragraph"),
        ])
        self.assertEqual(node.to_html(), expected.to_html())

    def test_paragraph_block_to_html_empty(self):
        block = ""
        node = paragraph_block_to_html(block)
        expected = ParentNode("p", [LeafNode(None, "")])
        self.assertEqual(node.to_html(), expected.to_html())

    def test_code_block_to_html(self):
        block = "```python\nprint('Hello')\n```"
        node = code_block_to_html(block)
        expected = ParentNode("pre", [
            ParentNode("code", [LeafNode(None, "print('Hello')")])
        ])
        self.assertEqual(node.to_html(), expected.to_html())

    def test_code_block_to_html_single_line(self):
        block = "```code```"
        node = code_block_to_html(block)
        expected = ParentNode("pre", [
            ParentNode("code", [LeafNode(None, "code")])
        ])
        self.assertEqual(node.to_html(), expected.to_html())

    def test_quote_block_to_html(self):
        block = "> This is a *quote*"
        node = quote_block_to_html(block)
        expected = ParentNode("blockquote", [
            LeafNode(None, "This is a "),
            LeafNode("i", "quote"),
        ])
        self.assertEqual(node.to_html(), expected.to_html())

    def test_quote_block_to_html_multiline(self):
        block = "> Line 1\n> Line **2**"
        node = quote_block_to_html(block)
        expected = ParentNode("blockquote", [
            LeafNode(None, "Line 1\nLine "),
            LeafNode("b", "2"),
        ])
        self.assertEqual(node.to_html(), expected.to_html())

    def test_unordered_list_block_to_html(self):
        block = "- Item 1\n- Item **2**"
        node = unordered_list_block_to_html(block)
        expected = ParentNode("ul", [
            ParentNode("li", [LeafNode(None, "Item 1")]),
            ParentNode("li", [LeafNode(None, "Item "), LeafNode("b", "2")]),
        ])
        self.assertEqual(node.to_html(), expected.to_html())

    def test_unordered_list_block_to_html_single_item(self):
        block = "- Single item"
        node = unordered_list_block_to_html(block)
        expected = ParentNode("ul", [
            ParentNode("li", [LeafNode(None, "Single item")]),
        ])
        self.assertEqual(node.to_html(), expected.to_html())

    def test_ordered_list_block_to_html(self):
        block = "1. Item 1\n2. Item **2**"
        node = ordered_list_block_to_html(block)
        expected = ParentNode("ol", [
            ParentNode("li", [LeafNode(None, "Item 1")]),
            ParentNode("li", [LeafNode(None, "Item "), LeafNode("b", "2")]),
        ])
        self.assertEqual(node.to_html(), expected.to_html())

    def test_ordered_list_block_to_html_single_item(self):
        block = "1. Single item"
        node = ordered_list_block_to_html(block)
        expected = ParentNode("ol", [
            ParentNode("li", [LeafNode(None, "Single item")]),
        ])
        self.assertEqual(node.to_html(), expected.to_html())

    def test_strip_block_prefix(self):
        # Heading
        self.assertEqual(strip_block_prefix("## Heading", BlockType.HEADING), "Heading")
        # Quote
        self.assertEqual(strip_block_prefix("> Line 1\n> Line 2", BlockType.QUOTE), "Line 1\nLine 2")
        # Unordered list
        self.assertEqual(strip_block_prefix("- Item 1\n- Item 2", BlockType.UNORDERED_LIST), "Item 1\nItem 2")
        # Ordered list
        self.assertEqual(strip_block_prefix("1. Item 1\n2. Item 2", BlockType.ORDERED_LIST), "Item 1\nItem 2")
        # Code
        self.assertEqual(strip_block_prefix("```python\ncode\n```", BlockType.CODE), "code")
        # Paragraph
        self.assertEqual(strip_block_prefix("Plain text", BlockType.PARAGRAPH), "Plain text")

    def test_markdown_to_html_node_basic(self):
        markdown = """# Heading

Paragraph with **bold** text.

> Quote *italic*

- List item 1
- List item 2

```code
```
"""
        node = markdown_to_html_node(markdown)
        expected = ParentNode("div", [
            ParentNode("h1", [LeafNode(None, "Heading")]),
            ParentNode("p", [LeafNode(None, "Paragraph with "), LeafNode("b", "bold"), LeafNode(None, " text.")]),
            ParentNode("blockquote", [LeafNode(None, "Quote "), LeafNode("i", "italic")]),
            ParentNode("ul", [
                ParentNode("li", [LeafNode(None, "List item 1")]),
                ParentNode("li", [LeafNode(None, "List item 2")]),
            ]),
            ParentNode("pre", [ParentNode("code", [LeafNode(None, "code")])]),
        ])
        self.assertEqual(node.to_html(), expected.to_html())

    def test_markdown_to_html_node_complex(self):
        markdown = """## Subheading

This is a paragraph with [link](url.com) and ![image](img.png).

> **Bold quote**

1. Ordered **item**
2. Second item

```python
print("Hello")
```
"""
        node = markdown_to_html_node(markdown)
        expected = ParentNode("div", [
            ParentNode("h2", [LeafNode(None, "Subheading")]),
            ParentNode("p", [
                LeafNode(None, "This is a paragraph with "),
                LeafNode("a", "link", {"href": "url.com"}),
                LeafNode(None, " and "),
                LeafNode("img", "", {"src": "img.png", "alt": "image"}),
                LeafNode(None, "."),
            ]),
            ParentNode("blockquote", [LeafNode("b", "Bold quote")]),
            ParentNode("ol", [
                ParentNode("li", [LeafNode(None, "Ordered "), LeafNode("b", "item")]),
                ParentNode("li", [LeafNode(None, "Second item")]),
            ]),
            ParentNode("pre", [ParentNode("code", [LeafNode(None, "print(\"Hello\")")])]),
        ])
        self.assertEqual(node.to_html(), expected.to_html())

    def test_markdown_to_html_node_empty(self):
        markdown = ""
        node = markdown_to_html_node(markdown)
        expected = ParentNode("div", [LeafNode(None, "")])
        self.assertEqual(node.to_html(), expected.to_html())

    def test_markdown_to_html_node_whitespace(self):
        markdown = "   \n\n   \n\t\n   "
        node = markdown_to_html_node(markdown)
        expected = ParentNode("div", [LeafNode(None, "")])
        self.assertEqual(node.to_html(), expected.to_html())


class TestExtractTitle(unittest.TestCase):
    def test_extract_title_basic(self):
        markdown = "# Hello"
        title = extract_title(markdown)
        self.assertEqual(title, "Hello")

    def test_extract_title_with_whitespace(self):
        markdown = "#   My Title  "
        title = extract_title(markdown)
        self.assertEqual(title, "My Title")

    def test_extract_title_in_multiblock(self):
        markdown = """Paragraph
# Main Title
More content"""
        title = extract_title(markdown)
        self.assertEqual(title, "Main Title")

    def test_extract_title_first_h1(self):
        markdown = """# First Title
# Second Title
Content"""
        title = extract_title(markdown)
        self.assertEqual(title, "First Title")

    def test_extract_title_no_h1_raises_error(self):
        markdown = "## Subheading\nContent"
        with self.assertRaises(ValueError) as cm:
            extract_title(markdown)
        self.assertEqual(str(cm.exception), "No h1 header found in Markdown")

    def test_extract_title_empty_markdown(self):
        markdown = ""
        with self.assertRaises(ValueError) as cm:
            extract_title(markdown)
        self.assertEqual(str(cm.exception), "No h1 header found in Markdown")

    def test_extract_title_only_whitespace(self):
        markdown = "   \n\n   "
        with self.assertRaises(ValueError) as cm:
            extract_title(markdown)
        self.assertEqual(str(cm.exception), "No h1 header found in Markdown")

    def test_extract_title_no_heading(self):
        markdown = "Just a paragraph\n- List item"
        with self.assertRaises(ValueError) as cm:
            extract_title(markdown)
        self.assertEqual(str(cm.exception), "No h1 header found in Markdown")

    def test_extract_title_h1_with_formatting(self):
        markdown = "# **Bold** Title"
        title = extract_title(markdown)
        self.assertEqual(title, "**Bold** Title")


if __name__ == "__main__":
    unittest.main()