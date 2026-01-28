"""
OCR the summaries index PDF using Gemini 2.5 Pro via OpenRouter.
Converts PDF pages to images and sends them to Gemini for text extraction.
"""

import base64
import json
import requests
import fitz  # PyMuPDF
from pathlib import Path
import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration
OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY_HERE"
PDF_PATH = r"C:\Users\Main\yanky fridman\בשלח_pages_4_to_14.pdf"
OUTPUT_PATH = r"C:\Users\Main\yanky fridman\summaries_index_ocr.json"

def pdf_to_images(pdf_path):
    """Convert PDF pages to base64 encoded images."""
    doc = fitz.open(pdf_path)
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        # Render at 2x resolution for better OCR quality
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        images.append({
            'page': page_num + 1,
            'base64': img_base64
        })
        print(f"Converted page {page_num + 1}/{len(doc)}")

    doc.close()
    return images

def ocr_with_gemini(image_base64, page_num, max_retries=3):
    """Send image to Gemini 2.5 Pro via OpenRouter for OCR."""
    import time

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "PDF OCR Script"
    }

    payload = {
        "model": "google/gemini-3-pro-preview",
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
                        "text": """Please perform OCR on this Hebrew text image. This is an index/table of contents for Torah summaries (תוכן עניינים).

Extract ALL text exactly as it appears, preserving:
1. The structure (numbered entries, indentation)
2. Hebrew text accurately
3. Page numbers or references
4. Any section headers or categories

Output the text in a structured format. For each entry, try to identify:
- The entry number/index
- The title/description (Hebrew)
- Any verse references (פסוקים)
- Page numbers if visible

Be thorough and accurate - this will be used to match summaries to their correct locations."""
                    }
                ]
            }
        ],
        "max_tokens": 8000,
        "temperature": 0.1
    }

    for attempt in range(max_retries):
        try:
            print(f"Sending page {page_num} to Gemini 2.5 Pro... (attempt {attempt + 1})")
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
    print(f"Processing PDF: {PDF_PATH}")

    # Step 1: Convert PDF to images
    print("\n=== Converting PDF to images ===")
    images = pdf_to_images(PDF_PATH)
    print(f"Converted {len(images)} pages to images")

    # Step 2: OCR each page with Gemini
    print("\n=== Running OCR with Gemini 2.5 Pro ===")
    results = []
    for img_data in images:
        result = ocr_with_gemini(img_data['base64'], img_data['page'])
        results.append(result)

        # Save partial results after each page
        partial_output = {
            "source_pdf": PDF_PATH,
            "total_pages": len(images),
            "completed_pages": len(results),
            "pages": results
        }
        with open(OUTPUT_PATH.replace('.json', '_partial.json'), 'w', encoding='utf-8') as f:
            json.dump(partial_output, f, ensure_ascii=False, indent=2)
        print(f"Partial results saved ({len(results)}/{len(images)} pages)")

    # Step 3: Save results
    print("\n=== Saving results ===")
    output = {
        "source_pdf": PDF_PATH,
        "total_pages": len(images),
        "pages": results
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Results saved to: {OUTPUT_PATH}")

    # Also save as plain text for easy reading
    text_output = OUTPUT_PATH.replace('.json', '.txt')
    with open(text_output, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(f"\n{'='*60}\n")
            f.write(f"PAGE {result.get('page', '?')}\n")
            f.write(f"{'='*60}\n\n")
            if 'text' in result:
                f.write(result['text'])
            elif 'error' in result:
                f.write(f"ERROR: {result['error']}")
            f.write("\n")

    print(f"Text version saved to: {text_output}")

    return results

if __name__ == "__main__":
    main()
