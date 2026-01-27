# -*- coding: utf-8 -*-
import re
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Read the extracted content
with open(r'C:\Users\Main\yanky fridman\extracted_content.txt', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# Define book names (seforim) from the index
SEFORIM = [
    'רבינו בחיי',
    'של״ה – דרך חיים תוכחת מוסר',
    'של"ה – דרך חיים תוכחת מוסר',
    'תורת משה – אלשי״ך',
    'תורת משה - אלשי״ך',
    'תורת משה – אלשי"ך',
    'אור המאיר',
    'ערבי נחל',
    'נועם אלימלך',
    'דגל מחנה אפרים',
    'אוהב ישראל',
    'מאור ושמש',
    'אור לשמים',
    'אהבת שלום',
    'אמרי פנחס',
    'אורח לחיים',
    'תפארת יהונתן',
    'מנחם ציון',
    'מאור עינים',
    'זרע קודש',
    'באר מים חיים',
    'קדושת לוי',
    'חת״ם סופר',
    'חת"ם סופר',
    'חת״ם סופר – תורת משה',
    'חת"ם סופר – תורת משה',
    'בת עין',
    'בני יששכר',
    'אגרא דכלה',
    'בארת המים',
    'אמרי נועם',
    'תפארת שלמה',
    'חידושי הרי״ם',
    'חידושי הרי"ם',
    'כתב סופר',
    'צמח דוד',
    'באר משה',
    'אך פרי תבואה',
    'בית הלוי',
    'אמת ליעקב',
    'מהר״י בעלזא',
    'מהר"י בעלזא',
    'עבודת יששכר',
    'עטרת ישועה',
    'שפת אמת',
    'פרי צדיק',
    'דברי יחזקאל',
    'מהרי״ד בעלזא',
    'מהרי"ד בעלזא',
    'ארן עדת',
    'שם משמואל',
    'קרן לדוד',
    'משך חכמה',
    'דברי ישראל',
    'תורת אבות',
    'בית אברהם',
    'דברי שלום',
    'ארץ צבי',
    'שיר ידידות',
    'שיר חדש',
    'טיב לבב',
    'טוב לבב',
    'דברי יואל',
    'תורת אמת',
    'מגן אברהם',
    'ייטב לב',
    'ישמח ישראל',
    'קדושת יום טוב',
    'ערוגת הבשם',
    'צבי לצדיק',
]

# Normalize sefer name
def normalize_sefer(name):
    name = name.strip()
    name = re.sub(r'[״"]', '"', name)
    name = re.sub(r"[׳']", "'", name)
    return name

# Create lookup set
SEFORIM_SET = set(normalize_sefer(s) for s in SEFORIM)

def is_sefer_header(line):
    """Check if a line is a sefer name header"""
    line = line.strip()
    normalized = normalize_sefer(line)
    if normalized in SEFORIM_SET:
        return normalized
    # Check partial match
    for s in SEFORIM_SET:
        if normalized == s or (len(normalized) > 5 and normalized in s) or (len(s) > 5 and s in normalized):
            return s
    return None

# Parse the document
class Entry:
    def __init__(self):
        self.sefer = ""
        self.summary = ""
        self.page = ""
        self.quote = ""
        self.id = 0

# Extract summaries section (pages 4-15 approximately, lines 79-440)
summaries = []
current_sefer = None
in_summary_section = False

for i, line in enumerate(lines):
    # Detect start of summary section
    if 'מפתח ותוכן ענינים' in line:
        in_summary_section = True
        continue
    
    # Detect end of summary section (when actual quotes begin with page markers like "א" at the top)
    if in_summary_section and i > 400 and re.match(r'^[א-ת]$', line.strip()):
        break
    
    if not in_summary_section:
        continue
    
    line = line.strip()
    if not line:
        continue
    
    # Skip page markers
    if re.match(r'^— Page \d+ —$', line):
        continue
    if re.match(r'^בס״ד$', line):
        continue
    
    # Check if this is a sefer header
    sefer = is_sefer_header(line)
    if sefer:
        current_sefer = sefer
        continue
    
    # Parse summary entries (format: "lead text-summary text... page")
    if current_sefer and line:
        # Pattern: "keyword-summary text......page"
        match = re.match(r'^(.+?)-(.+?)\s*\.{2,}\s*([א-ת״׳]+)$', line)
        if not match:
            # Try without dots
            match = re.match(r'^(.+?)-(.+)\s+([א-ת״׳]+)$', line)
        
        if match:
            entry = Entry()
            entry.sefer = current_sefer
            entry.summary = match.group(1).strip() + '-' + match.group(2).strip()
            entry.page = match.group(3).strip()
            summaries.append(entry)
        else:
            # Continuation of previous entry
            if summaries and line:
                # Check if this line ends with a page reference
                page_match = re.search(r'\s*\.{2,}\s*([א-ת״׳]+)$', line)
                if page_match:
                    summaries[-1].summary += ' ' + line[:page_match.start()].strip()
                    summaries[-1].page = page_match.group(1)
                elif re.search(r'\s+([א-ת״׳]+)$', line):
                    page_match = re.search(r'\s+([א-ת״׳]+)$', line)
                    if len(page_match.group(1)) <= 4:  # Short Hebrew page ref
                        summaries[-1].summary += ' ' + line[:page_match.start()].strip()
                        summaries[-1].page = page_match.group(1)
                    else:
                        summaries[-1].summary += ' ' + line
                else:
                    summaries[-1].summary += ' ' + line

# Now extract the full quotes section (starting around line 441)
quotes = []
current_sefer = None
current_quote = []
quote_start_line = 0

# Find where quotes section begins
for i, line in enumerate(lines):
    if 'רבינו בחיי פרשת בשלח' in line or (i > 440 and 'רבינו בחיי' in line and 'פרשת' in line):
        quote_start_line = i
        break

if quote_start_line == 0:
    quote_start_line = 441  # fallback

for i in range(quote_start_line, len(lines)):
    line = lines[i].strip()
    
    if not line:
        continue
    
    # Skip page markers
    if re.match(r'^— Page \d+ —$', line):
        continue
    if re.match(r'^[א-ת]$', line):  # Single Hebrew letter (page number)
        continue
    if re.match(r'^בס״ד$', line):
        continue
    
    # Check for sefer header (usually on its own line or with "פרשת בשלח")
    sefer = is_sefer_header(line.replace('פרשת בשלח', '').strip())
    if sefer:
        # Save previous quote
        if current_sefer and current_quote:
            quote_text = ' '.join(current_quote)
            # Split by paragraph markers if present
            quotes.append({
                'sefer': current_sefer,
                'quote': quote_text
            })
            current_quote = []
        current_sefer = sefer
        continue
    
    # Check for subheader within same sefer
    if line.endswith('הק׳') or line.endswith("הק'"):
        continue
    
    # Add line to current quote
    if current_sefer:
        current_quote.append(line)

# Save last quote
if current_sefer and current_quote:
    quotes.append({
        'sefer': current_sefer,
        'quote': ' '.join(current_quote)
    })

# Match summaries with quotes and assign IDs
for i, entry in enumerate(summaries):
    entry.id = i + 1

# Group by sefer
grouped = {}
for entry in summaries:
    if entry.sefer not in grouped:
        grouped[entry.sefer] = []
    grouped[entry.sefer].append(entry)

# Generate HTML output matching the PDF design
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
            font-family: 'Frank Ruehl', 'David', 'Times New Roman', serif;
            font-size: 14px;
            line-height: 1.6;
            direction: rtl;
            text-align: justify;
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
            color: #000;
        }
        .page-header {
            display: flex;
            justify-content: space-between;
            border-bottom: 1px solid #000;
            padding-bottom: 5px;
            margin-bottom: 20px;
            font-size: 12px;
        }
        .divider {
            text-align: center;
            margin: 20px 0;
            font-weight: bold;
        }
        h1 {
            text-align: center;
            font-size: 24px;
            margin: 30px 0 10px 0;
        }
        h2 {
            text-align: center;
            font-size: 20px;
            margin: 10px 0 20px 0;
        }
        h3 {
            font-size: 18px;
            font-weight: bold;
            margin: 25px 0 15px 0;
            text-align: center;
        }
        h4 {
            font-size: 16px;
            font-weight: bold;
            margin: 20px 0 10px 0;
            border-bottom: 1px solid #000;
            padding-bottom: 5px;
        }
        .index-entry {
            margin: 8px 0;
            text-indent: -20px;
            padding-right: 20px;
        }
        .index-ref {
            color: #444;
            font-size: 12px;
        }
        .quote-section {
            margin-top: 40px;
            page-break-before: always;
        }
        .mekor-hashefa {
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            margin: 30px 0 20px 0;
            border-top: 1px solid #000;
            border-bottom: 1px solid #000;
            padding: 10px 0;
        }
        .quote-block {
            margin: 15px 0;
            padding: 10px 0;
            border-bottom: 1px dotted #ccc;
        }
        .quote-header {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .quote-text {
            text-align: justify;
        }
        .fn-num {
            font-weight: bold;
            color: #333;
        }
        .fn-sefer {
            font-weight: bold;
        }
        .page-break {
            page-break-after: always;
        }
    </style>
</head>
<body>
    <h1>ליקוטי ספרי חסידות</h1>
    <h2>פרשת בשלח</h2>
    
    <div class="divider">═══════════════════════════════════════</div>
    
    <h3>מפתח ענינים</h3>
'''

# Add index entries grouped by sefer
for sefer in grouped:
    html += f'    <h4>{sefer}</h4>\n'
    for entry in grouped[sefer]:
        summary = entry.summary.replace('-', ' - ')
        html += f'    <div class="index-entry">{summary} <span class="index-ref">[{entry.id}]</span></div>\n'

html += '''
    <div class="quote-section">
        <div class="mekor-hashefa">מקור השפע</div>
'''

# Build a map of sefer to quotes
sefer_quotes = {}
for q in quotes:
    s = normalize_sefer(q['sefer'])
    if s not in sefer_quotes:
        sefer_quotes[s] = []
    sefer_quotes[s].append(q['quote'])

# Add full quotes
for i, entry in enumerate(summaries):
    page = entry.page if entry.page else 'א׳'
    
    # Try to find matching full quote
    full_quote = entry.summary  # Default to summary
    sefer_key = normalize_sefer(entry.sefer)
    
    # Look for a quote that starts with similar text
    if sefer_key in sefer_quotes and sefer_quotes[sefer_key]:
        # Use next available quote for this sefer
        full_quote = sefer_quotes[sefer_key].pop(0) if sefer_quotes[sefer_key] else entry.summary
    
    html += f'''        <div class="quote-block">
            <div class="quote-header">
                <span class="fn-num">[{entry.id}]</span> 
                <span class="fn-sefer">({entry.sefer}, עמוד {page})</span>
            </div>
            <div class="quote-text">{full_quote}</div>
        </div>
'''

html += '''    </div>
</body>
</html>
'''

# Write output
output_path = r'C:\Users\Main\yanky fridman\parshat_beshalach_output.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Generated output: {output_path}")
print(f"Total summaries found: {len(summaries)}")
print(f"Seforim found: {len(grouped)}")
for sefer in grouped:
    print(f"  - {sefer}: {len(grouped[sefer])} entries")
