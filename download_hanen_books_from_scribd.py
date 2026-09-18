import sys
import time
import subprocess
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def search_scribd_for_url(query):
    """Search Scribd.com for a query and return the first document URL."""
    print(f"Searching Scribd for: '{query}'")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Run in background
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Make Chrome less detectable
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    try:
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Go to Scribd.com
        driver.get("https://www.scribd.com")
        time.sleep(2)
        
        # Wait for the search box to be available
        wait = WebDriverWait(driver, 10)
        # Try multiple selectors for the search box
        search_selectors = [
            "input[type='search']",
            "input[name='q']",
            ".search_input",
            "input[placeholder='Search Scribd']"
        ]
        
        search_box = None
        for selector in search_selectors:
            try:
                search_box = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if search_box:
                    break
            except:
                continue
        
        if not search_box:
            # Try XPath as fallback
            try:
                search_box = driver.find_element(By.XPATH, "//input[@placeholder='Search Scribd']")
            except:
                pass
        
        if search_box:
            print("Found search box, entering query...")
            search_box.clear()
            search_box.send_keys(query)
            time.sleep(1)
            
            # Press Enter to search
            search_box.send_keys(Keys.RETURN)
            print("Search submitted")
            
            # Wait for results to load
            time.sleep(3)
            
            # Try to find the first result link that points to a document
            result_selectors = [
                "a[href*='/document/']",
                "a[href*='/doc/']",
                "a[href*='/scribd/']"  # Sometimes they use this pattern
            ]
            
            result_links = []
            for selector in result_selectors:
                links = driver.find_elements(By.CSS_SELECTOR, selector)
                if links:
                    result_links.extend(links)
                    break  # Use the first selector that finds results
            
            # Remove duplicates while preserving order
            seen = set()
            unique_links = []
            for link in result_links:
                href = link.get_attribute("href")
                if href and href not in seen:
                    seen.add(href)
                    unique_links.append(link)
            
            if unique_links:
                first_link = unique_links[0]
                href = first_link.get_attribute("href")
                text = first_link.text.strip()
                print(f"Found result: {text[:100]}...")
                print(f"URL: {href}")
                
                # Ensure we have a www.scribd.com URL (the downloader prefers this)
                if "es.scribd.com" in href or "fr.scribd.com" in href:
                    # Convert to www.scribd.com
                    href = href.replace("es.scribd.com", "www.scribd.com")
                    href = href.replace("fr.scribd.com", "www.scribd.com")
                    print(f"Converted to: {href}")
                
                return href
            else:
                print("No document links found in search results")
                # Debug: show what links we did find
                all_links = driver.find_elements(By.TAG_NAME, "a")
                print(f"Found {len(all_links)} total links on page")
                for i, link in enumerate(all_links[:5]):
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    if href and text and ('scribd' in href.lower() or len(text) > 20):
                        print(f"  Link {i+1}: {text[:50]}... -> {href}")
                return None
        else:
            print("Could not find search box")
            # Save page source for debugging
            with open(f"scribd_search_debug_{int(time.time())}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return None
            
    except Exception as e:
        print(f"Error during search: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        try:
            driver.quit()
        except:
            pass

def download_with_scribd_downloader(url):
    """Download a Scribd URL using the existing scribd-downloader script."""
    print(f"Downloading from: {url}")
    
    script_path = os.path.join(os.path.dirname(__file__), "scribd-downloader", "scribd-downloader.py")
    
    if not os.path.exists(script_path):
        print(f"ERROR: Scribd downloader script not found at {script_path}")
        return False
    
    try:
        # Run the script and pipe the URL as input
        proc = subprocess.Popen(
            [sys.executable, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send the URL followed by newline
        stdout, stderr = proc.communicate(input=url + "\n", timeout=300)  # 5 minute timeout
        
        print(f"Downloader return code: {proc.returncode}")
        if stdout:
            print(f"Stdout: {stdout[-500:] if len(stdout) > 500 else stdout}")  # Show last 500 chars
        if stderr:
            print(f"Stderr: {stderr[-500:] if len(stderr) > 500 else stderr}")
        
        if proc.returncode == 0:
            print("Download successful!")
            return True
        else:
            print("Download failed!")
            return False
            
    except subprocess.TimeoutExpired:
        print("Download timed out after 5 minutes")
        proc.kill()
        return False
    except Exception as e:
        print(f"Error running downloader: {e}")
        return False

def main():
    # List of Hanen books to download
    books = [
        "It Takes Two to Talk Hanen Centre",
        "Hablando nos entendemos los dos Hanen Centre",  # Spanish version
        "More Than Words Fern Sussman",
        "Más que palabras Fern Sussman",  # Spanish version
        "TalkAbility Fern Sussman",
        "You Make the Difference Ayala Manolson",
        "Learning Language and Loving It Elaine Weitzman Janice Greenberg"
    ]
    
    print("=== Starting Hanen Books Download from Scribd ===")
    print(f"Total books to process: {len(books)}")
    
    successful = 0
    failed = 0
    
    for i, book in enumerate(books, 1):
        print(f"\n{'='*60}")
        print(f"Processing book {i}/{len(books)}: {book}")
        print(f"{'='*60}")
        
        # Search for the book on Scribd
        url = search_scribd_for_url(book)
        
        if url:
            # Download the book
            if download_with_scribd_downloader(url):
                print(f"✓ SUCCESS: {book}")
                successful += 1
            else:
                print(f"✗ FAILED: Failed to download {book}")
                failed += 1
        else:
            print(f"✗ FAILED: Could not find {book} on Scribd")
            failed += 1
        
        # Add a delay between books to be respectful to the server
        if i < len(books):
            print(f"\nWaiting 5 seconds before next book...")
            time.sleep(5)
    
    print(f"\n{'='*60}")
    print(f"=== DOWNLOAD SUMMARY ===")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total: {len(books)}")
    print(f"{'='*60}")
    
    if failed > 0:
        print("\nSome books failed to download. You may want to:")
        print("1. Try running the script again (sometimes transient errors occur)")
        print("2. Search for the books manually on Scribd and note the URLs")
        print("3. Check if the books are available on other platforms like Internet Archive")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())