# -*- coding: utf-8 -*-
"""
Parse beshalach document with proper full-text matching.
Generates HTML with:
- מפתח ענינים (summaries) at top
- מקור השפע (actual full passages) at bottom
"""

import re
from collections import defaultdict

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def normalize_text(text):
    """Normalize Hebrew text for comparison"""
    text = re.sub(r'["\'\-־–—׳״]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_summaries(content):
    """Parse the summary/index section (lines before full texts)"""
    lines = content.split('\n')
    summaries = []
    current_sefer = "מפתח הספרים לפרשת בשלח"
    
    # Summary entries pattern: <b>verse</b>-summary text...page
    # Page is Hebrew numeral at end of line or next lines
    
    i = 0
    entry_buffer = []
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for full-text section start (has <h1><b>)
        if re.search(r'<center>\s*<h1>\s*<b>', line) and 'מפתח הספרים' not in line and 'ליקוטי' not in line:
            break
        
        # Check for sefer header in summaries (no h1)
        sefer_match = re.match(r'^<center>\s*<b>([^<]+)</b>\s*</center>$', line)
        if sefer_match:
            # Make sure it's not the main title
            sefer_name = sefer_match.group(1).strip()
            if sefer_name not in ['עם מפתח ענינים', 'וכאשר תקום מן הספר תחפש באשר למדת,', 
                                   'אם יש בו דבר אשר תוכל לקיימו.', '(לשון אגרת הרמב"ן)',
                                   'פרשת בשלח']:
                current_sefer = sefer_name
            i += 1
            continue
        
        # Check for entry start: <b>verse</b>-
        entry_start = re.match(r'^<b>([^<]+)</b>\s*[-–—]\s*(.*)$', line)
        if entry_start:
            # Save previous entry if exists
            if entry_buffer:
                summaries.append(process_entry_buffer(entry_buffer, current_sefer))
            entry_buffer = [(entry_start.group(1), entry_start.group(2))]
            i += 1
            continue
        
        # Continuation of entry (before page number)
        if entry_buffer and line and not line.startswith('<'):
            entry_buffer.append(('', line))
        
        i += 1
    
    # Process last entry
    if entry_buffer:
        summaries.append(process_entry_buffer(entry_buffer, current_sefer))
    
    return summaries

def process_entry_buffer(buffer, sefer):
    """Process accumulated lines into a single entry"""
    verse = buffer[0][0]
    text_parts = [buffer[0][1]]
    
    for _, line in buffer[1:]:
        text_parts.append(line)
    
    full_text = ' '.join(text_parts)
    
    # Extract page number (Hebrew numerals at end, after dots or at line end)
    page_match = re.search(r'\.{2,}\s*([א-ת]["\']?[א-ת]?["\']?)\s*$|([א-ת]["\']?[א-ת]?["\']?)\s*$', full_text)
    page = page_match.group(1) or page_match.group(2) if page_match else ''
    
    # Remove page from summary text
    if page_match:
        summary = full_text[:page_match.start()].strip()
        summary = re.sub(r'\.+\s*$', '', summary)
    else:
        summary = full_text.strip()
    
    return {
        'sefer': sefer,
        'verse': verse.strip(),
        'summary': summary.strip(),
        'page': page.strip()
    }

def parse_full_texts(content):
    """Parse the full text section (after <h1><b>ספר</b></h1> headers)"""
    lines = content.split('\n')
    full_texts = []
    current_sefer = None
    current_passage = []
    current_verse = None
    in_full_text_zone = False
    
    # Known book headers that start full-text zone
    book_pattern = re.compile(r'<center>\s*<h1>\s*(?:<b>)?([^<]+)(?:</b>)?\s*</h1>\s*</center>')
    verse_pattern = re.compile(r'^<b>([^<]{1,50})</b>')
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Check for book header (full-text style with h1)
        book_match = book_pattern.match(line_stripped)
        if book_match:
            book_name = book_match.group(1).strip()
            # Skip main titles
            if book_name in ['ליקוטי ספרי חסידות', 'מפתח הספרים לפרשת בשלח']:
                continue
            
            # Save previous passage
            if current_passage and current_verse and current_sefer:
                full_texts.append({
                    'sefer': current_sefer,
                    'verse': current_verse,
                    'text': '\n'.join(current_passage)
                })
            
            current_sefer = book_name
            current_passage = []
            current_verse = None
            in_full_text_zone = True
            continue
        
        if not in_full_text_zone:
            continue
        
        # Check for verse/passage start
        verse_match = verse_pattern.match(line_stripped)
        if verse_match and not line_stripped.startswith('<center>'):
            verse_text = verse_match.group(1).strip()
            # Save previous passage
            if current_passage and current_verse:
                full_texts.append({
                    'sefer': current_sefer,
                    'verse': current_verse,
                    'text': '\n'.join(current_passage)
                })
            current_verse = verse_text
            current_passage = [line_stripped]
            continue
        
        # Add line to current passage
        if current_verse and line_stripped:
            # Skip footer/header lines
            if '<footer>' in line_stripped or '<header>' in line_stripped:
                continue
            current_passage.append(line_stripped)
    
    # Save last passage
    if current_passage and current_verse and current_sefer:
        full_texts.append({
            'sefer': current_sefer,
            'verse': current_verse,
            'text': '\n'.join(current_passage)
        })
    
    return full_texts

def match_summary_to_fulltext(summary, full_texts, used_indices):
    """Match a summary entry to its full text passage"""
    sefer = normalize_text(summary['sefer'])
    verse = normalize_text(summary['verse'])
    
    candidates = []
    for idx, ft in enumerate(full_texts):
        if idx in used_indices:
            continue
        ft_sefer = normalize_text(ft['sefer'])
        ft_verse = normalize_text(ft['verse'])
        
        # Check sefer match (allow partial)
        if sefer not in ft_sefer and ft_sefer not in sefer:
            continue
        
        # Check verse match
        if verse == ft_verse or verse in ft_verse or ft_verse in verse:
            candidates.append((idx, ft))
    
    if candidates:
        # Return first match (order-based)
        idx, ft = candidates[0]
        used_indices.add(idx)
        return ft['text']
    
    return None

def clean_html_for_display(text):
    """Clean up HTML tags for display"""
    # Remove bold tags for verse headings at start
    text = re.sub(r'^<b>([^<]+)</b>\s*', r'\1 - ', text)
    # Keep other formatting but clean up
    text = re.sub(r'<footer>.*?</footer>', '', text, flags=re.DOTALL)
    text = re.sub(r'<header>.*?</header>', '', text, flags=re.DOTALL)
    text = re.sub(r'<center>.*?</center>', '', text, flags=re.DOTALL)
    # Clean extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def generate_html(summaries, full_texts):
    """Generate the final HTML output"""
    html_parts = ['''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>פרשת בשלח - ליקוטי ספרי חסידות</title>
    <style>
        @page { size: A4; margin: 2cm; }
        body {
            font-family: 'Frank Ruehl', 'David', 'Times New Roman', serif;
            font-size: 14pt;
            line-height: 1.8;
            direction: rtl;
            text-align: justify;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
        }
        .page-header {
            display: flex;
            justify-content: space-between;
            border-bottom: 2px solid #000;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .parsha-name { font-weight: bold; font-size: 16pt; }
        .summary-section { margin-bottom: 30px; }
        .summary-entry {
            display: flex;
            align-items: baseline;
            margin: 8px 0;
            gap: 10px;
        }
        .entry-id { font-weight: bold; min-width: 30px; }
        .entry-verse { font-weight: bold; color: #333; }
        .entry-summary { flex: 1; }
        .entry-page { font-weight: bold; min-width: 40px; text-align: left; }
        .divider { border-top: 2px solid #000; margin: 30px 0; }
        .source-header {
            text-align: center;
            font-weight: bold;
            font-size: 18pt;
            margin: 20px 0;
        }
        .sefer-header {
            text-align: center;
            font-weight: bold;
            font-size: 16pt;
            margin: 25px 0 15px 0;
            background: #f5f5f5;
            padding: 8px;
            border-radius: 4px;
        }
        .quote-entry {
            margin-bottom: 25px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background: #fafafa;
        }
        .quote-header {
            display: flex;
            gap: 15px;
            margin-bottom: 10px;
            font-weight: bold;
            border-bottom: 1px solid #ccc;
            padding-bottom: 8px;
            color: #333;
        }
        .quote-text { 
            text-align: justify; 
            line-height: 2; 
            white-space: pre-wrap;
        }
        .no-fulltext {
            color: #999;
            font-style: italic;
        }
        h1 { text-align: center; margin-bottom: 5px; }
        h2 { text-align: center; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>ליקוטי ספרי חסידות</h1>
    <h2>פרשת בשלח</h2>
    
    <div class="divider"></div>
    
    <section class="summary-section">
        <div class="source-header">מפתח ענינים</div>
''']
    
    # Generate summaries section
    current_sefer = None
    for i, entry in enumerate(summaries, 1):
        if entry['sefer'] != current_sefer:
            current_sefer = entry['sefer']
            html_parts.append(f'        <div class="sefer-header">{current_sefer}</div>\n')
        
        html_parts.append(f'''        <div class="summary-entry">
            <span class="entry-id">[{i}]</span>
            <span class="entry-verse">{entry['verse']}</span>
            <span class="entry-summary">{entry['summary']}</span>
            <span class="entry-page">{entry['page']}</span>
        </div>\n''')
    
    html_parts.append('''    </section>
    
    <div class="divider"></div>
    
    <section>
        <div class="source-header">מקור השפע</div>
''')
    
    # Generate full texts section
    used_indices = set()
    current_sefer = None
    
    for i, summary in enumerate(summaries, 1):
        if summary['sefer'] != current_sefer:
            current_sefer = summary['sefer']
            html_parts.append(f'        <div class="sefer-header">{current_sefer}</div>\n')
        
        # Find matching full text
        full_text = match_summary_to_fulltext(summary, full_texts, used_indices)
        
        if full_text:
            cleaned_text = clean_html_for_display(full_text)
            # Limit display length for very long texts
            display_text = cleaned_text[:3000] + '...' if len(cleaned_text) > 3000 else cleaned_text
        else:
            display_text = f'<span class="no-fulltext">[טקסט מלא לא נמצא - {summary["summary"][:100]}...]</span>'
        
        html_parts.append(f'''        <div class="quote-entry">
            <div class="quote-header">
                <span>[{i}]</span>
                <span>{summary['verse']}</span>
                <span>עמ' {summary['page']}</span>
            </div>
            <div class="quote-text">{display_text}</div>
        </div>\n''')
    
    html_parts.append('''    </section>
</body>
</html>''')
    
    return ''.join(html_parts)

def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    # Read the extracted content
    content = read_file('extracted_beshalach.txt')
    
    print("Parsing summaries...")
    summaries = parse_summaries(content)
    print(f"Found {len(summaries)} summary entries")
    
    # Debug: print first few summaries
    for i, s in enumerate(summaries[:5]):
        print(f"  [{i+1}] {s['sefer']}: {s['verse']} - {s['summary'][:50]}... ({s['page']})")
    
    print("\nParsing full texts...")
    full_texts = parse_full_texts(content)
    print(f"Found {len(full_texts)} full text passages")
    
    # Debug: print first few full texts
    for i, ft in enumerate(full_texts[:5]):
        print(f"  {ft['sefer']}: {ft['verse']} - {ft['text'][:50]}...")
    
    print("\nGenerating HTML...")
    html = generate_html(summaries, full_texts)
    
    with open('beshalach_output_v3.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\nOutput written to beshalach_output_v3.html")
    print(f"Total summaries: {len(summaries)}")
    print(f"Total full texts: {len(full_texts)}")

if __name__ == '__main__':
    main()
