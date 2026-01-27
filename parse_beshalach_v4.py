# -*- coding: utf-8 -*-
import zipfile
import re
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.chdir(r"C:\Users\Main\yanky fridman")
DOCX_PATH = "ocr-172a161e-b608-46df-83ec-5db88688b475.docx"
OUTPUT_PATH = "beshalach_output_v2.html"

SEFORIM = [
    'רבינו בחיי', 'של"ה', 'אלשי"ך', 'נועם אלימלך', 'מאור ושמש', 'קדושת לוי',
    'אור לשמים', 'דגל מחנה אפרים', 'אוהב ישראל', 'באר מים חיים', 'ישמח משה',
    'ערבי נחל', 'בני יששכר', 'תפארת שלמה', 'זרע קודש', 'דברי חיים', 'צמח צדיק',
    'שפת אמת', 'חידושי הרי"ם', 'אמרי אמת', 'בית ישראל', 'פני מנחם', 'לקוטי יהודה',
    'מהר"י מבעלזא', 'מהרי"ד מבעלזא', 'דובר שלום', 'דברי יואל', 'ויואל משה',
    'עטרת ישועה', 'קדושת ציון', 'אמרי חיים', 'חתם סופר', 'חת"ם סופר', 'יערות דבש',
    'ברכת פרץ', 'אור החיים', 'כלי יקר', 'אור המאיר', 'תורת המגיד', 'מגיד דבריו ליעקב',
    'עבודת ישראל', 'זכרון זאת', 'ברית שלום', 'שמן הטוב', 'פנים יפות', 'תולדות יעקב יוסף',
    'חסד לאברהם', 'אגרא דכלה', 'צבי לצדיק', 'מחנה אפרים', 'תורת משה', 'דרך חיים',
    'שם משמואל', 'אמרי נועם', 'פרי צדיק', 'ליקוטי מוהר"ן', 'קול שמחה', 'שפע חיים',
    'דברי שמואל', 'אהל משה', 'מנחת אלעזר', 'דרכי צדק', 'בית אהרן', 'אור ישראל',
    'אהבת שלום', 'אמרי פנחס', 'אורח לחיים', 'תפארת יהונתן', 'מנחם ציון', 'מאור עינים',
    'בת עין', 'כתב סופר', 'צמח דוד', 'באר משה', 'אך פרי תבואה', 'בית הלוי',
    'אמת ליעקב', 'מהר"י בעלזא', 'עבודת יששכר', 'דברי יחזקאל', 'מהרי"ד בעלזא',
    'ארן עדת', 'קרן לדוד', 'משך חכמה', 'דברי ישראל', 'תורת אבות', 'בית אברהם',
    'דברי שלום', 'ארץ צבי', 'שיר ידידות', 'שיר חדש', 'טיב לבב', 'תורת אמת',
    'מגן אברהם', 'ייטב לב', 'ישמח ישראל', 'קדושת יום טוב', 'ערוגת הבשם',
    'של"ה – דרך חיים תוכחת מוסר', 'תורת משה – אלשי"ך', 'חת"ם סופר – תורת משה'
]

def extract_text_from_docx(docx_path):
    with zipfile.ZipFile(docx_path, 'r') as z:
        xml_content = z.read('word/document.xml').decode('utf-8')
    text = re.sub(r'</w:p>', '\n', xml_content)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&')
    text = text.replace('&lt;', '<').replace('&gt;', '>')
    return text

def clean_html(text):
    return re.sub(r'<[^>]+>', '', text).strip()

def parse_document(lines):
    """Parse document by joining multi-line entries."""
    entries = []
    current_sefer = "דגל מחנה אפרים"  # Default for orphan entries
    entry_id = 0
    
    # Page pattern at end of line: dots followed by Hebrew page number
    # Matches: ט"ו, כ"א, ל"ב, 'כ, כ', ב"י, etc.
    page_end_pattern = re.compile(r'\.{2,}\s*([א-ת]?\'[א-ת]?|[א-ת]+\"[א-ת])\s*$')
    
    # Sefer header pattern - both <center><b> and <center><h1>
    sefer_pattern = re.compile(r'^<center>(?:<h1>)?(?:<b>)?([^<]+)(?:</b>)?(?:</h1>)?</center>$')
    
    # Entry start pattern: <b>verse</b>- or verse- (Hebrew word followed by dash)
    entry_start_pattern = re.compile(r'^(<b>[^<]+</b>|[א-ת][א-ת\s\'\"]+?)\s*[-–]')
    
    # TOC pattern (sefer name with dots and page)
    toc_pattern = re.compile(r'^<b>[^<]+</b>\.{5,}')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Skip TOC entries
        if toc_pattern.match(line):
            i += 1
            continue
        
        # Check for sefer header
        sefer_match = sefer_pattern.match(line)
        if sefer_match:
            sefer_name = sefer_match.group(1).strip()
            # Clean up name
            sefer_name = re.sub(r'<[^>]+>', '', sefer_name).strip()
            for s in SEFORIM:
                if s in sefer_name or sefer_name in s:
                    current_sefer = sefer_name
                    break
            else:
                # If not in list but looks like a sefer header, use it anyway
                if len(sefer_name) > 2 and len(sefer_name) < 50:
                    current_sefer = sefer_name
            i += 1
            continue
        
        # Check if line starts an entry
        entry_match = entry_start_pattern.match(line)
        if entry_match:
            # Collect all lines until we find one ending with page ref
            full_text = line
            j = i + 1
            
            # Check if current line already has page ref
            if not page_end_pattern.search(line):
                # Accumulate lines until we find page reference
                while j < len(lines) and j < i + 10:  # Max 10 lines lookahead
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    
                    # Stop if we hit a new entry or sefer header
                    if sefer_pattern.match(next_line) or (entry_start_pattern.match(next_line) and page_end_pattern.search(next_line)):
                        break
                    
                    full_text += ' ' + next_line
                    
                    # Check if this line ends with page ref
                    if page_end_pattern.search(next_line):
                        j += 1
                        break
                    j += 1
            
            # Try to parse the complete entry
            page_match = page_end_pattern.search(full_text)
            if page_match:
                page = page_match.group(1)
                content = page_end_pattern.sub('', full_text).strip()
                
                # Split into verse and summary
                # Pattern: <b>verse</b>-summary or verse-summary
                parts_match = re.match(r'^(<b>([^<]+)</b>|([א-ת][א-ת\s\'\"א"י]+?))\s*[-–]\s*(.+)$', content)
                if parts_match:
                    if parts_match.group(2):
                        verse = clean_html(parts_match.group(2))
                    else:
                        verse = parts_match.group(3).strip() if parts_match.group(3) else ""
                    summary = clean_html(parts_match.group(4))
                    
                    if verse and summary and len(verse) < 60:
                        entry_id += 1
                        entries.append({
                            'id': entry_id,
                            'sefer': current_sefer,
                            'verse': verse,
                            'summary': summary,
                            'page': page
                        })
            
            i = j
        else:
            i += 1
    
    return entries

def generate_html(entries):
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
            margin-bottom: 20px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .quote-header {
            display: flex;
            gap: 15px;
            margin-bottom: 10px;
            font-weight: bold;
            border-bottom: 1px solid #eee;
            padding-bottom: 8px;
        }
        .quote-text { text-align: justify; line-height: 2; }
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
'''
    
    seforim_groups = {}
    for entry in entries:
        sefer = entry['sefer']
        if sefer not in seforim_groups:
            seforim_groups[sefer] = []
        seforim_groups[sefer].append(entry)
    
    for sefer, group in seforim_groups.items():
        html += f'        <div class="sefer-header">{sefer}</div>\n'
        for entry in group:
            html += f'''        <div class="summary-entry">
            <span class="entry-id">[{entry['id']}]</span>
            <span class="entry-verse">{entry['verse']}</span>
            <span class="entry-summary">{entry['summary']}</span>
            <span class="entry-page">{entry['page']}</span>
        </div>
'''
    
    html += '''    </section>
    
    <div class="divider"></div>
    
    <section>
        <div class="source-header">מקור השפע</div>
'''
    
    current_sefer = None
    for entry in entries:
        if entry['sefer'] != current_sefer:
            current_sefer = entry['sefer']
            html += f'        <div class="sefer-header">{current_sefer}</div>\n'
        
        html += f'''        <div class="quote-entry">
            <div class="quote-header">
                <span>[{entry['id']}]</span>
                <span>{entry['verse']}</span>
                <span>עמ' {entry['page']}</span>
            </div>
            <div class="quote-text">{entry['summary']}</div>
        </div>
'''
    
    html += '''    </section>
</body>
</html>'''
    
    return html

def main():
    print("Extracting text from DOCX...")
    text = extract_text_from_docx(DOCX_PATH)
    print(f"Extracted {len(text)} characters")
    
    lines = [l for l in text.split('\n')]  # Keep all lines including empty
    print(f"Loaded {len(lines)} lines")
    
    print("Parsing document structure...")
    entries = parse_document(lines)
    print(f"Found {len(entries)} entries")
    
    if entries:
        print("\nSample entries:")
        for entry in entries[:15]:
            print(f"  [{entry['id']}] {entry['sefer']}: {entry['verse']} → {entry['page']}")
    
    print("\nGenerating HTML output...")
    html = generate_html(entries)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Output saved to: {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
