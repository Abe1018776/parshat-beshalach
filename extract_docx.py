import zipfile
import re
import os
import sys
import io

# Set stdout to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Get the docx files in directory
dir_path = r'C:\Users\Main\yanky fridman'
files = os.listdir(dir_path)
print("Files found:", files)

# Find the specific docx file
docx_file = None
for f in files:
    if 'בשלח' in f and f.endswith('.docx'):
        docx_file = os.path.join(dir_path, f)
        print(f"Found docx: {f}")
        break

if not docx_file:
    print("No docx file found")
    sys.exit(1)

# Extract text from docx
with zipfile.ZipFile(docx_file, 'r') as z:
    xml_content = z.read('word/document.xml').decode('utf-8')

# Extract text from w:t tags, preserving paragraph breaks
# Find paragraph markers and text
paragraphs = re.findall(r'<w:p[^>]*>.*?</w:p>', xml_content, re.DOTALL)

all_text = []
for para in paragraphs:
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', para)
    if texts:
        all_text.append(''.join(texts))

full_text = '\n'.join(all_text)

# Write output
output_path = os.path.join(dir_path, 'extracted_content.txt')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(full_text)

print(f"Written {len(full_text)} characters to {output_path}")
print("\n--- First 5000 chars ---\n")
print(full_text[:5000])
