import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

def load_all_publications(driver, max_tries=10):
    """
    Clicks 'Show more' repeatedly until all publications are loaded or no new 
    publications appear after a certain number of tries (max_tries).
    """

    attempts = 0

    while attempts < max_tries:
        try:
            show_more = driver.find_element(By.ID, "gsc_bpf_more")
            # Check if the button is disabled
            if 'disabled' in show_more.get_attribute('class'):
                break  # no more results to load
            #
            # Count current publications
            current_pub_count = len(driver.find_elements(By.CSS_SELECTOR, ".gsc_a_tr"))
            show_more.click()
            time.sleep(2)  # wait for new publications to load
            new_pub_count = len(driver.find_elements(By.CSS_SELECTOR, ".gsc_a_tr"))

            # If no new publications were added, increment attempts
            if new_pub_count == current_pub_count:
                attempts += 1
            else:
                attempts = 0  # reset attempts if new pubs were loaded
        except:
            # If we can't find the button, probably no "Show more" is present
            break

def get_citations_from_scholar(author_url):

    # Setup the Chrome driver using webdriver_manager
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    driver.get(author_url)

    # Wait for initial load
    time.sleep(3)

    # Load all publications (or until no more appear)
    load_all_publications(driver)

    # Now get the publication entries
    publications = driver.find_elements(By.CSS_SELECTOR, ".gsc_a_tr")
    results = []

    for pub in publications:
        # Get the title of the publication
        title_elem = pub.find_element(By.CSS_SELECTOR, ".gsc_a_t a")
        title = title_elem.text.strip()

        # Get the citation count
        try:
            citation_elem = pub.find_element(By.CSS_SELECTOR, ".gsc_a_c a")
            citations = citation_elem.text.strip()
            if citations == "":
                citations = "0"
        except:
            citations = "0"

        results.append((title, citations))

    driver.quit()

    return results


def save_to_csv(data, filename="scholar_data.csv"):
    """
    Saves the publication data to a CSV file.
    Data should be a list of tuples: [(title, citations), ...]
    """

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(["Title", "Citations"])
        writer.writerows(data)


if __name__ == "__main__":
    # Use the Google Scholar author profile you provided
    AUTHOR_PROFILE_URL = "https://scholar.google.com/citations?hl=en&user=wWlI9XMAAAAJ"
    data = get_citations_from_scholar(AUTHOR_PROFILE_URL)

    # Print the results
    for title, citation_count in data:
        print(f"Title: {title}\nCitations: {citation_count}\n")

    # Save results to CSV
    save_to_csv(data, "scholar_data.csv")
    print("Data saved to scholar_data.csv")