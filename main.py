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


def crawl_article(link):
    url = 'https://unsplash.com'
    with requests.Session() as session:
        response = session.get(link)
    article_soup = BeautifulSoup(response.content, 'html.parser')
    link_authors = []
    info_author = article_soup.find('a', class_ = 'N2odk RZQOk eziW_ Byk7y KHq0c')
    if info_author['href'][1] != '@':
        colab_author = article_soup.find('div', class_ = 'AVon2 RZQOk iOqvK FHkK2')
        colab_author = urljoin(url, colab_author.a['href'])
        link_authors.append(colab_author)
    link_author = urljoin(url, info_author['href'])
    link_authors.append(link_author)
    images_element = article_soup.find_all('img', class_ = 'tB6UZ a5VGX')
    image_link = []
    for image_element in images_element:
        if 'src' in image_element.attrs:
            image_link.append(image_element['src'])
    
    content_element = article_soup.find('div', class_ = 'eoX8Y IKU9M YBMqo')
    features = article_soup.find('div', class_ = 'VZRk3 rLPoM')
    collections_element = article_soup.find('div', class_ = 'gZhmU')
    coll = collections_element.find_all('a', class_ = 'A3ryi')
    link_colls = []
    for c in coll:
        link_coll = urljoin(url, c['href'])
        link_colls.append(link_coll)
    info_article = {'Link authors': link_authors, 'Link related photos': image_link,
                    'Content': content_element.get_text(),
                    'Features of image': features.get_text(separator=' | '),
                    'Link related collections': link_colls}
    return info_article

def crawl_web_unsplash():
    url = 'https://unsplash.com'
    with requests.Session() as session:
        response = session.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    figures = soup.find_all('figure')
    results = []
    for figure in figures:
        try:
            link_element = figure.find('a', class_ = 'rEAWd')
            if 'href' in link_element.attrs:        
                title = link_element['title']
                link_image_article = urljoin(url, link_element['href'])
                info_image = link_element.find('div', class_ = 'MorZF')
                link_image_origin = info_image.img['src']
                info_article = crawl_article(link_image_article)
                results.append((title, link_image_article, link_image_origin, info_article))

        except:
            continue
    # print(results)
    return results


def save_to_data(output_folder, filename, title, link_image_article, link_image_origin, info_article):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    file_path = os.path.join(output_folder, filename)
    existing_files = set(os.listdir(output_folder))
    if filename not in existing_files:
        with open(file_path, 'w', encoding='utf-8') as file:
            try:
                
                file.write("Title: {}\nLink image article: {}\nLink image origin: {}\nInformation image article: {}.".format(title, link_image_article, link_image_origin, info_article))
                    
            except Exception as e:
                print(f"Error writing to file: {e}")
        print(f'Content saved to {file_path}')
    else:
        print(f"File {filename} is exists!")


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
                WHERE table_name = 'web_table'
            );
        '''
        cursor.execute(table_exists_query)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            # Create the web_table table
            create_table_query = '''
                CREATE TABLE web_table (
                    title VARCHAR(512),
                    link_image_article VARCHAR(512),
                    link_image_origin VARCHAR(512),
                    info_image_article VARCHAR(1024)
                );
            '''
            cursor.execute(create_table_query)

            print("Table 'web_table' created successfully.")
        else:
            print("Table 'web_table' already exists. Skipping creation.")

    except (Exception, psycopg2.Error) as error:
        print(f"Error creating or checking table: {error}")

    finally:
        if connection:
            cursor.close()
            connection.close()

def save_file_to_database(folder_path):
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
        for filename in set(os.listdir(folder_path)):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                if not lines:
                    continue
                else:
                    title = lines[0]
                    link_image_article = lines[1]
                    link_image_origin = lines[2]
                    info_image_article = lines[3]
            insert_query = sql.SQL("INSERT INTO web_table (title, link_image_article, link_image_origin, info_image_article) VALUES (%s, %s, %s, %s)")
            cursor.execute(insert_query, (title, link_image_article, link_image_origin, info_image_article))
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
        search_query = "SELECT title, link_image_article, link_image_origin, info_image_article FROM web_table WHERE title ILIKE %s OR info_image_article ILIKE %s"
        cursor.execute(search_query, ('%' + query + '%', '%' + query + '%'))
        results = cursor.fetchall()
        
        if results:
            # return results
            related_links = [result[0] for result in results]
            print(f"Related link URLs for query '{query}':")
            for record in results:
                title, link_image_article, link_image_origin, info_image_article = record
            #     # print(record)
                print(f"Title: {title}, Link image article: {link_image_article}, Link image origin: {link_image_origin}, Information image article: {info_image_article}")
            #     # return title, link_image_article, link_image_origin, info_image_article
                return related_links
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

def show_search(query):
    # query = txt.value
    output = search(query)
    return output


with gr.Blocks() as demo:

    with gr.Row():
        txt = gr.Textbox(
            scale=4,
            show_label=False,
            placeholder="Enter your search here...",
            container=False,
        )
        btn = gr.Button(value = 'Search')
    results = gr.Textbox(value="", lines=8)
    txt_query = txt.submit(show_search, [txt], [results])
    btn.click(show_search, inputs=[txt], outputs=[results])
    clear = gr.ClearButton([txt, results])


folder_path='C:/Users/Lenovo/OneDrive/Documents/Intern_FPT/Mock-Project/data/'
results = crawl_web_unsplash()
if results:
    for result in results:
        title, link_image_article, link_image_origin, info_image_article = result
        file_path = datetime.now().strftime("%d_%m_%y") + "_" + link_image_article.split("//")[1].replace("/", "_").replace(".", "_") + ".txt"
        # with open(file_path, 'w', encoding='utf-8') as file:    
        save_to_data(folder_path, file_path, title, link_image_article, link_image_origin, info_image_article)
        print("Save url to file txt successful!")
        
else:
    print("Error: Unable to crawl Unsplash.")


# Replace these values with your PostgreSQL credentials
db_name = 'web_data'
user = 'postgres'
password = 'TulaSlayer259@'
 
create_database(db_name, user, password)
create_table_database()
save_file_to_database(folder_path)


if __name__ == "__main__":
    demo.launch()