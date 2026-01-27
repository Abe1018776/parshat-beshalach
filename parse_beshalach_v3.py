# -*- coding: utf-8 -*-
import zipfile
import re
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Use relative paths
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

def clean_html(text):
    """Remove HTML tags from text."""
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def parse_document(lines):
    """Parse the document into structured sections."""
    entries = []
    current_sefer = None
    entry_id = 0
    in_toc = True  # Start in table of contents
    
    # Page format: Hebrew letters like י"ז, כ"א, ל"ב, 'כ, ב"י, י"א
    page_pattern = r"([א-ת]?'[א-ת]|[א-ת]+\"[א-ת])"
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Skip table of contents entries (book name followed by dots and page)
        if re.match(r'^<b>[^<]+</b>\.{5,}', line):
            continue
        
        # Check for sefer header: <center><b>ספר</b></center>
        sefer_match = re.match(r'^<center><b>([^<]+)</b></center>$', line)
        if sefer_match:
            sefer_name = sefer_match.group(1).strip()
            # Verify it's a known sefer
            for s in SEFORIM:
                if s in sefer_name or sefer_name in s:
                    current_sefer = sefer_name
                    in_toc = False  # Left table of contents
                    break
            continue
        
        # Skip if still in TOC or no sefer set
        if in_toc or not current_sefer:
            # But check if line has entry pattern to exit TOC
            if re.match(r'^<b>[^<]+</b>\s*[-–]', line):
                in_toc = False
            else:
                continue
        
        # Check for summary entry: <b>פסוק</b>-תוכן......page
        # Pattern 1: <b>verse</b>-summary...page
        entry_match = re.match(r'^<b>([^<]+)</b>\s*[-–]\s*(.+?)\.{2,}\s*(' + page_pattern + r')\s*$', line)
        if entry_match:
            entry_id += 1
            verse = clean_html(entry_match.group(1))
            summary = clean_html(entry_match.group(2))
            page = entry_match.group(3)
            entries.append({
                'id': entry_id,
                'sefer': current_sefer,
                'verse': verse,
                'summary': summary,
                'page': page
            })
            continue
        
        # Pattern 2: verse-summary...page (no HTML tags)
        entry_match2 = re.match(r'^([א-ת][א-ת\s\'\"]+?)\s*[-–]\s*(.+?)\.{2,}\s*(' + page_pattern + r')\s*$', line)
        if entry_match2:
            verse = entry_match2.group(1).strip()
            summary = entry_match2.group(2).strip()
            page = entry_match2.group(3)
            # Validate: verse should be short, summary longer
            if 2 <= len(verse) <= 50 and len(summary) > 15:
                entry_id += 1
                entries.append({
                    'id': entry_id,
                    'sefer': current_sefer,
                    'verse': verse,
                    'summary': summary,
                    'page': page
                })
                continue
    
    return entries

def generate_html(entries):
    """Generate HTML output matching the target PDF format."""
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
        .parsha-name { font-weight: bold; font-size: 16pt; }
        .summary-section { margin-bottom: 30px; }
        .summary-entry {
            display: flex;
            align-items: baseline;
            margin: 8px 0;
            gap: 10px;
        }
        .entry-id {
            font-weight: bold;
            min-width: 30px;
        }
        .entry-verse {
            font-weight: bold;
            color: #333;
        }
        .entry-summary { flex: 1; }
        .entry-page {
            font-weight: bold;
            min-width: 40px;
            text-align: left;
        }
        .divider {
            border-top: 2px solid #000;
            margin: 30px 0;
        }
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
        .quote-text {
            text-align: justify;
            line-height: 2;
        }
        h1 { text-align: center; margin-bottom: 5px; }
        h2 { text-align: center; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>ליקוטי ספרי חסידות</h1>
    <h2>פרשת בשלח</h2>
    
    <div class="divider"></div>
    
    <!-- מפתח ענינים - Summary Index -->
    <section class="summary-section">
        <div class="source-header">מפתח ענינים</div>
'''
    
    # Group entries by sefer
    seforim_groups = {}
    for entry in entries:
        sefer = entry['sefer']
        if sefer not in seforim_groups:
            seforim_groups[sefer] = []
        seforim_groups[sefer].append(entry)
    
    # Generate summary index
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
    
    <!-- מקור השפע - Full Quotes Section -->
    <section>
        <div class="source-header">מקור השפע</div>
'''
    
    # Generate full quotes section
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
    
    # Parse directly from extracted text
    clean_lines = [l.strip() for l in text.split('\n') if l.strip()]
    print(f"Loaded {len(clean_lines)} lines")
    
    print("Parsing document structure...")
    entries = parse_document(clean_lines)
    print(f"Found {len(entries)} entries")
    
    if entries:
        print("\nSample entries:")
        for entry in entries[:10]:
            print(f"  [{entry['id']}] {entry['sefer']}: {entry['verse']} → {entry['page']}")
    
    print("\nGenerating HTML output...")
    html = generate_html(entries)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Output saved to: {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
