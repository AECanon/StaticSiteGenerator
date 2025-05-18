import os
import shutil
import sys
from textnode import extract_title, markdown_to_html_node

def clear_and_copy_directory(src, dst):
    """
    Delete all contents in dst and copy src to dst.
    """
    if os.path.exists(dst):
        shutil.rmtree(dst)
    if os.path.exists(src):
        shutil.copytree(src, dst)
    else:
        print(f"Warning: {src} directory not found, creating empty {dst}")
        os.makedirs(dst, exist_ok=True)

def generate_page(from_path, template_path, dest_path, basepath):
    """
    Generate an HTML page from a Markdown file using a template.
    
    Args:
        from_path (str): Path to the input Markdown file.
        template_path (str): Path to the HTML template file.
        dest_path (str): Path to the output HTML file.
        basepath (str): Base path for URLs (e.g., '/' or '/mysite/').
    """
    print(f"Generating page from {from_path} to {dest_path} using {template_path}")
    
    # Read Markdown file
    with open(from_path, 'r', encoding='utf-8') as f:
        markdown = f.read()
    
    # Read template file
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Convert Markdown to HTML
    html_content = markdown_to_html_node(markdown).to_html()
    
    # Extract title
    title = extract_title(markdown)
    
    # Replace placeholders in template
    final_html = template.replace('{{ Title }}', title).replace('{{ Content }}', html_content)
    
    # Replace href and src with basepath
    final_html = final_html.replace('href="/', f'href="{basepath}')
    final_html = final_html.replace('src="/', f'src="{basepath}')
    
    # Create destination directory if it doesn't exist
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    # Write HTML to destination
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(final_html)

def generate_pages_recursive(dir_path_content, template_path, dest_dir_path, basepath):
    """
    Recursively generate HTML pages for all Markdown files in dir_path_content.
    
    Args:
        dir_path_content (str): Path to the content directory (e.g., 'content').
        template_path (str): Path to the HTML template file (e.g., 'template.html').
        dest_dir_path (str): Path to the output directory (e.g., 'docs').
        basepath (str): Base path for URLs (e.g., '/' or '/mysite/').
    """
    if not os.path.exists(dir_path_content):
        print(f"Warning: Content directory {dir_path_content} not found")
        return
    if not os.path.exists(template_path):
        print(f"Warning: Template file {template_path} not found")
        return

    for root, _, files in os.walk(dir_path_content):
        for filename in files:
            if filename.endswith('.md'):
                # Input Markdown path (e.g., content/blog/glorfindel/index.md)
                from_path = os.path.join(root, filename)
                # Relative path (e.g., blog/glorfindel/index.md)
                relative_path = os.path.relpath(from_path, dir_path_content)
                # Output HTML path (e.g., docs/blog/glorfindel/index.html)
                dest_path = os.path.join(dest_dir_path, os.path.splitext(relative_path)[0] + '.html')
                generate_page(from_path, template_path, dest_path, basepath)

def main():
    # Get basepath from CLI argument, default to '/'
    basepath = sys.argv[1] if len(sys.argv) > 1 else '/'
    
    # Ensure basepath ends with '/'
    if not basepath.endswith('/'):
        basepath += '/'
    
    # Clear docs/ and copy static/
    clear_and_copy_directory('static', 'docs')
    
    # Generate pages for all Markdown files in content/
    generate_pages_recursive('content', 'template.html', 'docs', basepath)

if __name__ == "__main__":
    main()