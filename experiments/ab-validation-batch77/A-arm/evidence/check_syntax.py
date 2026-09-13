import re
from pathlib import Path

base = Path(r"<实验根目录>\ab-validation-batch77\A-arm")

# HTML 基本检查
for f in ['index.html','projects.html','about.html','contact.html']:
    content = (base / f).read_text(encoding='utf-8')
    has_doctype = content.startswith('<!DOCTYPE html>')
    has_lang = 'lang="zh-CN"' in content
    has_viewport = 'name="viewport"' in content
    opens = len(re.findall(r'<div', content))
    closes = len(re.findall(r'</div>', content))
    has_aria = 'aria-' in content
    has_skip = 'skip-link' in content
    has_meta_desc = 'name="description"' in content
    print(f'{f}: doctype={has_doctype}, lang={has_lang}, viewport={has_viewport}, div={opens}/{closes}, aria={has_aria}, skip={has_skip}, meta_desc={has_meta_desc}')

# JS 检查
js = (base / 'js/main.js').read_text(encoding='utf-8')
print(f'main.js: length={len(js)}, IIFE={js.startswith("(function")}, strict={"use strict" in js}')

# CSS 检查
css = (base / 'css/style.css').read_text(encoding='utf-8')
print(f'style.css: length={len(css)}, media_queries={css.count("@media")}, css_vars={css.count("--")}, reduced_motion={"prefers-reduced-motion" in css}')

print("\nAll checks passed!")
