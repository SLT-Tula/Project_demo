import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import gradio as gr
import os
import pandas as pd
from datetime import datetime
import psycopg2
import time
from psycopg2 import sql
import schedule
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def crawl_article_unsplash(link):
    url = 'https://unsplash.com'
    with requests.Session() as session:
        response = session.get(link)
    article_soup = BeautifulSoup(response.content, 'html.parser')
    link_authors = []
    name_authors = []
    info_author = article_soup.find('a', class_ = 'N2odk RZQOk eziW_ Byk7y KHq0c')
    if info_author['href'][1] != '@':
        colab_author = article_soup.find('a', class_ = 'NowSe eziW_')
        name_authors.append(colab_author.get_text())
        colab_author = urljoin(url, colab_author['href'])
        link_authors.append(colab_author)
    name_author = info_author.get_text()
    link_author = urljoin(url, info_author['href'])
    link_authors.append(link_author)
    name_authors.append(name_author)
    if len(link_authors) == 2:
        link_author = link_authors[0]
    if len(name_authors) == 2:
        name_author = name_authors[0]
    author = name_author + ' - ' + link_author
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
    day_publish = article_soup.find('span', class_ = 'e6qY8 IKU9M')
    day_publish = day_publish.find('time').get_text()
    link_download = article_soup.find('div', class_ = 'sBV1O')
    if link_download is not None:
        link_download = link_download.a['href']
    else:
        link_download = 'Cannot download free'
    return author, link_download, content_element.get_text(), features.get_text(separator=' | '), day_publish

def crawl_article_picography(link):
    with requests.Session() as session:
        response = session.get(link)
    article_soup = BeautifulSoup(response.content, 'html.parser')
    info_author = article_soup.find('span', class_ = 'photographer-profile')
    element_author = info_author.find('a')
    name_author = element_author.get_text()
    link_author = element_author['href']
    author = name_author + ' - ' + link_author
    features = article_soup.find('div', class_ = 'tags')
    day_publish = article_soup.find('meta', property = 'article:published_time')
    day_publish = day_publish['content']
    link_download = article_soup.find('div', class_ = 'download-buttons')
    del link_download.a['target']
    link_download = link_download.a['href']
    return author, link_download, features.get_text(separator=' | ')[8:-4], day_publish

def crawl_web():
    urls = ['https://unsplash.com', 'https://picography.co']
    name_webs = ['Unsplash', 'Picography']
    for i, url in enumerate(urls):
        name_web = name_webs[i]
        with requests.Session() as session:
            response = session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        if url == 'https://unsplash.com':
            figures = soup.find_all('figure')
            results = []
            for figure in figures:
                try:
                    link_element = figure.find('a', class_ = 'rEAWd')
                    if 'href' in link_element.attrs:        
                        title = link_element['title']
                        link_image_article = urljoin(url, link_element['href'])
                        info_image = link_element.find('div', class_ = 'MorZF')
                        link_image = info_image.img['src']
                        author, link_download, content, features, day_publish = crawl_article_unsplash(link_image_article)
                        results.append((link_image_article, title, link_image, author, link_download, features, day_publish, name_web))

                except:
                    continue
        elif url == 'https://picography.co':
            figures = soup.find_all('div', class_ = 'single-photo-thumb')
            results = []
            for figure in figures:
                try:
                    link_element = figure.find('a')
                    if 'href' in link_element.attrs:        
                        title = link_element['title']
                        link_image_article = link_element['href']
                        link_image = link_element.img['src']
                        author, link_download, features, day_publish = crawl_article_picography(link_image_article)
                        results.append((link_image_article, title, link_image, author, link_download, features, day_publish, name_web))
                except:
                    continue
    return results


def save_to_data(output_folder, filename, link_image_article, title, link_image, author, link_download, features, day_publish, name_web):
    try:
        # if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
        file_path = os.path.join(output_folder, filename)
        existing_files = set(os.listdir(output_folder))
        if filename not in existing_files:
            with open(file_path, 'w', encoding='utf-8') as file:
                try:
                    file.write("{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}".format(link_image_article, title, link_image, author, link_download, features, day_publish, name_web))
                except Exception as e:
                    print(f"Error writing to file: {e}")
            print(f'Content saved to {file_path}')
        else:
            print(f"File {filename} is exists!")
    except Exception as e:
        print(f"Error: {e}")


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
                    link_image_article TEXT PRIMARY KEY,
                    title VARCHAR,
                    image TEXT,
                    author TEXT,
                    link_download TEXT,
                    features TEXT,
                    day_publish DATE,
                    name_web TEXT
                );
            '''
            cursor.execute(create_table_query)
            # Populate the search_vector column
            # update_search_vector_query = '''
            #     UPDATE web_table SET search_vector = to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(info_image_article, ''))
            # '''
            # cursor.execute(update_search_vector_query)

            print("Table 'web_table' created successfully.")
        else:
            print("Table 'web_table' already exists. Skipping creation.")

    except (Exception, psycopg2.Error) as error:
        print(f"Error creating or checking table: {error}")

    finally:
        if connection:
            cursor.close()
            connection.close()

def send_email(subject, body):
    # Thay các giá trị này bằng thông tin của email của bạn
    sender_email = "huynhdangtien259@gmail.com"
    receiver_email = "huynhdangtien85@gmail.com"
    password = "andu wzcy fvbw rqss"
    
    # Tạo một tin nhắn email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    
    # Thêm nội dung vào email
    message.attach(MIMEText(body, "plain"))
    
    # Kết nối đến máy chủ SMTP và gửi email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.send_message(message)

def save_file_to_database(db_name, folder_path):
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
            # if filename not in set(os.listdir(folder_path)):
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                if not lines:
                    continue
                else:
                    link_image_article = lines[0]
                    title = lines[1]
                    link_image = lines[2]
                    author = lines[3]
                    link_download = lines[4]
                    features = lines[5]
                    day_publish = lines[6]
                    name_web = lines[7]
            cursor.execute(f"SELECT COUNT(*) FROM web_table WHERE link_image_article = %s", (link_image_article,))
            count = cursor.fetchone()[0]
            if count == 0:
                insert_query = sql.SQL("INSERT INTO web_table (link_image_article, title, image, author, link_download, features, day_publish, name_web) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
                cursor.execute(insert_query, (link_image_article, title, link_image, author, link_download, features, day_publish, name_web))
                send_email("New Data Saved", f"New data has been saved to the database:\n{title}")
                print(f"File saved to {db_name}")
            else:
                print(f"Key {link_image_article} is exists!")

    except (Exception, psycopg2.Error) as error:
        print(f"Error saving files to the database: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def execute_search_query(query, features, name_webs):
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

        # Split the query into individual words
        # keywords = query.split()
        # features_conditions = " AND ".join(["features ILIKE %s" for _ in features])
        # webs_conditions = " AND ".join(["name_webs ILIKE %s" for _ in name_webs])

        # # Tạo tuple các giá trị để thêm vào câu truy vấn
        # values = [f"%{query}%"] + [f"%{feature}%" for feature in features] + [f"%{name_web}%" for name_web in name_webs]
        # # Use AND conditions to ensure that results contain all keywords
        # search_query = f"""
        #     SELECT link_image_article, title, image, author, link_download, features, day_publish, name_web 
        #     FROM web_table 
        #     WHERE title ILIKE %s
        #     AND ({features_conditions})
        #     AND ({webs_conditions})
        #     """
        # .format(" OR ".join([f"(features ILIKE %s)" for _ in features]))
        # """.format(" AND ".join([f"(title ILIKE %s)" for _ in keywords]))

        # cursor.execute(search_query, ['%' + word + '%' for word in keywords] * 2)
        conditions = []
        values = [f"%{query}%"]
        # Thêm điều kiện truy vấn cho tính năng nếu có
        if features:
            features_conditions = " AND ".join(["features ILIKE %s" for _ in features])
            conditions.append(f"({features_conditions})")
            values.extend([f"%{feature}%" for feature in features])
        # Thêm điều kiện truy vấn cho trang web nếu có
        if name_webs:
            webs_conditions = " AND ".join(["name_web ILIKE %s" for _ in name_webs])
            conditions.append(f"({webs_conditions})")
            values.extend([f"%{name_web}%" for name_web in name_webs])

        # Xây dựng câu truy vấn
        where_clause = " AND ".join(conditions)
        search_query = f"""
            SELECT link_image_article, title, image, author, link_download, features, day_publish, name_web 
            FROM web_table 
            WHERE title ILIKE %s
        """
        if conditions:
            search_query += f" AND ({where_clause})"
        cursor.execute(search_query, values)
        results = cursor.fetchall()

        return results
        
    except (Exception, psycopg2.Error) as error:
        print(f"Error searching in the database: {error}")

    finally:
        if connection:
            cursor.close()
            connection.close()


def search(query, features, name_webs):
    # Customize the SQL query to retrieve relevant link URLs based on the user's question
    result = execute_search_query(query, features, name_webs)
    return result

def show_search(query, features, name_webs):
    start_time = time.time()
    output = search(query, features, name_webs)
    end_time = time.time()
    if output:
        formatted_results = gr.DataFrame(value=pd.DataFrame({"Link image article": [result[0]], "Title": [result[1]],
                                                              "Image": [f"<img src='{result[2]}'>"], "Author": [result[3]],
                                                              "Link download": [result[4]], "Features image": [result[5]],
                                                              "Day published": [result[6]], "Name web": [result[7]],
                                                              "Elapsed time (s)": [end_time - start_time]} for result in output),
                                                              interactive=True, wrap=True)
        return formatted_results
    else:
        return "No results found."

# css='div {background-image: url("https://miro.medium.com/v2/resize:fit:876/1*5eytpWnZAJeoVlHBir4m4w.png")}'
with gr.Blocks() as demo:
    unsplash_icon_html = "<img src='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTcfXWlIL-GP4gLuivasNP2eTt4XVoesC9Oqc0y8rWQKVT-8NBWKOZw-NR26JIgV7MeTgQ&usqp=CAU' style='width: 40px; height: 40px; margin-right: 5px;'>"
    btn_html = f"<div style='text-align: center; font-size: 48px; padding: 10px; display: flex; align-items: center; color: #008080;'>{unsplash_icon_html} Image search engine<span style='margin-left: 5px;'>🔍</span></div>"
    gr.HTML(btn_html)
#     gr.Markdown(value="Image search engine in Unsplash")
#     gr.ImageEditor(value="C:/Users/Lenovo/OneDrive/Documents/Intern_FPT/Mock-Project/icon_unsplash.png", height=200, width=600)
    with gr.Row():
        txt = gr.Textbox(
            scale=4,
            show_label=False,
            placeholder="Enter your search here...",
            container=False,
        )
        features_checkbox = gr.CheckboxGroup(
            choices=["Nature", "People", "Animal"],
            label="Select features to include",
        )
        webs_checkbox = gr.CheckboxGroup(
            choices=["Unsplash", "Picography"],
            label="Select website to include",
        )
        btn = gr.Button(value = 'Search', icon="C:/Users/Lenovo/OneDrive/Documents/Intern_FPT/Mock-Project/download.png")
    results = gr.DataFrame(headers=["Link image article", "Title", "Image", "Author", "Link download", "Features image", "Day published", "Name web", "Elapsed time (s)"],
                           datatype=["markdown", "str", "markdown", "markdown", "markdown", "str", "date", "str", "date"], interactive=True, wrap=True)
    txt_query = txt.submit(show_search, [txt, features_checkbox, webs_checkbox], [results])
    btn.click(show_search, inputs=[txt, features_checkbox, webs_checkbox], outputs=[results])
    clear = gr.ClearButton([txt, features_checkbox, webs_checkbox, results])


def crawl_and_save():
    folder_path='C:/Users/Lenovo/OneDrive/Documents/Intern_FPT/Mock-Project/data/'
    results = crawl_web()
    if results:
        for result in results:
            link_image_article, title, link_image, author, link_download, features, day_publish, name_web = result
            filename = datetime.now().strftime("%d_%m_%y") + "_" + link_image_article.split("//")[1].replace("/", "_").replace(".", "_") + ".txt"
            save_to_data(folder_path, filename, link_image_article, title, link_image, author, link_download, features, day_publish, name_web)
    else:
        print("Error: Unable to crawl.")

# def crawl_and_save_every_hours():
folder_path='C:/Users/Lenovo/OneDrive/Documents/Intern_FPT/Mock-Project/data/'
crawl_and_save()
db_name = 'web_data'
user = 'postgres'
password = 'TulaSlayer259@'
create_database(db_name, user, password)
create_table_database()
save_file_to_database(db_name, folder_path)

if __name__ == "__main__":
    demo.launch()

# schedule.every().hours.do(crawl_and_save_every_hours())

# Vòng lặp để duy trì lịch trình chạy
# while True:
#     schedule.run_pending()
#     time.sleep(1)