"""
Convert authentication_report.md to PDF using markdown and pdfkit/weasyprint.
This script uses markdown2 + pdfkit (wkhtmltopdf) as primary,
or falls back to a browser-based approach.
"""
import subprocess
import sys
import os

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Try markdown2 + weasyprint approach
def convert_with_weasyprint():
    try:
        import markdown2
    except ImportError:
        install("markdown2")
        import markdown2

    try:
        from weasyprint import HTML
    except ImportError:
        install("weasyprint")
        from weasyprint import HTML

    script_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(script_dir, "authentication_report.md")
    pdf_path = os.path.join(script_dir, "authentication_report.pdf")

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Convert markdown to HTML with extras
    html_body = markdown2.markdown(md_content, extras=[
        "tables", "fenced-code-blocks", "code-friendly",
        "cuddled-lists", "break-on-newline"
    ])

    # Professional CSS styling
    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

@page {{
    size: A4;
    margin: 2cm 2.5cm;
    @bottom-center {{
        content: counter(page);
        font-family: 'Inter', sans-serif;
        font-size: 9pt;
        color: #94a3b8;
    }}
}}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 10.5pt;
    line-height: 1.7;
    color: #1e293b;
    background: white;
}}

h1 {{
    font-size: 22pt;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 8px;
    padding-bottom: 12px;
    border-bottom: 3px solid #6366f1;
}}

h2 {{
    font-size: 15pt;
    font-weight: 600;
    color: #1e40af;
    margin-top: 28px;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1.5px solid #e2e8f0;
}}

h3 {{
    font-size: 12pt;
    font-weight: 600;
    color: #334155;
    margin-top: 20px;
    margin-bottom: 8px;
}}

p {{
    margin-bottom: 10px;
    text-align: justify;
}}

blockquote {{
    border-left: 4px solid #6366f1;
    padding: 10px 16px;
    margin: 12px 0;
    background: #f8fafc;
    border-radius: 0 6px 6px 0;
    color: #475569;
    font-size: 10pt;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}}

th {{
    background: #1e293b;
    color: white;
    font-weight: 600;
    text-align: left;
    padding: 10px 12px;
}}

th:first-child {{
    border-radius: 6px 0 0 0;
}}

th:last-child {{
    border-radius: 0 6px 0 0;
}}

td {{
    padding: 8px 12px;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: top;
}}

tr:nth-child(even) {{
    background: #f8fafc;
}}

tr:hover {{
    background: #f1f5f9;
}}

code {{
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 9pt;
    background: #f1f5f9;
    padding: 2px 6px;
    border-radius: 4px;
    color: #7c3aed;
}}

pre {{
    background: #1e293b;
    color: #e2e8f0;
    padding: 16px;
    border-radius: 8px;
    margin: 14px 0;
    overflow-x: auto;
    font-size: 9pt;
    line-height: 1.5;
    page-break-inside: avoid;
}}

pre code {{
    background: none;
    color: #e2e8f0;
    padding: 0;
}}

ul, ol {{
    margin: 8px 0 8px 20px;
}}

li {{
    margin-bottom: 4px;
}}

strong {{
    color: #0f172a;
}}

hr {{
    border: none;
    border-top: 2px solid #e2e8f0;
    margin: 24px 0;
}}

a {{
    color: #6366f1;
    text-decoration: none;
}}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    HTML(string=full_html).write_pdf(pdf_path)
    print(f"✅ PDF created successfully: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    convert_with_weasyprint()
