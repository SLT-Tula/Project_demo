import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import gradio as gr
import os
from datetime import datetime
import psycopg2
import time
from psycopg2 import sql


# link_author_saved = []

def crawl_content_article(link):
    url = 'https://unsplash.com'
    response = requests.get(link)
    article_soup = BeautifulSoup(response.content, 'html.parser')
    # print(link)
    img_element = article_soup.find_all('figure')
    image_link = []
    content_element = article_soup.find('div', class_ = 'eoX8Y IKU9M YBMqo')
    features = article_soup.find('div', class_ = 'VZRk3 rLPoM')
    collections_element = article_soup.find('div', class_ = 'gZhmU')
    coll = collections_element.find('a', class_ = 'A3ryi')
    link_colls = []
    for c in coll:
        link_coll = urljoin(url, c['href'])
        link_colls.append(link_coll)
    for img in img_element:
        info_img = img.find('div', class_ = 'MorZF')
        image_link.append(info_img.img['src'])
        # return image_link, content_element.get_text()
    return image_link, content_element.get_text(), features.get_text(separator=' | '), link_colls

def crawl_web_unsplash():
    url = 'https://unsplash.com'
    with requests.Session() as session:
        response = session.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    figures = soup.find_all('figure')
    results = []
    for figure in figures:
        try:
            link_element = figure.find('a')
            title = link_element['title']
            # if link_element['href'][1] == '@':
            #     link_author = urljoin(url, link_element['href'])
                # if link_author not in link_author_saved:
                    # link_author_saved.append(link_author)
            if link_element['href'][:7] == '/photos':
                link_image_article = urljoin(url, link_element['href'])

            info_image = figure.find('div', class_ = 'MorZF')
            link_image_origin = info_image.img['src']
            link_image_relate, content, features_image, link_colls_relate = crawl_content_article(link_image_article)
            # print(content)
            # if title and link_author and link_image_article and link_image_origin and content and features_image and link_image_relate and link_colls_relate is not None:
            results.append((title, link_image_article, link_image_origin, content, features_image, link_image_relate, link_colls_relate))

        except:
            continue
    return results


def save_to_data(output_folder, filename, title, link_image_article, link_image_origin, content, features_image, link_image_relate, link_colls_relate):
    os.makedirs(output_folder, exist_ok=True)
    file_path = os.path.join(output_folder, filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        try:
            file.write("Title: " + title + '\n'
                    + "Link image article: " + link_image_article + '\n' + 'Link image origin: ' + link_image_origin + '\n'
                    + "Content: " + content + '\n' + 'Featured image: ' + features_image + '\n'
                    + 'Link related photos: ' + link_image_relate + '\n' + 'Link related collections: ' + link_colls_relate)
        except Exception as e:
            print(f"Error writing to file: {e}")
    print(f'Content saved to {file_path}')


def create_database(db_name, user, password, host='localhost', port=5432):
    try:
        # Connect to the default 'postgres' database
        connection = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port
        )
        connection.autocommit = True
        cursor = connection.cursor()

        database_exists_query = f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';"
        cursor.execute(database_exists_query)
        database_exists = cursor.fetchone()

        if not database_exists:
            # Create a new database
            create_db_query = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
            cursor.execute(create_db_query)
    
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists. Skipping creation.")
 
    except (Exception, psycopg2.Error) as error:
        print(f"Error creating database: {error}")

    finally:
        if connection:
            cursor.close()
            connection.close()

def create_table_database():
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(
            database='web_data',
            user='postgres',
            password='TulaSlayer259@',
            host='localhost',
            port=5432
        )
        connection.autocommit = True
        cursor = connection.cursor()

        table_exists_query = '''
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = 'web_data'
            );
        '''
        cursor.execute(table_exists_query)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            # Create the web_data table
            create_table_query = '''
                CREATE TABLE web_data (
                    filename VARCHAR(255),
                    link_url VARCHAR(255)
                );
            '''
            cursor.execute(create_table_query)

            print("Table 'web_data' created successfully.")
        else:
            print("Table 'web_data' already exists. Skipping creation.")

    except (Exception, psycopg2.Error) as error:
        print(f"Error creating or checking table: {error}")

    finally:
        if connection:
            cursor.close()
            connection.close()

def save_file_to_database(folder_path, db_name, user, password, host='localhost', port=5432):
    try:
        connection = psycopg2.connect(
            database=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        connection.autocommit = True
        cursor = connection.cursor()
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                link_url = file.read()
            insert_query = sql.SQL("INSERT INTO web_data (filename, link_url) VALUES (%s, %s)")
            cursor.execute(insert_query, (filename, link_url))
            print(f"File saved to {db_name}")
            
    except (Exception, psycopg2.Error) as error:
        print(f"Error saving files to the database: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def execute_search_query(query):
    try:
        connection = psycopg2.connect(
            database='web_data',
            user='postgres',
            password='TulaSlayer259@',
            host='localhost',
            port=5432
        )
        connection.autocommit = True
        cursor = connection.cursor()

        # Customize the SQL query based on your data structure and search criteria
        search_query = "SELECT filename, link_url FROM web_data WHERE filename ILIKE %s OR link_url ILIKE %s"
        cursor.execute(search_query, ('%' + query + '%', '%' + query + '%'))
        results = cursor.fetchall()
        
        if results:
            # return results
            # related_links = [result[0] for result in results]
            print(f"Related link URLs for query '{query}':")
            for record in results:
                filename, link_url = record
                # print(record)
                print(f"Filename: {filename}, Link URL: {link_url}")
                return filename, link_url
        else:
            # return None
            print(f"No related link URLs found for query '{query}'.")
        
    except (Exception, psycopg2.Error) as error:
        print(f"Error searching in the database: {error}")

    finally:
        if connection:
            cursor.close()
            connection.close()
 
    


def search(query):
    # Customize the SQL query to retrieve relevant link URLs based on the user's question
    result = execute_search_query(query)
 
    return result



def print_like_dislike(x: gr.LikeData):
    print(x.index, x.value, x.liked)


def add_text(history, text):
    history = history + [(text, None)]
    return history, gr.Textbox(value="", interactive=False)


def bot(history):
    response = search(txt.value)
    history[-1][1] = ""
    for character in response:
        history[-1][1] += character
        time.sleep(0.05)
        yield history


with gr.Blocks() as demo:
    chatbot = gr.Chatbot(
        [],
        elem_id="chatbot",
        bubble_full_width=False,
        label='Search Engine'
    )

    with gr.Row():
        txt = gr.Textbox(
            scale=4,
            show_label=False,
            placeholder="Enter your search here...",
            container=False,
        )
        clear = gr.ClearButton([txt, chatbot])

    txt_msg = txt.submit(add_text, [chatbot, txt], [chatbot, txt], queue=False).then(
        bot, chatbot, chatbot, api_name="bot_response"
    )
    txt_msg.then(lambda: gr.Textbox(interactive=True), None, [txt], queue=False)

    chatbot.like(print_like_dislike, None, None)


folder_path='C:/Users/Lenovo/OneDrive/Documents/Intern_FPT/Mock-Project/data/'
results = crawl_web_unsplash()
if results:
    for result in results:
        title, link_image_article, link_image_origin, content, features_image, link_image_relate, link_colls_relate = result
        file_path = datetime.now().strftime("%d_%m_%y") + "_" + link_image_article.split("//")[1].replace("/", "_").replace(".", "_") + ".txt"
        with open(file_path, 'w', encoding='utf-8') as file:    
            save_to_data(folder_path, file_path, title, link_image_article, link_image_origin, content, features_image, link_image_relate, link_colls_relate)
            print("Save url to file txt successful!")
        
else:
    print("Error: Unable to crawl Unsplash.")


# Replace these values with your PostgreSQL credentials
# db_name = 'web_data'
# user = 'postgres'
# password = 'TulaSlayer259@'
 
# create_database(db_name, user, password)
# create_table_database()
# save_file_to_database(folder_path, db_name, user, password)


# demo.queue()
# if __name__ == "__main__":
#     demo.launch()