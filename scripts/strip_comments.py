import os
import re
import io
import tokenize
import ast
import sys

BASE_DIR = r"c:\\Users\\luism\\Documents\\Prácticas\\GSI\\Proyecto"
TARGETS = [
    (os.path.join(BASE_DIR, 'templates', 'denuncias'), ('.html', '.htm')),
    (os.path.join(BASE_DIR, 'static', 'css'), ('.css',)),
    (os.path.join(BASE_DIR, 'static', 'js'), ('.js',)),
    (BASE_DIR, ('.py',)),
    (os.path.join(BASE_DIR, 'denuncias'), ('.py',)),
    (os.path.join(BASE_DIR, 'canal_denuncias'), ('.py',)),
]

HEADER_PATTERNS = (
    re.compile(r"^#!"),
    re.compile(r"coding[:=]\\s*[-\\w.]+"),
)


def strip_html_css_js_comments(content: str, ext: str) -> str:
    content = re.sub(r"/\\*.*?\\*/", '', content, flags=re.S)
    content = re.sub(r"^[\\t ]*//.*$", '', content, flags=re.M)
    if ext in ('.html', '.htm'):
        content = re.sub(r"<!--.*?-->", '', content, flags=re.S)
        content = re.sub(r"\\{#.*?#\\}", '', content, flags=re.S)
    return content


def strip_python_comments(content: str) -> str:
    lines = content.splitlines(True)
    header_lines = []
    preserved_idx = set()
    for i in range(min(2, len(lines))):
        if any(p.search(lines[i]) for p in HEADER_PATTERNS):
            header_lines.append(lines[i])
            preserved_idx.add(i)
    remainder = ''.join(l for i, l in enumerate(lines) if i not in preserved_idx)

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(remainder).readline))
        filtered = [tok for tok in tokens if tok.type != tokenize.COMMENT]
        rebuilt = tokenize.untokenize(filtered)
    except Exception:
        rebuilt = re.sub(r"^[\\t ]*#.*$", '', remainder, flags=re.M)
        rebuilt = re.sub(r"([^'\"])(#).*", lambda m: m.group(1).rstrip(), rebuilt)

    return ''.join(header_lines) + rebuilt


def strip_python_docstrings(content: str) -> str:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return content

    class DocstringRemover(ast.NodeTransformer):
        def remove_ds(self, node):
            if getattr(node, 'body', None):
                if (len(node.body) > 0 and isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], 'value', None), ast.Constant) and isinstance(node.body[0].value.value, str)):
                    node.body.pop(0)
            return node

        def visit_FunctionDef(self, node):
            self.generic_visit(node)
            return self.remove_ds(node)

        def visit_AsyncFunctionDef(self, node):
            self.generic_visit(node)
            return self.remove_ds(node)

        def visit_ClassDef(self, node):
            self.generic_visit(node)
            return self.remove_ds(node)

        def visit_Module(self, node):
            self.generic_visit(node)
            return self.remove_ds(node)

    new_tree = DocstringRemover().visit(tree)
    ast.fix_missing_locations(new_tree)
    try:
        new_content = ast.unparse(new_tree)
        if not new_content.endswith('\n'):
            new_content += '\n'
        return new_content
    except Exception:
        return content


def strip_comments(content: str, ext: str, path: str) -> str:
    if ext == '.py':
        if os.path.basename(path) == 'strip_comments.py':
            return content
        content_no_docs = strip_python_docstrings(content)
        return strip_python_comments(content_no_docs)
    else:
        return strip_html_css_js_comments(content, ext)


changed_files = []
for dir_path, exts in TARGETS:
    if not os.path.isdir(dir_path):
        continue
    for root, dirs, files in os.walk(dir_path):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for name in files:
            lower = name.lower()
            if not any(lower.endswith(ext) for ext in exts):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    original = f.read()
                cleaned = strip_comments(original, os.path.splitext(lower)[1], path)
                if cleaned != original:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(cleaned)
                    changed_files.append(path)
            except Exception as e:
                print(f"Skip {path}: {e}")

print(f"Stripped comments in {len(changed_files)} files.")
for p in changed_files:
    print(p)