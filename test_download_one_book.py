#!/usr/bin/env python3
# Test script to download just one book

import sys
import os

# Add the current directory to path so we can import our module
sys.path.insert(0, os.path.dirname(__file__))

from download_hanen_books_from_scribd import search_scribd_for_url, download_with_scribd_downloader

def test_one_book():
    """Test downloading one book."""
    book = "It Takes Two to Talk Hanen Centre"
    print(f"Testing with book: {book}")
    
    # Search for the book
    print("Searching Scribd...")
    url = search_scribd_for_url(book)
    
    if url:
        print(f"Found URL: {url}")
        # Download the book
        print("Downloading...")
        success = download_with_scribd_downloader(url)
        if success:
            print("✓ Test PASSED: Book downloaded successfully")
            return True
        else:
            print("✗ Test FAILED: Download failed")
            return False
    else:
        print("✗ Test FAILED: Could not find book on Scribd")
        return False

if __name__ == "__main__":
    success = test_one_book()
    sys.exit(0 if success else 1)