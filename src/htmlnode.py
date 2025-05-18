class HTMLNode:
    def __init__(self, tag=None, value=None, children=None, props=None):
        self.tag = tag
        self.value = value
        self.children = children
        self.props = props

    def to_html(self):
        raise NotImplementedError("to_html method not implemented")

    def props_to_html(self):
        if not self.props:
            return ""
        return " " + " ".join(f'{key}="{value}"' for key, value in self.props.items())

    def __repr__(self):
        return f"HTMLNode({repr(self.tag)}, {repr(self.value)}, {repr(self.children)}, {repr(self.props)})"


class LeafNode(HTMLNode):
    # List of void elements that shouldn't have closing tags
    VOID_ELEMENTS = {
        "area", "base", "br", "col", "embed", 
        "hr", "img", "input", "link", "meta", 
        "param", "source", "track", "wbr"
    }

    def __init__(self, tag, value, props=None):
        if value is None and tag not in self.VOID_ELEMENTS:
            raise ValueError("LeafNode requires a value for non-void elements")
        super().__init__(tag=tag, value=value, children=None, props=props)

    def to_html(self):
        if self.value is None and self.tag not in self.VOID_ELEMENTS:
            raise ValueError("LeafNode requires a value for non-void elements")
        
        if not self.tag:
            return self.value if self.value is not None else ""
            
        props_html = self.props_to_html()
        
        if self.tag in self.VOID_ELEMENTS:
            return f"<{self.tag}{props_html}>"
        return f"<{self.tag}{props_html}>{self.value}</{self.tag}>"

    def __repr__(self):
        return f"LeafNode({repr(self.tag)}, {repr(self.value)}, {repr(self.props)})"

class ParentNode(HTMLNode):
    def __init__(self, tag, children, props=None):
        if tag is None:
            raise ValueError("ParentNode requires a tag")
        if children is None or len(children) == 0:  # Added check for empty list
            raise ValueError("ParentNode requires children")
        super().__init__(tag=tag, value=None, children=children, props=props)

    def to_html(self):
        if self.tag is None:
            raise ValueError("ParentNode requires a tag")
        if self.children is None or len(self.children) == 0:  # Added check for empty list
            raise ValueError("ParentNode has no children")
        
        props_html = self.props_to_html()
        children_html = ""
        for child in self.children:
            children_html += child.to_html()
        
        return f"<{self.tag}{props_html}>{children_html}</{self.tag}>"

