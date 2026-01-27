# -*- coding: utf-8 -*-
"""
Parse beshalach document - v7
Use existing v2 HTML for summaries (already correctly parsed),
then match with full texts from extracted file.
"""

import re
import sys

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def normalize(text):
    """Normalize for comparison"""
    return re.sub(r'[\s"\'\-־–—׳״]', '', text).strip()

def extract_summaries_from_html(html):
    """Extract already-parsed summaries from v2 HTML"""
    summaries = []
    current_sefer = None
    
    # Find summary entries
    sefer_pattern = re.compile(r'<div class="sefer-header">([^<]+)</div>')
    entry_pattern = re.compile(
        r'<div class="summary-entry">\s*'
        r'<span class="entry-id">\[(\d+)\]</span>\s*'
        r'<span class="entry-verse">([^<]+)</span>\s*'
        r'<span class="entry-summary">([^<]+)</span>\s*'
        r'<span class="entry-page">([^<]+)</span>\s*'
        r'</div>'
    )
    
    # Find the summary section
    summary_section = re.search(r'<div class="source-header">מפתח ענינים</div>(.*?)<div class="divider">', html, re.DOTALL)
    if not summary_section:
        return []
    
    section_html = summary_section.group(1)
    
    # Parse line by line
    pos = 0
    while pos < len(section_html):
        # Check for sefer header
        sefer_match = sefer_pattern.search(section_html, pos)
        entry_match = entry_pattern.search(section_html, pos)
        
        if sefer_match and (not entry_match or sefer_match.start() < entry_match.start()):
            current_sefer = sefer_match.group(1)
            pos = sefer_match.end()
        elif entry_match:
            summaries.append({
                'id': int(entry_match.group(1)),
                'sefer': current_sefer,
                'verse': entry_match.group(2),
                'summary': entry_match.group(3),
                'page': entry_match.group(4)
            })
            pos = entry_match.end()
        else:
            break
    
    return summaries

def parse_full_texts(content):
    """Parse full text passages from מקור השפע section"""
    lines = content.split('\n')
    full_texts = []
    current_sefer = None
    in_full_text = False
    
    # Full text starts with <h1><b>sefer</b></h1>
    book_pattern = re.compile(r'<center>\s*<h1>\s*(?:<b>)?([^<]+)(?:</b>)?\s*</h1>\s*</center>')
    skip_titles = ['ליקוטי ספרי חסידות', 'מפתח הספרים', 'מפתח ענינים']
    
    # Passage start: <b>verse</b>
    passage_pattern = re.compile(r'^<b>([^<]{1,80})</b>')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for book header
        book_match = book_pattern.match(line)
        if book_match:
            name = book_match.group(1).strip()
            if not any(skip in name for skip in skip_titles):
                current_sefer = name
                in_full_text = True
            i += 1
            continue
        
        if not in_full_text or not current_sefer:
            i += 1
            continue
        
        # Check for passage start
        passage_match = passage_pattern.match(line)
        if passage_match and '<center>' not in line:
            verse = passage_match.group(1).strip()
            
            # Collect full passage
            passage_lines = [line]
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if book_pattern.match(next_line):
                    break
                if passage_pattern.match(next_line) and '<center>' not in next_line:
                    break
                if next_line and '<footer>' not in next_line and '<header>' not in next_line.lower():
                    passage_lines.append(next_line)
                j += 1
            
            text = '\n'.join(passage_lines)
            if len(text) > 50:
                full_texts.append({
                    'sefer': current_sefer,
                    'verse': verse,
                    'text': text
                })
            i = j
        else:
            i += 1
    
    return full_texts

def match_summary_to_fulltext(summary, full_texts, used_indices):
    """Match summary to full text using verse and content matching"""
    sefer = normalize(summary['sefer'])
    verse = normalize(summary['verse'])
    summary_text = normalize(summary['summary'])
    
    best_match = None
    best_score = 0
    best_idx = -1
    
    for idx, ft in enumerate(full_texts):
        if idx in used_indices:
            continue
        
        ft_sefer = normalize(ft['sefer'])
        ft_verse = normalize(ft['verse'])
        ft_text = normalize(ft['text'][:500])
        
        score = 0
        
        # Sefer matching (bonus, not required)
        if sefer == ft_sefer:
            score += 30
        elif len(sefer) > 4 and len(ft_sefer) > 4:
            if sefer in ft_sefer or ft_sefer in sefer:
                score += 20
            elif sefer[:4] == ft_sefer[:4]:
                score += 15
        
        # Verse matching (primary)
        if verse == ft_verse:
            score += 100
        elif len(verse) > 2 and len(ft_verse) > 2:
            if verse in ft_verse:
                score += 80
            elif ft_verse in verse:
                score += 70
            else:
                # First chars match
                common = 0
                for c1, c2 in zip(verse, ft_verse):
                    if c1 == c2:
                        common += 1
                    else:
                        break
                if common >= 2:
                    score += 30 + common * 10
        
        # Content matching - check if summary words appear in full text
        summary_words = set(re.findall(r'[א-ת]+', summary_text))
        if len(summary_words) > 3:
            matches = sum(1 for w in summary_words if w in ft_text)
            content_ratio = matches / len(summary_words)
            if content_ratio > 0.3:
                score += int(content_ratio * 50)
        
        if score > best_score:
            best_score = score
            best_match = ft
            best_idx = idx
    
    if best_match and best_score >= 50:
        used_indices.add(best_idx)
        return best_match
    
    return None

def clean_text(text):
    """Clean HTML for display"""
    text = re.sub(r'<b>([^<]*)</b>', r'\1', text)
    text = re.sub(r'<u>([^<]*)</u>', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def generate_html(summaries, full_texts):
    """Generate final HTML with actual full texts"""
    
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
        .entry-id { font-weight: bold; min-width: 35px; }
        .entry-verse { font-weight: bold; color: #333; min-width: 80px; }
        .entry-summary { flex: 1; }
        .entry-page { font-weight: bold; min-width: 45px; text-align: left; }
        .divider { border-top: 2px solid #000; margin: 30px 0; }
        .source-header {
            text-align: center;
            font-weight: bold;
            font-size: 20pt;
            margin: 25px 0;
            color: #222;
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
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #ccc;
            border-radius: 6px;
            background: #fafafa;
        }
        .quote-header {
            display: flex;
            gap: 20px;
            margin-bottom: 12px;
            font-weight: bold;
            font-size: 15pt;
            border-bottom: 2px solid #ddd;
            padding-bottom: 10px;
            color: #444;
        }
        .quote-text { 
            text-align: justify; 
            line-height: 2;
            font-size: 14pt;
        }
        .no-match {
            color: #666;
            font-style: italic;
            background: #fff8e1;
            padding: 10px;
            border-radius: 4px;
        }
        h1 { text-align: center; font-size: 24pt; margin-bottom: 5px; }
        h2 { text-align: center; font-size: 18pt; margin-top: 5px; color: #555; }
    </style>
</head>
<body>
    <h1>ליקוטי ספרי חסידות</h1>
    <h2>פרשת בשלח</h2>
    <div class="divider"></div>
    
    <section>
        <div class="source-header">מפתח ענינים</div>
'''
    
    # Summaries
    current_sefer = None
    for s in summaries:
        if s['sefer'] != current_sefer:
            current_sefer = s['sefer']
            html += f'        <div class="sefer-header">{current_sefer}</div>\n'
        html += f'''        <div class="summary-entry">
            <span class="entry-id">[{s['id']}]</span>
            <span class="entry-verse">{s['verse']}</span>
            <span class="entry-summary">{s['summary']}</span>
            <span class="entry-page">{s['page']}</span>
        </div>\n'''
    
    html += '''    </section>
    <div class="divider"></div>
    
    <section>
        <div class="source-header">מקור השפע</div>
'''
    
    # Full texts
    used = set()
    current_sefer = None
    matched = 0
    
    for s in summaries:
        if s['sefer'] != current_sefer:
            current_sefer = s['sefer']
            html += f'        <div class="sefer-header">{current_sefer}</div>\n'
        
        ft = match_summary_to_fulltext(s, full_texts, used)
        
        if ft:
            matched += 1
            text = clean_text(ft['text'])
            if len(text) > 3000:
                text = text[:3000] + '\n\n[...]'
        else:
            # Fallback: use summary as placeholder
            text = f'<div class="no-match">{s["summary"]}</div>'
        
        html += f'''        <div class="quote-entry">
            <div class="quote-header">
                <span>[{s['id']}]</span>
                <span>{s['verse']}</span>
                <span>עמ\' {s['page']}</span>
            </div>
            <div class="quote-text">{text}</div>
        </div>\n'''
    
    html += '''    </section>
</body>
</html>'''
    
    return html, matched

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    # Read existing v2 HTML to get properly parsed summaries
    print("Reading v2 HTML for summaries...")
    v2_html = read_file('beshalach_output_v2.html')
    summaries = extract_summaries_from_html(v2_html)
    print(f"Found {len(summaries)} summaries")
    
    # Show first few
    for s in summaries[:5]:
        print(f"  [{s['id']}] {s['sefer']}: {s['verse']} ({s['page']})")
    
    # Parse full texts
    print("\nParsing full texts from extracted file...")
    content = read_file('extracted_beshalach.txt')
    full_texts = parse_full_texts(content)
    print(f"Found {len(full_texts)} full text passages")
    
    # Show first few
    for ft in full_texts[:5]:
        print(f"  {ft['sefer']}: {ft['verse'][:25]}...")
    
    # Generate HTML
    print("\nGenerating final HTML...")
    html, matched = generate_html(summaries, full_texts)
    
    with open('beshalach_output_v3.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\nOutput: beshalach_output_v3.html")
    print(f"Summaries: {len(summaries)}")
    print(f"Full texts: {len(full_texts)}")
    print(f"Matched: {matched}/{len(summaries)} ({100*matched/len(summaries):.1f}%)")

if __name__ == '__main__':
    main()
