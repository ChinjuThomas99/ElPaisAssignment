from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from collections import Counter
import time
import requests
import json


driver = webdriver.Chrome()  
driver.get('https://elpais.com/')

driver.maximize_window()
try:
    wait = WebDriverWait(driver, 20)  
    try:
        accept_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id = 'didomi-notice-agree-button']")))
    except:
        print("Element not found with ID. Trying alternative selectors...")
        accept_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='didomi-notice-agree-button']/span"))
        )

    driver.execute_script("arguments[0].scrollIntoView(true);", accept_button)
    accept_button.click()

    # Ensure the page is in Spanish
    dropdown_element = driver.find_element(By.ID, "edition_head")
    selected_option_text = dropdown_element.find_element(By.TAG_NAME, "span").text
    selected_option_text = selected_option_text.encode('utf-8').decode('utf-8')
    #assert selected_option_text.strip() == 'ESPAÑA', f"Expected 'ESPAÑA', but got '{selected_option_text.strip()}'"
    if 'ESPA' in selected_option_text:
        print("The webpage is in Spanish.")
    else:
        print(f"Unexpected text: {selected_option_text}")

    print(driver.execute_script("return document.characterSet;"))

    # Navigate to the Opinion section
    opinion_section = driver.find_element(By.PARTIAL_LINK_TEXT, "Opin")
    
    opinion_section.click()
    time.sleep(3)
    print("Navigated to the Opinion section of the website")

    # Scrape the first 5 articles
    articles = driver.find_elements(By.XPATH, "/html/body/main/div[1]/section[1]/div/article")[:5]

    # Print the number of articles found
    #print(f"Found {len(articles)} articles.")

    article_data = []
    for index, article in enumerate(articles, start=1):
        ActionChains(driver).move_to_element(article).perform()
        
    
        article_link = article.find_element(By.XPATH, './/h2/a').get_attribute('href')
        driver.execute_script("window.open(arguments[0]);", article_link)
        driver.switch_to.window(driver.window_handles[-1])  # Switch to the new tab
        
        try:
            # Extract title, content, and image
            title = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//h1'))
            ).text
            
            content = ""
            paragraphs = driver.find_elements(By.XPATH, '/html/body/article/div/p')
            for paragraph in paragraphs:
                content += paragraph.text + "\n"
            try:
                h2_content = driver.find_element(By.XPATH, '/html/body/article/header/div[2]/h2').text
                content += "\n" + h2_content
            except:
                pass
            
            image_url = driver.find_element(By.XPATH, '//span/img').get_attribute('src')

    
            article_data.append({'title': title, 'content': content, 'image_url': image_url})

            
            img_data = requests.get(image_url).content
            with open(f"article_{index}.jpg", 'wb') as img_file:
                img_file.write(img_data)

        except Exception as e:
            print(f"Error processing article: {e}")
        
    
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
except Exception as e:
    print(f"Error: {e}")
    
finally:
    
    driver.quit()

# Print the Title and content of article in spanish
for data in article_data:
    print(f"Title: {data['title']}")
    print(f"Content: {data['content']}")


def translate_text_rapid(text, target_language="en"):
    url = "https://rapid-translate-multi-traduction.p.rapidapi.com/t"
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "your_api_key_here", #API Key
        "X-RapidAPI-Host": "rapid-translate-multi-traduction.p.rapidapi.com",
    }
    payload = {"from": "auto", "to": target_language, "e": "", "q": [text]}
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    
    translated_text = response.json()[0]
    return translated_text

def analyze_translated_headers(headers):
    exclude_words = {"es"} 
    flattened_headers = [
        " ".join(item) if isinstance(item, list) else str(item)
        for item in headers
    ]
    
    all_words = " ".join(flattened_headers).lower().split()
    filtered_words = [word for word in all_words if word not in exclude_words]

    word_counts = Counter(filtered_words)
    repeated_words = {word: count for word, count in word_counts.items() if count > 2}
    return repeated_words

# Translating article titles and analyzing repeated words
translated_titles = []
for article in article_data:
    spanish_title = article["title"]
    try:
        translated_title = translate_text_rapid(spanish_title)
        print(f"Original Title: {spanish_title}")
        print(f"Translated Title: {translated_title}")
        translated_titles.append(translated_title)
    except Exception as e:
        print(f"Error translating title: {e}")


repeated_words = analyze_translated_headers(translated_titles)
print("Repeated words and their counts:")
for word, count in repeated_words.items():
    print(f"{word}: {count}")

