#!/usr/bin/env python3
import re
import os
import sys
import argparse
import html

def parse_attributes(text):
    attr_match = re.search(r'(.+?)\s*(\{[^}]+\})\s*$', text.strip())
    if attr_match:
        main_text = attr_match.group(1).strip()
        attrs_text = attr_match.group(2)[1:-1].strip()

        classes = []
        id_val = None

        if attrs_text.startswith('.'):
            parts = attrs_text[1:].split('#')
            classes = [c for c in parts[0].split('.') if c]
            id_val = parts[1] if len(parts) > 1 else None
        elif attrs_text.startswith('#'):
            id_val = attrs_text[1:]
        else:
            classes = [attrs_text]

        attrs = ''
        if classes: attrs += f' class="{" ".join(classes)}"'
        if id_val: attrs += f' id="{id_val}"'
        return attrs, main_text
    return '', text.strip()

def process_inline_markup(line):
    line = re.sub(r'`([^`]+)`', lambda m: f"<code>{m.group(1)}</code>", line)
    line = re.sub(r'\*\*\*(.*?)\*\*\*', lambda m: f"<strong><em>{m.group(1)}</em></strong>", line)
    line = re.sub(r'\*\*(.*?)\*\*', lambda m: f"<strong>{m.group(1)}</strong>", line)
    line = re.sub(r'__(.*?)__', lambda m: f"<strong>{m.group(1)}</strong>", line)
    line = re.sub(r'\*(.*?)\*', lambda m: f"<em>{m.group(1)}</em>", line)
    line = re.sub(r'_(.*?)_', lambda m: f"<em>{m.group(1)}</em>", line)
    line = re.sub(r'~~(.*?)~~', lambda m: f"<del>{m.group(1)}</del>", line)
    line = re.sub(r'!\[([^\]]*)\]\s*\(\s*([^)\s]+)\s*(?:"[^"]*")?\s*\)', 
                  lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}">', line)
    line = re.sub(r'\[([^\]]*)\]\s*\(\s*([^)\s]+)\s*(?:"[^"]*")?\s*\)', 
                  lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', line)
    if line.rstrip().endswith('  '):
        line = line.rstrip() + '<br>'
    return line

def convert_mdex_to_html(mdex_file):
    base_name = os.path.splitext(mdex_file)[0]
    html_file = f"{base_name}.html"
    css_file = f"{base_name}.css"

    if not os.path.exists(css_file):
        css_content = """/* MDEX Styles */"""
        with open(css_file, 'w') as f:
            f.write(css_content)
        print(f"✅ Created {css_file}")

    with open(mdex_file, 'r') as f:
        contents = [line.rstrip() for line in f]

    html_output = []
    blockquote_stack = []
    list_stack = []
    code_block = False

    for line in contents:
        stripped = line.strip()

        if code_block:
            if stripped.startswith('```'):
                html_output.append('</pre>')
                code_block = False
            else:
                html_output.append(html.escape(line))
            continue

        if stripped.startswith('```'):
            html_output.append('<pre>')
            code_block = True
            continue

        if stripped == '':
            html_output.append('<br>')
            continue

        if re.match(r'^[*_-]{3,}$', stripped):
            while blockquote_stack: html_output.append('</blockquote>'); blockquote_stack.pop()
            while list_stack: html_output.append('</li></ul></ol>'); list_stack.pop()
            html_output.append('<hr>')
            continue

        if stripped.startswith('#'):
            while blockquote_stack: html_output.append('</blockquote>'); blockquote_stack.pop()
            while list_stack: html_output.append('</li></ul></ol>'); list_stack.pop()
            level = len(line) - len(line.lstrip('#'))
            text = line.lstrip('#').strip()
            attrs, clean_text = parse_attributes(text)
            processed_text = process_inline_markup(clean_text)
            html_output.append(f'<h{level}{attrs}>{processed_text}</h{level}>')
            continue

        quote_level = 0
        clean_line = line
        while clean_line.startswith('>'):
            quote_level += 1
            clean_line = clean_line[1:].lstrip()

        list_match = re.match(r'^(\s*)((\d+\.)|[\*\+\-])\s+(.*)', line)
        if list_match:
            indent, list_marker_full, marker_type, raw_content = list_match.groups()
            attrs, content = parse_attributes(raw_content.strip())
            content = process_inline_markup(content)

            while blockquote_stack: html_output.append('</blockquote>'); blockquote_stack.pop()
            while list_stack: html_output.append('</li></ul></ol>'); list_stack.pop()

            for _ in range(quote_level): 
                html_output.append('<blockquote>'); blockquote_stack.append(True)

            tag = 'ol' if marker_type and marker_type.endswith('.') else 'ul'
            html_output.append(f'<{tag}><li{attrs}>{content}')
            list_stack.append((tag, True))
            continue

        while len(blockquote_stack) > quote_level:
            html_output.append('</blockquote>'); blockquote_stack.pop()
        while len(list_stack): html_output.append('</li></ul></ol>'); list_stack.pop()

        while len(blockquote_stack) < quote_level:
            html_output.append('<blockquote>'); blockquote_stack.append(True)

        if quote_level == 0 and blockquote_stack:
            while blockquote_stack: html_output.append('</blockquote>'); blockquote_stack.pop()

        attrs, clean_text = parse_attributes(clean_line)
        text = process_inline_markup(clean_text)
        html_output.append(f'<p{attrs}>{text}</p>')

    while blockquote_stack: html_output.append('</blockquote>'); blockquote_stack.pop()
    while list_stack: html_output.append('</li></ul></ol>'); list_stack.pop()

    html_content = '\n'.join(html_output)

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="{css_file}">
    <title>{base_name.title()}</title>
</head>
<body>
    {html_content}
</body>
</html>""")

    print(f"✅ Created {html_file}")
    print(f"📁 Files: {html_file}, {css_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MDEX Compiler (.mdex → .html)")
    parser.add_argument('file', nargs='?', help="Input .mdex file")
    args = parser.parse_args()

    if args.file and args.file.endswith('.mdex'):
        convert_mdex_to_html(args.file)
    elif args.file:
        print("❌ File must end with .mdex")
        sys.exit(1)
    else:
        print("Usage: ./mdex.py index.mdex")
        sys.exit(1)
