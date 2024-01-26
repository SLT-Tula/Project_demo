import requests
from bs4 import BeautifulSoup
import gradio as gr
import os

urls_to_scrape = [
    # "https://www.gradio.app/docs/",
    "https://flask.palletsprojects.com/en/3.0.x/"]

# Function to extract text from a URL
def extract_text_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # print(soup)
            # Customize this based on the structure of the website
            contents = []
            for tag in soup.find_all(True):
                # print(tag)
                if tag.name =='a':
                    if str(tag['href'])[:7] != 'https:':
                        print(url+str(tag['href']))
                        contents.append(url+str(tag['href']))
                    else:
                        contents.append(str(tag['href']))
                elif tag.name == 'p':
                    contents.append(str(tag.get_text()))
            return ' '.join(contents)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def save_to_data(output_folder='./data', filename, content):
    os.makedirs(output_folder, exist_ok=True)
    file_path = os.path.join(output_folder, filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f'Content saved to {file_path}')


for url in urls_to_scrape:
    content = extract_text_from_url(url)
    print('Content URL: ', content)
    print('\n--------------------------------\n')

