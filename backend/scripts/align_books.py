"""
Script to extract aligned sentence pairs from parallel English/French markdown books.
"""
import re
import csv
from pathlib import Path


def clean_markdown(text):
    """Remove markdown formatting and metadata."""
    # Remove YAML frontmatter
    text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.DOTALL)

    # Remove markdown headers (##, ###, etc.)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove markdown formatting
    text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)  # Bold/italic
    text = re.sub(r'`([^`]+)`', r'\1', text)  # Code
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Links
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)  # Images
    text = re.sub(r'\{[^}]+\}', '', text)  # Attributes like {.unnumbered}
    text = re.sub(r'>\s+', '', text, flags=re.MULTILINE)  # Blockquotes
    text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)  # List markers
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)  # Numbered lists
    text = re.sub(r':::', '', text)  # Custom blocks

    return text


def extract_sentences(text):
    """Extract sentences from text."""
    # Clean the text
    text = clean_markdown(text)

    # Split into paragraphs
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    sentences = []
    for para in paragraphs:
        # Clean up the paragraph
        para = re.sub(r'\s+', ' ', para).strip()

        # Skip very short paragraphs, signatures, metadata
        if len(para) < 20:
            continue
        if para.startswith('(') or para.startswith('['):
            continue
        if 'Signature' in para or 'unnumbered' in para:
            continue

        # Split into sentences (simple approach - split on . ! ? followed by space and capital)
        # But keep acronyms and abbreviations together
        sentence_parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', para)

        for sent in sentence_parts:
            sent = sent.strip()
            # Filter out very short sentences, pure punctuation, etc.
            if len(sent) >= 15 and re.search(r'[a-zA-Z]', sent):
                # Clean up extra whitespace
                sent = re.sub(r'\s+', ' ', sent)
                sentences.append(sent)

    return sentences


def align_sentences(en_sentences, fr_sentences):
    """
    Align English and French sentences.
    Uses a simple heuristic: assume sentences are roughly in the same order.
    """
    pairs = []

    # For now, use a simple 1:1 alignment based on order
    # This assumes the books are fairly well aligned structurally
    min_len = min(len(en_sentences), len(fr_sentences))

    # Take pairs from the beginning of each list
    for i in range(min_len):
        en_sent = en_sentences[i]
        fr_sent = fr_sentences[i]

        # Basic quality checks
        # English and French sentences should be roughly similar in length (within 3x ratio)
        len_ratio = max(len(en_sent), len(fr_sent)) / min(len(en_sent), len(fr_sent))

        if len_ratio > 5:  # Skip pairs with very different lengths
            continue

        pairs.append((en_sent, fr_sent))

    return pairs


def main():
    # Paths
    project_root = Path(__file__).parent.parent.parent
    en_book = project_root / "data" / "books" / "thirty-six-reasons-for-winning-the-lost_interior.md"
    fr_book = project_root / "data" / "books" / "trente-six-raisons-de-gagner-les-perdus_interieur.md"
    csv_file = project_root / "data" / "books" / "aligned_book.csv"

    print(f"Reading English book: {en_book}")
    with open(en_book, 'r', encoding='utf-8') as f:
        en_text = f.read()

    print(f"Reading French book: {fr_book}")
    with open(fr_book, 'r', encoding='utf-8') as f:
        fr_text = f.read()

    print("Extracting sentences from English book...")
    en_sentences = extract_sentences(en_text)
    print(f"  Found {len(en_sentences)} English sentences")

    print("Extracting sentences from French book...")
    fr_sentences = extract_sentences(fr_text)
    print(f"  Found {len(fr_sentences)} French sentences")

    print("Aligning sentences...")
    pairs = align_sentences(en_sentences, fr_sentences)
    print(f"  Created {len(pairs)} aligned pairs")

    # Read existing pairs from CSV
    existing_pairs = set()
    if csv_file.exists():
        with open(csv_file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_pairs.add((row['en'].strip(), row['fr'].strip()))

    print(f"  Found {len(existing_pairs)} existing pairs in CSV")

    # Filter out duplicates
    new_pairs = [p for p in pairs if p not in existing_pairs]
    print(f"  Adding {len(new_pairs)} new pairs")

    # Append new pairs to CSV
    if new_pairs:
        with open(csv_file, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            for en, fr in new_pairs:
                writer.writerow([en, fr])

        print(f"\n[SUCCESS] Successfully added {len(new_pairs)} new sentence pairs to {csv_file}")
        print(f"  Total pairs in CSV: {len(existing_pairs) + len(new_pairs)}")
    else:
        print("\n[SUCCESS] No new pairs to add (all pairs already exist in CSV)")

    # Show some examples
    if new_pairs:
        print("\nSample of new pairs:")
        for i, (en, fr) in enumerate(new_pairs[:5], 1):
            print(f"\n{i}. EN: {en[:100]}{'...' if len(en) > 100 else ''}")
            print(f"   FR: {fr[:100]}{'...' if len(fr) > 100 else ''}")


if __name__ == "__main__":
    main()
