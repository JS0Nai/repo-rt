# src_mapper/generators/html_generator.py

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..utils import read_file_content

def _build_html_content_tree(file_info_list: List[Dict[str, Any]], repo_root_path: Path, config_module) -> Dict[str, Any]:
    """
    Builds a nested dictionary representing the file tree with content.
    File nodes contain actual content or placeholders for binary/error files.
    """
    content_tree = {}
    
    for file_info in file_info_list:
        relative_path_parts = file_info['relative_path_posix'].split('/')
        
        # Navigate to the right spot in the tree
        current_level = content_tree
        for i, part in enumerate(relative_path_parts[:-1]):  # All parts except the filename
            if part not in current_level:
                current_level[part] = {}  # Create directory node if it doesn't exist
            current_level = current_level[part]
        
        # Handle the file (last part)
        filename = relative_path_parts[-1]
        
        # Try to read the file content
        content, is_binary, error_msg = read_file_content(
            file_info['absolute_path'],
            config_module.ENCODINGS_TO_TRY
        )
        
        # Store appropriate content in the tree
        if is_binary:
            content_display = f"[Binary File: {error_msg or 'Cannot display content'}]"
        elif content is None:
            content_display = f"[Error: {error_msg or 'Unknown error reading file'}]"
        else:
            content_display = content
        
        current_level[filename] = content_display
    
    return content_tree

def _determine_language_class(file_path: str) -> str:
    """
    Determines the language class for syntax highlighting based on file extension.
    Returns empty string if no specific language is matched.
    """
    # Extract extension
    _, ext = os.path.splitext(file_path.lower())
    if not ext:
        return ""
    
    # Common language mappings for syntax highlighting
    language_map = {
        # Programming languages
        '.py': 'language-python',
        '.js': 'language-javascript',
        '.jsx': 'language-jsx',
        '.ts': 'language-typescript',
        '.tsx': 'language-tsx',
        '.html': 'language-html',
        '.css': 'language-css',
        '.scss': 'language-scss',
        '.sass': 'language-sass',
        '.java': 'language-java',
        '.c': 'language-c',
        '.cpp': 'language-cpp',
        '.h': 'language-c',
        '.hpp': 'language-cpp',
        '.cs': 'language-csharp',
        '.go': 'language-go',
        '.rs': 'language-rust',
        '.rb': 'language-ruby',
        '.php': 'language-php',
        '.swift': 'language-swift',
        '.kt': 'language-kotlin',
        '.scala': 'language-scala',
        '.dart': 'language-dart',
        '.elm': 'language-elm',
        '.erl': 'language-erlang',
        '.ex': 'language-elixir',
        '.exs': 'language-elixir',
        '.hs': 'language-haskell',
        '.lua': 'language-lua',
        '.pl': 'language-perl',
        '.r': 'language-r',
        '.sql': 'language-sql',
        
        # Markup & config
        '.xml': 'language-xml',
        '.json': 'language-json',
        '.md': 'language-markdown',
        '.yml': 'language-yaml',
        '.yaml': 'language-yaml',
        '.toml': 'language-toml',
        '.ini': 'language-ini',
        '.cfg': 'language-ini',
        '.conf': 'language-ini',
        '.sh': 'language-bash',
        '.bash': 'language-bash',
        '.zsh': 'language-bash',
        '.ps1': 'language-powershell',
        '.dockerfile': 'language-dockerfile',
        '.graphql': 'language-graphql',
        '.proto': 'language-protobuf',
    }
    
    return language_map.get(ext, '')

def _generate_html_fragment_recursive(tree_level_data: Dict[str, Any], current_path_parts: Optional[List[str]] = None) -> str:
    """
    Recursively generates HTML fragments for the tree structure.
    Uses <details> for directories and <pre><code> for file content.
    """
    if current_path_parts is None:
        current_path_parts = []
    
    # Sort items: directories first, then files, both alphabetically
    sorted_items = sorted(
        tree_level_data.items(),
        key=lambda x: (not isinstance(x[1], dict), x[0].lower())
    )
    
    html_parts = []
    
    for name, content_or_dir in sorted_items:
        is_directory = isinstance(content_or_dir, dict)
        current_full_path = '/'.join(current_path_parts + [name])
        
        if is_directory:
            # It's a directory
            html_parts.append(f'<details><summary class="dir-name">{name}/</summary>')
            # Recursively process subdirectory, building upon the path parts
            html_parts.append(_generate_html_fragment_recursive(
                content_or_dir, 
                current_path_parts + [name]
            ))
            html_parts.append('</details>')
        else:
            # It's a file
            language_class = _determine_language_class(name)
            
            # Use JavaScript .toLowerCase() for case-insensitive comparison
            is_binary_or_error = (
                isinstance(content_or_dir, str) and 
                (content_or_dir.startswith('[Binary File:') or 
                 content_or_dir.startswith('[Error:'))
            )
            
            html_parts.append(f'<details><summary class="file-name">{name}</summary>')
            
            # Add "Copy" button for text files
            if not is_binary_or_error:
                html_parts.append('<button class="copy-button" onclick="copyToClipboard(this)">Copy</button>')
            
            # Handle content display with appropriate language class for highlighting
            pre_class = "binary-content" if is_binary_or_error else ""
            if language_class and not is_binary_or_error:
                html_parts.append(f'<pre class="{pre_class}"><code class="{language_class}">{_escape_html(content_or_dir)}</code></pre>')
            else:
                html_parts.append(f'<pre class="{pre_class}"><code>{_escape_html(content_or_dir)}</code></pre>')
            
            html_parts.append('</details>')
    
    return ''.join(html_parts)

def _escape_html(text: str) -> str:
    """
    Escapes HTML special characters to prevent rendering issues.
    """
    if not isinstance(text, str):
        text = str(text)
    
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))

def generate_html_map(
    file_info_list: List[Dict[str, Any]],
    repo_root_path: Path,
    repo_name: str,
    output_file_path: Path,
    config_module
) -> None:
    """
    Generates an interactive HTML map of the repository.
    
    Args:
        file_info_list: List of dictionaries containing file metadata
        repo_root_path: Path to repository root
        repo_name: Name of the repository
        output_file_path: Path to write the HTML output file
        config_module: Configuration module with constants
    """
    # Build the nested tree with file content
    content_tree = _build_html_content_tree(file_info_list, repo_root_path, config_module)
    
    # Generate the HTML tree structure
    html_tree = _generate_html_fragment_recursive(content_tree)
    
    # Count the number of files for statistics
    file_count = len(file_info_list)
    
    # Construct the complete HTML document
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{repo_name} - Repository Map</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism.min.css">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.5;
            margin: 0;
            padding: 20px;
            color: #333;
            background-color: #f8f9fa;
        }}
        
        header {{
            background-color: #4a4a4a;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            margin: 0;
            font-size: 2em;
        }}
        
        .stats {{
            font-size: 0.9em;
            color: #ddd;
            margin-top: 5px;
        }}
        
        .repository-container {{
            padding: 10px 0;
        }}
        
        /* Tree styling */
        details {{
            margin-left: 20px;
        }}
        
        details summary {{
            cursor: pointer;
            padding: 5px;
            background-color: #fff;
            border-radius: 4px;
            margin: 2px 0;
        }}
        
        details summary:hover {{
            background-color: #f1f1f1;
        }}
        
        .dir-name {{
            font-weight: bold;
            color: #0366d6;
        }}
        
        .file-name {{
            color: #24292e;
        }}
        
        pre {{
            background-color: #f6f8fa;
            border-radius: 3px;
            padding: 10px;
            overflow: auto;
            max-height: 500px;
            margin: 10px 0;
            border: 1px solid #ddd;
        }}
        
        .binary-content {{
            background-color: #f1f1f1;
            color: #777;
            font-style: italic;
        }}
        
        .copy-button {{
            position: absolute;
            right: 50px;
            margin-top: -30px;
            background-color: #f1f1f1;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 3px 8px;
            font-size: 0.8em;
            cursor: pointer;
        }}
        
        .copy-button:hover {{
            background-color: #e1e1e1;
        }}
        
        code {{
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 0.9em;
        }}
        
        /* Make root details expanded by default */
        .root-details {{
            margin-left: 0;
        }}
        
        /* Footer */
        footer {{
            margin-top: 30px;
            text-align: center;
            color: #777;
            font-size: 0.8em;
            border-top: 1px solid #ddd;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <header>
        <h1>{repo_name} Repository Map</h1>
        <p class="stats">Files: {file_count} | Generated: <span id="generation-date"></span></p>
    </header>
    
    <div class="repository-container">
        <details open class="root-details">
            <summary class="dir-name">{repo_name}/</summary>
            {html_tree}
        </details>
    </div>
    
    <footer>
        Generated with repo-mapper | <a href="https://github.com/username/repo-mapper" target="_blank">Project Page</a>
    </footer>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/plugins/autoloader/prism-autoloader.min.js"></script>
    
    <script>
        // Set generation date
        document.getElementById('generation-date').textContent = new Date().toLocaleString();
        
        // Copy to clipboard functionality
        function copyToClipboard(button) {{
            const codeElem = button.nextElementSibling.querySelector('code');
            const textToCopy = codeElem.textContent;
            
            const textArea = document.createElement('textarea');
            textArea.value = textToCopy;
            document.body.appendChild(textArea);
            textArea.select();
            
            try {{
                document.execCommand('copy');
                button.textContent = 'Copied!';
                setTimeout(() => {{
                    button.textContent = 'Copy';
                }}, 2000);
            }} catch (err) {{
                console.error('Failed to copy text:', err);
                button.textContent = 'Failed to copy';
                setTimeout(() => {{
                    button.textContent = 'Copy';
                }}, 2000);
            }}
            
            document.body.removeChild(textArea);
        }}
    </script>
</body>
</html>"""
    
    # Write the HTML to the output file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(html)