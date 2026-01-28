# -*- coding: utf-8 -*-
"""
Advanced Parser: Map Authors -> Summaries -> Content
For Likutei Sifrei Chassidus documents

Strategy:
1. Extract all author names from main TOC
2. Extract all summaries grouped by author
3. Extract actual content sections with page markers
4. Map summaries to content using: opening words + page numbers + author context
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher

@dataclass
class Summary:
    author: str
    opening_words: str  # The bold text at start (verse/topic reference)
    summary_text: str   # The actual summary
    page_ref: str       # Hebrew page number (e.g., י"ז)
    line_number: int
    matched_content: Optional['ContentSection'] = None
    match_confidence: float = 0.0

@dataclass
class ContentSection:
    author: str
    text: str
    page_number: str  # From footer
    start_line: int
    end_line: int
    opening_phrases: List[str] = field(default_factory=list)  # First few words of paragraphs

@dataclass
class Author:
    name: str
    page_start: str  # Hebrew page number
    summaries: List[Summary] = field(default_factory=list)
    content_sections: List[ContentSection] = field(default_factory=list)


def hebrew_page_to_int(page: str) -> int:
    """Convert Hebrew page number to integer for comparison"""
    hebrew_nums = {
        'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9,
        'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90,
        'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400
    }
    # Clean up the page string
    page = page.replace("'", "").replace('"', '').replace(' ', '')
    total = 0
    for char in page:
        if char in hebrew_nums:
            total += hebrew_nums[char]
    return total


def normalize_text(text: str) -> str:
    """Normalize Hebrew text for comparison"""
    # Remove nikud, punctuation, extra spaces
    text = re.sub(r'[\u0591-\u05C7]', '', text)  # Remove nikud
    text = re.sub(r'[.,;:!?\-\u2013\u2014]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def similarity_score(a: str, b: str) -> float:
    """Calculate similarity between two strings"""
    a_norm = normalize_text(a)
    b_norm = normalize_text(b)
    return SequenceMatcher(None, a_norm, b_norm).ratio()


def extract_opening_words(text: str, num_words: int = 5) -> str:
    """Extract first N words from text"""
    words = normalize_text(text).split()[:num_words]
    return ' '.join(words)


class DocumentParser:
    def __init__(self, content: str):
        self.lines = content.split('\n')
        self.content = content
        self.authors: Dict[str, Author] = {}
        self.summaries: List[Summary] = []
        self.content_sections: List[ContentSection] = []

    def parse(self):
        """Main parsing pipeline"""
        print("Step 1: Extracting authors from TOC...")
        self._extract_authors_from_toc()

        print("Step 2: Extracting summaries...")
        self._extract_summaries()

        print("Step 3: Extracting content sections...")
        self._extract_content_sections()

        print("Step 4: Mapping summaries to content...")
        self._map_summaries_to_content()

        return self

    def _extract_authors_from_toc(self):
        """Extract author names and page numbers from main TOC (lines 15-75 approx)"""
        # Pattern: <b>Author Name</b>......'page
        toc_pattern = re.compile(r'<b>([^<]+)</b>\.+\s*([\'"]?[א-ת"\']+)')

        for i, line in enumerate(self.lines[:100]):  # TOC is in first 100 lines
            match = toc_pattern.search(line)
            if match and i >= 14:  # Skip header lines
                author_name = match.group(1).strip()
                page = match.group(2).strip()
                if author_name not in self.authors:
                    self.authors[author_name] = Author(name=author_name, page_start=page)

        print(f"   Found {len(self.authors)} authors in TOC")

    def _extract_summaries(self):
        """Extract summaries grouped by author from the summary index section"""
        current_author = None
        in_summary_section = False

        # Track multi-line summaries
        current_summary_start = None
        current_summary_opening = None
        current_summary_lines = []

        # Pattern for author headers in summary section
        author_header = re.compile(r'<center><b>([^<]+)</b></center>')
        author_header_h1 = re.compile(r'<center><h1><b>([^<]+)</b></h1></center>')

        # Pattern to detect start of a summary: <b>Opening</b>-
        summary_start_pattern = re.compile(r'^<b>([^<]+)</b>[\-–—](.*)$')

        # Pattern for page number at end of line (dots followed by Hebrew letters)
        page_end_pattern = re.compile(r'\.{2,}\s*([א-ת"\']+)\s*$')

        # Also match page patterns like "כ"א" at end
        page_alt_pattern = re.compile(r'\s+([א-ת][\'"]?[א-ת]?)\s*$')

        # Find where summary section starts (after TOC, before content)
        summary_section_start = 76  # After TOC
        content_start = 0
        for i, line in enumerate(self.lines):
            if '<header>' in line.lower() and 'רבינו בחיי' in line and i > 400:
                content_start = i
                break

        if content_start == 0:
            content_start = len(self.lines)

        def save_current_summary():
            nonlocal current_summary_start, current_summary_opening, current_summary_lines
            if current_summary_opening and current_summary_lines:
                full_text = ' '.join(current_summary_lines)
                # Extract page number from end
                page_match = page_end_pattern.search(full_text)
                if page_match:
                    page = page_match.group(1).strip()
                    text = full_text[:page_match.start()].strip()
                else:
                    # Try alternative pattern
                    page_match = page_alt_pattern.search(full_text)
                    if page_match:
                        page = page_match.group(1).strip()
                        text = full_text[:page_match.start()].strip()
                    else:
                        page = ''
                        text = full_text

                # Clean up text
                text = re.sub(r'\.{2,}', '', text).strip()

                if current_author and len(text) > 10:  # Skip very short entries
                    summary = Summary(
                        author=current_author,
                        opening_words=current_summary_opening,
                        summary_text=text,
                        page_ref=page,
                        line_number=current_summary_start
                    )
                    self.summaries.append(summary)
                    if current_author in self.authors:
                        self.authors[current_author].summaries.append(summary)

            current_summary_start = None
            current_summary_opening = None
            current_summary_lines = []

        for i, line in enumerate(self.lines[summary_section_start:content_start], start=summary_section_start):
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                continue

            # Check for author header (starts new author section)
            match = author_header.search(line) or author_header_h1.search(line)
            if match:
                # Save any pending summary
                save_current_summary()

                author_name = match.group(1).strip()
                # Find matching author (fuzzy match)
                for name in self.authors:
                    if similarity_score(name, author_name) > 0.8:
                        current_author = name
                        break
                else:
                    current_author = author_name
                    if current_author not in self.authors:
                        self.authors[current_author] = Author(name=current_author, page_start='')
                continue

            # Check for start of new summary
            start_match = summary_start_pattern.match(line_stripped)
            if start_match:
                # Save previous summary if any
                save_current_summary()

                # Start new summary
                current_summary_start = i + 1
                current_summary_opening = start_match.group(1).strip()
                rest = start_match.group(2).strip()
                if rest:
                    current_summary_lines = [rest]
                else:
                    current_summary_lines = []
                continue

            # Continue accumulating current summary
            if current_summary_opening:
                current_summary_lines.append(line_stripped)

        # Save last summary
        save_current_summary()

        print(f"   Found {len(self.summaries)} summaries")

    def _extract_content_sections(self):
        """Extract actual content sections with page markers"""
        current_author = None
        current_text = []
        current_start = 0
        current_page = ''

        # Find where content starts (after summary index)
        content_start = 0
        for i, line in enumerate(self.lines):
            if '<header>' in line.lower() and 'רבינו בחיי' in line and i > 400:
                content_start = i
                break

        if content_start == 0:
            # Fallback: look for first h1 author header
            for i, line in enumerate(self.lines):
                if '<center><h1><b>' in line and i > 400:
                    content_start = i
                    break

        # Multiple patterns for author content headers
        author_patterns = [
            re.compile(r'<center><h1><b>([^<]+)</b></h1></center>'),  # <center><h1><b>Author</b></h1></center>
            re.compile(r'<center><h1>([^<]+)</h1></center>'),  # <center><h1>Author</h1></center>
            re.compile(r'^<header>([^<]+)</header>$'),  # <header>Author</header> (standalone)
        ]

        # Pattern for page footers
        page_footer = re.compile(r'<footer><center>([א-ת"\']+)</center></footer>')

        # Also capture page numbers from footer tags
        page_footer_alt = re.compile(r'<footer>([א-ת"\']+)</footer>')

        def match_author(line: str) -> Optional[str]:
            """Try to match author name from line"""
            for pattern in author_patterns:
                match = pattern.search(line)
                if match:
                    name = match.group(1).strip()
                    # Skip generic headers
                    if name in ['פרשת בשלח', 'בס"ד']:
                        return None
                    return name
            return None

        def find_author_match(name: str) -> str:
            """Find matching author from known authors"""
            for known_name in self.authors:
                if similarity_score(known_name, name) > 0.7:
                    return known_name
            return name

        def save_section():
            nonlocal current_author, current_text, current_start, current_page
            if current_author and current_text:
                text = '\n'.join(current_text)
                if len(text.strip()) > 50:  # Skip very short sections
                    section = ContentSection(
                        author=current_author,
                        text=text,
                        page_number=current_page,
                        start_line=current_start,
                        end_line=i,
                        opening_phrases=self._extract_paragraph_openings(text)
                    )
                    self.content_sections.append(section)
                    if current_author in self.authors:
                        self.authors[current_author].content_sections.append(section)

        for i, line in enumerate(self.lines[content_start:], start=content_start):
            # Check for author header
            author_name = match_author(line)
            if author_name:
                # Save previous section
                save_section()

                # Start new section
                current_author = find_author_match(author_name)
                if current_author not in self.authors:
                    self.authors[current_author] = Author(name=current_author, page_start='')

                current_text = []
                current_start = i
                current_page = ''
                continue

            # Check for page footer
            page_match = page_footer.search(line) or page_footer_alt.search(line)
            if page_match:
                current_page = page_match.group(1).strip()

            # Accumulate text
            if current_author:
                current_text.append(line)

        # Save last section
        i = len(self.lines)
        save_section()

        print(f"   Found {len(self.content_sections)} content sections")

    def _extract_paragraph_openings(self, text: str) -> List[str]:
        """Extract opening words from paragraphs marked with <b> tags"""
        openings = []
        # Find bold text that starts paragraphs
        bold_pattern = re.compile(r'<b>([^<]+)</b>')
        for match in bold_pattern.finditer(text):
            opening = match.group(1).strip()
            if len(opening) > 2:  # Skip very short matches
                openings.append(opening)
        return openings

    def _map_summaries_to_content(self):
        """Map each summary to its corresponding content section - STRICT AUTHOR MATCHING"""
        mapped = 0

        for summary in self.summaries:
            best_match = None
            best_score = 0

            # Get content sections for this author ONLY (strict match)
            author_sections = []
            for section in self.content_sections:
                author_sim = similarity_score(section.author, summary.author)
                # STRICT: Only match if author similarity > 0.7 (same author)
                if author_sim > 0.7:
                    author_sections.append((section, author_sim))

            # NO FALLBACK - if no same-author content, skip this summary
            if not author_sections:
                continue  # Don't match to different author

            for section, author_sim in author_sections:
                score = 0

                # Signal 1: Opening words match (weight: 40%)
                opening_normalized = normalize_text(summary.opening_words)

                # Check opening phrases (bold text in content)
                best_phrase_score = 0
                for phrase in section.opening_phrases:
                    phrase_norm = normalize_text(phrase)
                    # Exact match or containment
                    if opening_normalized == phrase_norm:
                        best_phrase_score = 1.0
                        break
                    elif opening_normalized in phrase_norm:
                        best_phrase_score = max(best_phrase_score, 0.9)
                    elif phrase_norm in opening_normalized:
                        best_phrase_score = max(best_phrase_score, 0.8)
                    else:
                        # Fuzzy match
                        sim = similarity_score(opening_normalized, phrase_norm)
                        if sim > 0.7:
                            best_phrase_score = max(best_phrase_score, sim)

                score += best_phrase_score * 0.4

                # Also check if opening words appear anywhere in content (bonus)
                content_normalized = normalize_text(section.text)
                if opening_normalized in content_normalized:
                    score += 0.15

                # Signal 2: Page number match (weight: 30%)
                if summary.page_ref and section.page_number:
                    summary_page = hebrew_page_to_int(summary.page_ref)
                    section_page = hebrew_page_to_int(section.page_number)
                    page_diff = abs(summary_page - section_page)
                    if page_diff == 0:
                        score += 0.3
                    elif page_diff <= 1:
                        score += 0.2
                    elif page_diff <= 3:
                        score += 0.1

                # Signal 3: Author match (weight: 30%)
                score += author_sim * 0.3

                if score > best_score:
                    best_score = score
                    best_match = section

            if best_match and best_score > 0.25:
                summary.matched_content = best_match
                summary.match_confidence = best_score
                mapped += 1

        print(f"   Mapped {mapped}/{len(self.summaries)} summaries ({100*mapped/len(self.summaries):.1f}%)")

    def get_mapping_report(self) -> str:
        """Generate a report of all mappings"""
        lines = []
        lines.append("=" * 80)
        lines.append("SUMMARY TO CONTENT MAPPING REPORT")
        lines.append("=" * 80)

        for author_name, author in self.authors.items():
            lines.append(f"\n### {author_name} ###")
            lines.append(f"Page start: {author.page_start}")
            lines.append(f"Summaries: {len(author.summaries)}")
            lines.append(f"Content sections: {len(author.content_sections)}")

            for summary in author.summaries:
                status = "MATCHED" if summary.matched_content else "UNMATCHED"
                conf = f"({summary.match_confidence:.0%})" if summary.matched_content else ""
                lines.append(f"\n  [{status}] {conf}")
                lines.append(f"  Opening: {summary.opening_words}")
                lines.append(f"  Summary: {summary.summary_text[:100]}...")
                lines.append(f"  Page ref: {summary.page_ref}")
                if summary.matched_content:
                    lines.append(f"  -> Content page: {summary.matched_content.page_number}")
                    lines.append(f"  -> Lines: {summary.matched_content.start_line}-{summary.matched_content.end_line}")

        # Statistics
        total = len(self.summaries)
        matched = sum(1 for s in self.summaries if s.matched_content)
        high_conf = sum(1 for s in self.summaries if s.match_confidence > 0.7)

        lines.append("\n" + "=" * 80)
        lines.append("STATISTICS")
        lines.append("=" * 80)
        lines.append(f"Total summaries: {total}")
        lines.append(f"Matched: {matched} ({100*matched/total:.1f}%)")
        lines.append(f"High confidence (>70%): {high_conf} ({100*high_conf/total:.1f}%)")
        lines.append(f"Unmatched: {total - matched}")

        return '\n'.join(lines)

    def export_json(self) -> dict:
        """Export mapping as JSON-serializable dict"""
        result = {
            'authors': [],
            'statistics': {
                'total_summaries': len(self.summaries),
                'matched': sum(1 for s in self.summaries if s.matched_content),
                'high_confidence': sum(1 for s in self.summaries if s.match_confidence > 0.7)
            }
        }

        for author_name, author in self.authors.items():
            author_data = {
                'name': author_name,
                'page_start': author.page_start,
                'summaries': []
            }

            for summary in author.summaries:
                summary_data = {
                    'opening_words': summary.opening_words,
                    'summary_text': summary.summary_text,
                    'page_ref': summary.page_ref,
                    'line_number': summary.line_number,
                    'matched': summary.matched_content is not None,
                    'confidence': summary.match_confidence
                }
                if summary.matched_content:
                    summary_data['content'] = {
                        'page_number': summary.matched_content.page_number,
                        'start_line': summary.matched_content.start_line,
                        'end_line': summary.matched_content.end_line
                    }
                author_data['summaries'].append(summary_data)

            result['authors'].append(author_data)

        return result


def main():
    import json

    # Read the document
    input_file = r"C:\Users\Main\yanky fridman\ocr-172a161e-b608-46df-83ec-5db88688b475.txt"

    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse
    parser = DocumentParser(content)
    parser.parse()

    # Generate report
    report = parser.get_mapping_report()
    report_file = input_file.replace('.txt', '_mapping_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")

    # Export JSON
    json_data = parser.export_json()
    json_file = input_file.replace('.txt', '_mapping.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"JSON saved to: {json_file}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Authors: {len(parser.authors)}")
    print(f"Summaries: {len(parser.summaries)}")
    print(f"Content sections: {len(parser.content_sections)}")
    matched = sum(1 for s in parser.summaries if s.matched_content)
    print(f"Matched: {matched}/{len(parser.summaries)} ({100*matched/len(parser.summaries):.1f}%)")


if __name__ == '__main__':
    main()
