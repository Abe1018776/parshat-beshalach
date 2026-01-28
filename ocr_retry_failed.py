"""
Retry OCR for failed pages using Gemini Flash (more reliable for OCR).
"""

import base64
import json
import requests
import fitz  # PyMuPDF
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY_HERE"
PDF_PATH = r"C:\Users\Main\yanky fridman\בשלח_pages_4_to_14.pdf"
EXISTING_RESULTS = r"C:\Users\Main\yanky fridman\summaries_index_ocr.json"
OUTPUT_PATH = r"C:\Users\Main\yanky fridman\summaries_index_ocr_complete.json"

# Pages that failed (empty or thinking output)
FAILED_PAGES = [1, 2, 3, 5, 7, 9, 11]

def pdf_page_to_image(pdf_path, page_num):
    """Convert a single PDF page to base64 encoded image."""
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]  # 0-indexed
    mat = fitz.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    doc.close()
    return img_base64

def ocr_with_gemini_flash(image_base64, page_num, max_retries=3):
    """Send image to Gemini Flash via OpenRouter for OCR."""

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "PDF OCR Script"
    }

    # Simpler, more direct prompt for Gemini Flash
    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": """OCR this Hebrew text image completely. Extract ALL text exactly as written.

This is a table of contents (תוכן עניינים) for Torah commentaries.

Output format:
- Preserve section headers (like book names)
- For each entry: the key phrase (in bold like **text**) followed by the summary text
- Include page numbers (like נ"ב or ע"ה at the end of entries)

Extract everything visible, including both columns if present. Do not summarize or paraphrase - output the exact text."""
                    }
                ]
            }
        ],
        "max_tokens": 8000,
        "temperature": 0
    }

    for attempt in range(max_retries):
        try:
            print(f"Sending page {page_num} to Gemini Flash... (attempt {attempt + 1})")
            response = requests.post(url, headers=headers, json=payload, timeout=180)

            if response.status_code != 200:
                print(f"Error on page {page_num}: {response.status_code}")
                print(response.text)
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                return {"error": response.text, "page": page_num}

            result = response.json()
            content = result['choices'][0]['message']['content']

            # Check if result is too short (likely failed)
            if len(content.strip()) < 100:
                print(f"Page {page_num}: Response too short ({len(content)} chars), retrying...")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue

            print(f"Page {page_num} OCR complete ({len(content)} chars)")
            return {"page": page_num, "text": content}

        except Exception as e:
            print(f"Error on page {page_num}: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in 5 seconds...")
                time.sleep(5)
            else:
                return {"error": str(e), "page": page_num}

    return {"error": "Max retries exceeded", "page": page_num}

def main():
    # Load existing results
    print("Loading existing results...")
    with open(EXISTING_RESULTS, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create a dict for easy lookup
    results_dict = {p['page']: p for p in data['pages']}

    print(f"\nRetrying failed pages: {FAILED_PAGES}")
    print("=" * 60)

    for page_num in FAILED_PAGES:
        print(f"\n--- Processing page {page_num} ---")
        img_base64 = pdf_page_to_image(PDF_PATH, page_num)
        result = ocr_with_gemini_flash(img_base64, page_num)
        results_dict[page_num] = result

        # Save after each page
        updated_pages = [results_dict[i] for i in sorted(results_dict.keys())]
        output = {
            "source_pdf": PDF_PATH,
            "total_pages": len(updated_pages),
            "pages": updated_pages
        }
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"Progress saved to {OUTPUT_PATH}")

        time.sleep(2)  # Rate limiting

    # Save final text version
    print("\n" + "=" * 60)
    print("Saving final text version...")

    text_output = OUTPUT_PATH.replace('.json', '.txt')
    with open(text_output, 'w', encoding='utf-8') as f:
        for page_num in sorted(results_dict.keys()):
            result = results_dict[page_num]
            f.write(f"\n{'='*60}\n")
            f.write(f"PAGE {result.get('page', '?')}\n")
            f.write(f"{'='*60}\n\n")
            if 'text' in result:
                f.write(result['text'])
            elif 'error' in result:
                f.write(f"ERROR: {result['error']}")
            f.write("\n")

    print(f"Text version saved to: {text_output}")
    print("\nDone!")

if __name__ == "__main__":
    main()
