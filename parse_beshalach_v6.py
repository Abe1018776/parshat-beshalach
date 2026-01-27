# -*- coding: utf-8 -*-
"""
Parse beshalach document - v6
Properly separates summaries from full texts using <h1> tag detection.
"""

import re
import sys

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def normalize_text(text):
    """Normalize Hebrew text for comparison"""
    text = re.sub(r'["\'\-־–—׳״\s]', '', text)
    return text.strip()

def find_full_text_start(lines):
    """Find where full-text section begins (first <h1><b>ספר</b></h1> that's not a title)"""
    skip_titles = ['ליקוטי ספרי חסידות', 'מפתח הספרים לפרשת בשלח', 'מפתח ענינים']
    for i, line in enumerate(lines):
        if '<h1>' in line and '<b>' in line:
            match = re.search(r'<h1>\s*(?:<b>)?([^<]+)(?:</b>)?\s*</h1>', line)
            if match:
                title = match.group(1).strip()
                if not any(skip in title for skip in skip_titles):
                    return i
    return len(lines)

def parse_summaries(lines, end_line):
    """Parse summary entries from the index section"""
    summaries = []
    current_sefer = "דגל מחנה אפרים"
    
    # Page pattern at end: dots + Hebrew numerals
    page_pattern = re.compile(r'\.{2,}\s*([\'א-ת״]["\']?[א-ת]?["\']?)\s*$|([א-ת]["\']?[א-ת]?["\']?)\s*$')
    # Sefer header in summaries: <center><b>name</b></center> (no h1)
    sefer_pattern = re.compile(r'^<center>\s*<b>([^<]+)</b>\s*</center>$')
    # Entry start: <b>verse</b>- or bold verse with dash
    entry_start_pattern = re.compile(r'^<b>([^<]+)</b>\s*[-–](.*)$')
    # Skip TOC entries with lots of dots
    toc_pattern = re.compile(r'^<b>[^<]+</b>\.{5,}')
    
    skip_sefers = ['עם מפתח ענינים', 'פרשת בשלח', '(לשון אגרת הרמב"ן)', 
                   'וכאשר תקום מן הספר תחפש באשר למדת', 'אם יש בו דבר אשר תוכל לקיימו',
                   'כל הזכויות שמורות למו"ל']
    
    i = 0
    while i < end_line:
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # Skip TOC
        if toc_pattern.match(line):
            i += 1
            continue
        
        # Check for sefer header
        sefer_match = sefer_pattern.match(line)
        if sefer_match:
            name = sefer_match.group(1).strip()
            if not any(skip in name for skip in skip_sefers):
                current_sefer = name
            i += 1
            continue
        
        # Check for entry start
        entry_match = entry_start_pattern.match(line)
        if entry_match:
            verse = entry_match.group(1).strip()
            rest = entry_match.group(2)
            
            # Collect continuation lines until page reference found
            full_text = rest
            j = i + 1
            while j < end_line and j < i + 10:
                next_line = lines[j].strip()
                if not next_line:
                    j += 1
                    continue
                # Stop if new entry or header
                if entry_start_pattern.match(next_line) or sefer_pattern.match(next_line):
                    break
                full_text += ' ' + next_line
                if page_pattern.search(next_line):
                    j += 1
                    break
                j += 1
            
            # Extract page
            page_match = page_pattern.search(full_text)
            if page_match:
                page = page_match.group(1) or page_match.group(2)
                summary = page_pattern.sub('', full_text).strip()
                summary = re.sub(r'\.+\s*$', '', summary).strip()
                
                if verse and summary and len(verse) < 60:
                    summaries.append({
                        'sefer': current_sefer,
                        'verse': verse,
                        'summary': summary,
                        'page': page
                    })
            
            i = j
        else:
            i += 1
    
    return summaries

def parse_full_texts(lines, start_line):
    """Parse full text passages from the מקור השפע section"""
    full_texts = []
    current_sefer = None
    
    # Book header with h1
    book_pattern = re.compile(r'<center>\s*<h1>\s*(?:<b>)?([^<]+)(?:</b>)?\s*</h1>\s*</center>')
    # Passage start: bold Hebrew text
    passage_pattern = re.compile(r'^<b>([^<]{1,80})</b>')
    
    i = start_line
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for book header
        book_match = book_pattern.match(line)
        if book_match:
            current_sefer = book_match.group(1).strip()
            i += 1
            continue
        
        if not current_sefer:
            i += 1
            continue
        
        # Check for passage start
        passage_match = passage_pattern.match(line)
        if passage_match and '<center>' not in line:
            verse = passage_match.group(1).strip()
            
            # Collect the full passage
            passage_lines = [line]
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                
                # Stop conditions
                if book_pattern.match(next_line):
                    break
                if passage_pattern.match(next_line) and '<center>' not in next_line:
                    # New passage starts
                    break
                
                if next_line and '<footer>' not in next_line and '<header>' not in next_line.lower():
                    passage_lines.append(next_line)
                j += 1
            
            passage_text = '\n'.join(passage_lines)
            if len(passage_text) > 50:  # Skip very short fragments
                full_texts.append({
                    'sefer': current_sefer,
                    'verse': verse,
                    'text': passage_text
                })
            
            i = j
        else:
            i += 1
    
    return full_texts

def match_summary_to_fulltext(summary, full_texts, sefer_indices, used):
    """Match summary to its full text passage"""
    sefer_norm = normalize_text(summary['sefer'])
    verse_norm = normalize_text(summary['verse'])
    
    # Find matching sefer passages
    candidates = []
    for idx, ft in enumerate(full_texts):
        if idx in used:
            continue
        ft_sefer = normalize_text(ft['sefer'])
        ft_verse = normalize_text(ft['verse'])
        
        # Check sefer match (fuzzy)
        sefer_match = False
        if sefer_norm in ft_sefer or ft_sefer in sefer_norm:
            sefer_match = True
        # Handle special cases like "מאור ושמש" 
        if len(sefer_norm) > 5 and len(ft_sefer) > 5:
            if sefer_norm[:5] == ft_sefer[:5]:
                sefer_match = True
        
        if not sefer_match:
            continue
        
        # Check verse match
        if verse_norm == ft_verse:
            candidates.append((idx, ft, 100))
        elif verse_norm in ft_verse or ft_verse in verse_norm:
            candidates.append((idx, ft, 80))
        elif len(verse_norm) > 3 and verse_norm[:3] == ft_verse[:3] if len(ft_verse) > 3 else False:
            candidates.append((idx, ft, 60))
    
    if candidates:
        # Sort by score, prefer first occurrence
        candidates.sort(key=lambda x: (-x[2], x[0]))
        idx, ft, _ = candidates[0]
        used.add(idx)
        return ft
    
    return None

def clean_html(text):
    """Clean HTML for display"""
    # Remove HTML tags
    text = re.sub(r'<b>([^<]+)</b>', r'\1', text)
    text = re.sub(r'<u>([^<]+)</u>', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def generate_html(summaries, full_texts):
    """Generate final HTML"""
    html = '''<!DOCTYPE html>
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
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
        }
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
            background: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
        }
        .quote-entry {
            margin-bottom: 25px;
            padding: 15px;
            border: 1px solid #ccc;
            border-radius: 5px;
            background: #fafafa;
        }
        .quote-header {
            display: flex;
            gap: 15px;
            margin-bottom: 10px;
            font-weight: bold;
            border-bottom: 1px solid #ddd;
            padding-bottom: 8px;
        }
        .quote-text { 
            text-align: justify; 
            line-height: 2;
        }
        .no-match {
            color: #888;
            font-style: italic;
            font-size: 12pt;
        }
        h1, h2 { text-align: center; }
    </style>
</head>
<body>
    <h1>ליקוטי ספרי חסידות</h1>
    <h2>פרשת בשלח</h2>
    <div class="divider"></div>
    
    <section>
        <div class="source-header">מפתח ענינים</div>
'''
    
    # Summaries section
    current_sefer = None
    for i, s in enumerate(summaries, 1):
        if s['sefer'] != current_sefer:
            current_sefer = s['sefer']
            html += f'        <div class="sefer-header">{current_sefer}</div>\n'
        html += f'''        <div class="summary-entry">
            <span class="entry-id">[{i}]</span>
            <span class="entry-verse">{s['verse']}</span>
            <span class="entry-summary">{s['summary']}</span>
            <span class="entry-page">{s['page']}</span>
        </div>\n'''
    
    html += '''    </section>
    <div class="divider"></div>
    
    <section>
        <div class="source-header">מקור השפע</div>
'''
    
    # Full texts section
    used = set()
    sefer_indices = {}
    current_sefer = None
    matched_count = 0
    
    for i, summary in enumerate(summaries, 1):
        if summary['sefer'] != current_sefer:
            current_sefer = summary['sefer']
            html += f'        <div class="sefer-header">{current_sefer}</div>\n'
        
        ft = match_summary_to_fulltext(summary, full_texts, sefer_indices, used)
        
        if ft:
            matched_count += 1
            text = clean_html(ft['text'])
            # Truncate if very long
            if len(text) > 2500:
                text = text[:2500] + ' [...]'
        else:
            text = f'<span class="no-match">[טקסט מלא לא נמצא]</span>'
        
        html += f'''        <div class="quote-entry">
            <div class="quote-header">
                <span>[{i}]</span>
                <span>{summary['verse']}</span>
                <span>עמ' {summary['page']}</span>
            </div>
            <div class="quote-text">{text}</div>
        </div>\n'''
    
    html += '''    </section>
</body>
</html>'''
    
    return html, matched_count

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    content = read_file('extracted_beshalach.txt')
    lines = content.split('\n')
    
    print(f"Total lines: {len(lines)}")
    
    # Find where full texts start
    full_text_start = find_full_text_start(lines)
    print(f"Full text section starts at line: {full_text_start}")
    
    # Parse summaries (before full texts)
    print("Parsing summaries...")
    summaries = parse_summaries(lines, full_text_start)
    print(f"Found {len(summaries)} summary entries")
    
    # Show first few
    for i, s in enumerate(summaries[:5]):
        print(f"  [{i+1}] {s['sefer']}: {s['verse']} - {s['page']}")
    
    # Parse full texts
    print("\nParsing full texts...")
    full_texts = parse_full_texts(lines, full_text_start)
    print(f"Found {len(full_texts)} full text passages")
    
    # Show first few
    for ft in full_texts[:5]:
        print(f"  {ft['sefer']}: {ft['verse'][:30]}...")
    
    # Generate HTML
    print("\nGenerating HTML...")
    html, matched = generate_html(summaries, full_texts)
    
    with open('beshalach_output_v3.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\nOutput: beshalach_output_v3.html")
    print(f"Summaries: {len(summaries)}")
    print(f"Full texts: {len(full_texts)}")
    print(f"Matched: {matched}/{len(summaries)}")

if __name__ == '__main__':
    main()
