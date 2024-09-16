from celery import Celery
from bs4 import BeautifulSoup
from main import Session,model
import requests
from Data import Document
from error_handling import handle_error
import numpy as np
import logging
logging.basicConfig(level=logging.INFO)
celery_app=Celery('celery_worker',broker='redis://localhost:6379/0',backend='redis://localhost:6379/0')
@celery_app.task
def background(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup= BeautifulSoup(response.content,'html.parser')
        article_text= ''.join([p.text for p in soup.find_all('p')])
        logging.info(article_text[:500])
        save_document(article_text)
        return article_text
    else:
        logging.info("Failed")
        return None
@celery_app.task    
def process_urls():    
    url_list=[
        'https://en.wikipedia.org/wiki/Heart',
        'https://en.wikipedia.org/wiki/Circulatory_system',]
    for url in url_list:
        background(url)
    print(f"Processing URL: {url}")   
@celery_app.task       
def save_document(text):
    session=Session()
    try:
        embedding =model.encode(text)[0]
        print(embedding)
        doc=Document(text=text,embedding=embedding)
        session.add(doc)
        session.commit()
        print("saved")
    except Exception as e:
        handle_error(e)
    finally:
        session.close()
     
    