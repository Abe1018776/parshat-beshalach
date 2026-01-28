# -*- coding: utf-8 -*-
"""
Generate HTML output with proper RTL support
Find the SPECIFIC paragraph in content that matches each summary's opening words
"""

import re
from typing import List, Tuple, Optional


def clean_html_tags(text: str) -> str:
    """Remove HTML tags from text"""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def normalize_for_matching(text: str) -> str:
    """Normalize text for matching"""
    text = re.sub(r'[\u0591-\u05C7]', '', text)  # Remove nikud
    text = re.sub(r'[.,;:!?\-\u2013\u2014\(\)\[\]\"\'"]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def find_matching_paragraph(opening_words: str, content_text: str) -> Optional[str]:
    """
    Find the specific paragraph in content that starts with the opening words.
    Returns the full paragraph text.
    """
    opening_norm = normalize_for_matching(opening_words)

    # Split content into paragraphs (by double newline or by <b> tags in original)
    # First, let's find paragraphs that start with bold text
    paragraphs = []

    # Split by common paragraph markers
    lines = content_text.split('\n')
    current_para = []

    for line in lines:
        line_clean = clean_html_tags(line).strip()
        if not line_clean:
            if current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
        else:
            current_para.append(line_clean)

    if current_para:
        paragraphs.append(' '.join(current_para))

    # Find paragraph that starts with our opening words
    for para in paragraphs:
        para_norm = normalize_for_matching(para)
        if para_norm.startswith(opening_norm):
            return para
        # Also check if opening words appear at start after some prefix
        if opening_norm in para_norm[:len(opening_norm) + 50]:
            return para

    return None


def extract_summaries_and_content(source_file: str) -> List[dict]:
    """
    Extract summaries from the index section and find their matching content.
    Returns list of {author, opening_words, summary_text, full_content}
    """
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    results = []

    # Find summary section (lines ~76-470)
    # Find content section start
    content_start = 0
    for i, line in enumerate(lines):
        if '<center><h1><b>רבינו בחיי</b></h1></center>' in line:
            content_start = i
            break

    if content_start == 0:
        content_start = 474  # Fallback

    # Parse summaries from index
    current_author = None
    summary_pattern = re.compile(r'^<b>([^<]+)</b>[\-–—](.+)$')
    author_header = re.compile(r'<center><b>([^<]+)</b></center>')

    # Build author -> content mapping
    author_content = {}
    current_content_author = None
    current_content_lines = []

    # First pass: extract all content sections
    author_h1 = re.compile(r'<center><h1>(?:<b>)?([^<]+)(?:</b>)?</h1></center>')

    for i, line in enumerate(lines[content_start:], start=content_start):
        match = author_h1.search(line)
        if match:
            # Save previous
            if current_content_author and current_content_lines:
                if current_content_author not in author_content:
                    author_content[current_content_author] = []
                author_content[current_content_author].append('\n'.join(current_content_lines))

            current_content_author = match.group(1).strip()
            current_content_lines = []
        elif current_content_author:
            current_content_lines.append(line)

    # Save last
    if current_content_author and current_content_lines:
        if current_content_author not in author_content:
            author_content[current_content_author] = []
        author_content[current_content_author].append('\n'.join(current_content_lines))

    print(f"Found content for {len(author_content)} authors")

    # Second pass: extract summaries and match to content
    for i, line in enumerate(lines[76:content_start], start=76):
        # Check for author header
        author_match = author_header.search(line)
        if author_match:
            current_author = author_match.group(1).strip()
            continue

        # Check for summary
        if current_author and '<b>' in line:
            # Accumulate multi-line summary
            summary_lines = [line.strip()]
            j = i + 1
            while j < content_start and j - 76 < len(lines[76:content_start]):
                next_line = lines[j].strip()
                if not next_line or '<center>' in next_line or next_line.startswith('<b>'):
                    break
                summary_lines.append(next_line)
                j += 1

            full_summary = ' '.join(summary_lines)

            # Parse opening words and summary text
            match = summary_pattern.match(full_summary.split('\n')[0] if '\n' in full_summary else full_summary)
            if not match:
                # Try matching just the first line
                first_line = summary_lines[0]
                match = summary_pattern.match(first_line)

            if match:
                opening_words = match.group(1).strip()
                summary_rest = match.group(2).strip()

                # Add continuation lines
                if len(summary_lines) > 1:
                    summary_rest += ' ' + ' '.join(summary_lines[1:])

                # Clean up - remove page number at end
                summary_rest = re.sub(r'\.{2,}[א-ת"\']+\s*$', '', summary_rest)
                summary_rest = re.sub(r'\s+[א-ת][\'"]?[א-ת]?\s*$', '', summary_rest)
                summary_rest = clean_html_tags(summary_rest)

                # Find matching content
                full_content = None

                # Look for this author in content
                for content_author, sections in author_content.items():
                    # Fuzzy author match
                    if current_author in content_author or content_author in current_author:
                        # Search in all sections for this author
                        for section in sections:
                            para = find_matching_paragraph(opening_words, section)
                            if para:
                                full_content = para
                                break
                        if full_content:
                            break

                if full_content and len(summary_rest) > 20:
                    results.append({
                        'author': current_author,
                        'opening_words': opening_words,
                        'summary_text': summary_rest,
                        'full_content': full_content
                    })

    return results


def generate_html(entries: List[dict], output_file: str):
    """Generate HTML with proper RTL support"""

    html = '''<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <title>פרשת בשלח - ליקוטי ספרי חסידות</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: 'David', 'Times New Roman', serif;
            direction: rtl;
            text-align: right;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .entry {
            page-break-after: always;
            margin-bottom: 40px;
        }
        .entry:last-child {
            page-break-after: avoid;
        }
        .header {
            font-size: 18pt;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
        }
        .summary {
            font-size: 14pt;
            margin-bottom: 30px;
            text-align: justify;
        }
        .separator {
            border-top: 1px solid #999;
            margin: 20px 0;
        }
        .source-header {
            font-size: 14pt;
            font-weight: bold;
            text-align: center;
            margin: 15px 0;
            text-decoration: underline;
        }
        .content {
            font-size: 11pt;
            text-align: justify;
            color: #444;
        }
        .entry-number {
            font-weight: bold;
        }
        h1 {
            text-align: center;
            font-size: 24pt;
            margin-bottom: 30px;
        }
    </style>
</head>
<body>
    <h1>פרשת בשלח</h1>
    <h2 style="text-align: center;">ליקוטי ספרי חסידות עם מפתח ענינים</h2>
'''

    for i, entry in enumerate(entries, 1):
        html += f'''
    <div class="entry">
        <div class="header">{entry['opening_words']} - {entry['author']}</div>
        <div class="summary">{entry['summary_text']}</div>
        <div class="separator"></div>
        <div class="source-header">מקור השפע</div>
        <div class="content">
            <span class="entry-number">[{i}]</span> {entry['full_content']}
        </div>
    </div>
'''

    html += '''
</body>
</html>
'''

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"HTML saved: {output_file}")
    print(f"Total entries: {len(entries)}")


def main():
    source_file = r"C:\Users\Main\yanky fridman\ocr-172a161e-b608-46df-83ec-5db88688b475.txt"
    output_file = r"C:\Users\Main\yanky fridman\parshat_beshalach.html"

    print("Extracting summaries and matching content...")
    entries = extract_summaries_and_content(source_file)

    print(f"\nFound {len(entries)} valid entries with matching content")

    if entries:
        print(f"\nFirst 3 entries found (check HTML for details)")

    generate_html(entries, output_file)


if __name__ == '__main__':
    main()
