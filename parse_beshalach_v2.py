# -*- coding: utf-8 -*-
import zipfile
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DOCX_PATH = r"C:\Users\Main\yanky fridman\ocr-172a161e-b608-46df-83ec-5db88688b475.docx"
OUTPUT_PATH = r"C:\Users\Main\yanky fridman\beshalach_output_v2.html"

def extract_text_from_docx(docx_path):
    """Extract text content from docx by reading the XML."""
    with zipfile.ZipFile(docx_path, 'r') as z:
        xml_content = z.read('word/document.xml').decode('utf-8')
    
    # Remove XML tags but preserve paragraph breaks
    text = re.sub(r'</w:p>', '\n', xml_content)
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up entities
    text = text.replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&')
    text = text.replace('&lt;', '<').replace('&gt;', '>')
    return text

def parse_document(text):
    """Parse the document into structured sections."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # Known seforim names
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
        'דברי שמואל', 'אהל משה', 'מנחת אלעזר', 'דרכי צדק', 'בית אהרן', 'אור ישראל'
    ]
    
    entries = []
    current_sefer = None
    current_entry = None
    in_summary_section = True
    summary_entries = []
    quote_entries = []
    
    # Pattern for summary line: <b>פסוק</b>-תוכן......... דף
    summary_pattern = re.compile(r'^(.+?)\s*[-–]\s*(.+?)\s*\.{2,}\s*([א-ת]+"?[א-ת]?|[א-ת]\'?)$')
    
    # Pattern for page reference at end of line
    page_ref_pattern = re.compile(r'\.{2,}\s*([א-ת]+"?[א-ת]?|[א-ת]\'?)\s*$')
    
    # Pattern to detect sefer header (centered bold sefer name)
    sefer_header_pattern = re.compile(r'^(' + '|'.join(re.escape(s) for s in SEFORIM) + r')$')
    
    entry_id = 0
    
    for i, line in enumerate(lines):
        # Check if this is a sefer header
        for sefer in SEFORIM:
            if sefer in line and len(line) < len(sefer) + 20:
                if line.strip() == sefer or line.replace(' ', '') == sefer.replace(' ', ''):
                    current_sefer = sefer
                    break
        
        # Check for summary pattern (verse-summary......page)
        match = summary_pattern.match(line)
        if match and current_sefer:
            entry_id += 1
            verse = match.group(1).strip()
            summary = match.group(2).strip()
            page = match.group(3).strip()
            
            summary_entries.append({
                'id': entry_id,
                'sefer': current_sefer,
                'verse': verse,
                'summary': summary,
                'page': page,
                'full_quote': ''
            })
            continue
        
        # Check for page ref at end (could be part of summary)
        page_match = page_ref_pattern.search(line)
        if page_match and '-' in line and current_sefer:
            parts = line.split('-', 1)
            if len(parts) == 2:
                verse = parts[0].strip()
                rest = parts[1].strip()
                summary = page_ref_pattern.sub('', rest).strip()
                page = page_match.group(1)
                
                if verse and summary:
                    entry_id += 1
                    summary_entries.append({
                        'id': entry_id,
                        'sefer': current_sefer,
                        'verse': verse,
                        'summary': summary,
                        'page': page,
                        'full_quote': ''
                    })
    
    # Second pass: extract full quotes
    current_sefer = None
    current_quote_lines = []
    
    for i, line in enumerate(lines):
        # Check for sefer name as header for quotes section
        for sefer in SEFORIM:
            if sefer in line and len(line) < len(sefer) + 30:
                # Save previous quote if exists
                if current_sefer and current_quote_lines:
                    quote_text = '\n'.join(current_quote_lines)
                    quote_entries.append({
                        'sefer': current_sefer,
                        'text': quote_text
                    })
                current_sefer = sefer
                current_quote_lines = []
                break
        else:
            # Not a header, accumulate quote text
            if current_sefer and line and not summary_pattern.match(line):
                # Skip table of contents lines
                if not re.match(r'^\.{5,}', line) and not line.startswith('דף'):
                    current_quote_lines.append(line)
    
    # Save last quote
    if current_sefer and current_quote_lines:
        quote_text = '\n'.join(current_quote_lines)
        quote_entries.append({
            'sefer': current_sefer,
            'text': quote_text
        })
    
    # Match quotes to summaries by sefer name
    for entry in summary_entries:
        for quote in quote_entries:
            if quote['sefer'] == entry['sefer']:
                # Check if verse appears in quote text
                if entry['verse'] in quote['text']:
                    entry['full_quote'] = quote['text']
                    break
    
    return summary_entries

def generate_html(entries):
    """Generate HTML output matching the target PDF format."""
    html = '''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>פרשת בשלח - ליקוטי ספרי חסידות</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
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
        .page {
            page-break-after: always;
            min-height: 90vh;
            display: flex;
            flex-direction: column;
        }
        .page-header {
            display: flex;
            justify-content: space-between;
            border-bottom: 2px solid #000;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .parsha-name {
            font-weight: bold;
            font-size: 16pt;
        }
        .page-num {
            font-size: 14pt;
        }
        .summary-section {
            flex: 0 0 auto;
            margin-bottom: 30px;
        }
        .summary-title {
            font-weight: bold;
            font-size: 15pt;
            margin-bottom: 10px;
        }
        .summary-text {
            font-size: 13pt;
            margin-bottom: 15px;
        }
        .divider {
            border-top: 1px solid #000;
            margin: 20px 0;
        }
        .source-header {
            text-align: center;
            font-weight: bold;
            font-size: 16pt;
            margin: 20px 0;
        }
        .quote-section {
            flex: 1;
        }
        .quote-entry {
            margin-bottom: 25px;
        }
        .quote-number {
            font-weight: bold;
            font-size: 14pt;
            margin-left: 10px;
        }
        .quote-source {
            font-weight: bold;
            font-size: 13pt;
            color: #333;
        }
        .quote-text {
            font-size: 13pt;
            text-align: justify;
            margin-top: 5px;
        }
        .sefer-header {
            text-align: center;
            font-weight: bold;
            font-size: 18pt;
            margin: 30px 0 20px 0;
            border-bottom: 1px solid #ccc;
            padding-bottom: 10px;
        }
        .index-section {
            margin-bottom: 40px;
        }
        .index-entry {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
        }
        .index-verse {
            font-weight: bold;
        }
        .index-summary {
            flex: 1;
            margin: 0 20px;
        }
        .index-page {
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1 style="text-align: center;">ליקוטי ספרי חסידות</h1>
    <h2 style="text-align: center;">פרשת בשלח</h2>
    <div class="divider"></div>
    
    <!-- מפתח ענינים - Summary Index -->
    <section class="index-section">
        <h2 style="text-align: center;">מפתח ענינים</h2>
'''
    
    # Group entries by sefer for index
    seforim_groups = {}
    for entry in entries:
        sefer = entry['sefer']
        if sefer not in seforim_groups:
            seforim_groups[sefer] = []
        seforim_groups[sefer].append(entry)
    
    # Generate index section
    for sefer, group in seforim_groups.items():
        html += f'        <div class="sefer-header">{sefer}</div>\n'
        for entry in group:
            html += f'''        <div class="index-entry">
            <span class="index-verse">{entry['verse']}</span>
            <span class="index-summary">{entry['summary']}</span>
            <span class="index-page">[{entry['id']}] {entry['page']}</span>
        </div>
'''
    
    html += '''    </section>
    
    <div class="divider"></div>
    
    <!-- מקור השפע - Full Quotes Section -->
    <section>
        <h2 class="source-header">מקור השפע</h2>
'''
    
    # Generate full quotes section
    current_sefer = None
    for entry in entries:
        if entry['sefer'] != current_sefer:
            current_sefer = entry['sefer']
            html += f'        <div class="sefer-header">{current_sefer}</div>\n'
        
        quote_text = entry['full_quote'] if entry['full_quote'] else entry['summary']
        html += f'''        <div class="quote-entry">
            <span class="quote-number">[{entry['id']}]</span>
            <span class="quote-source">{entry['verse']} - {entry['page']}</span>
            <div class="quote-text">{quote_text}</div>
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
    
    # Save extracted text for debugging
    with open(r"C:\Users\Main\yanky fridman\extracted_beshalach.txt", 'w', encoding='utf-8') as f:
        f.write(text)
    print("Saved extracted text to extracted_beshalach.txt")
    
    print("Parsing document structure...")
    entries = parse_document(text)
    print(f"Found {len(entries)} entries")
    
    print("Generating HTML output...")
    html = generate_html(entries)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Output saved to: {OUTPUT_PATH}")
    print("\nSample entries:")
    for entry in entries[:5]:
        print(f"  [{entry['id']}] {entry['sefer']}: {entry['verse']} - {entry['page']}")

if __name__ == '__main__':
    main()
