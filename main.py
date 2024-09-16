import time
import redis
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as OrmSession
from sentence_transformers import SentenceTransformer
from  Data import Document, Base
from error_handling import handle_error

retrive = FastAPI()
Database_url = "postgresql://artisusxiren:Newpass@localhost/database_user"
engine=create_engine(Database_url)
Session = sessionmaker(bind=engine)

model = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L6-v2')
redis_client=redis.Redis(host='localhost',port=6379,db=0)
Cache_expiry=600
rate_limit=5

class SearchQuery(BaseModel):
    user_id:str
    text:str
    top_k: int=5
    threshold : float=0.1
@retrive.on_event('startup')   
async def startup_event():
    from celery_back import process_urls
    process_urls()
     
    
@retrive.get("/health")
def health_check():
    return{"status":"Api is running"}
@retrive.post("/search")
def search(query:SearchQuery):
    session=Session()
    try:
        user_id=query.user_id
        text=query.text
        top_k=query.top_k
        threshold=query.threshold
        user_requests= redis_client.get(user_id)
        if user_requests and int(user_requests)>rate_limit:
            raise HTTPException(status_code=429,detail="requests exceeded limit")
        redis_client.incr(user_id)
        start_time=time.time()
        query_embeddings=model.encode([text])[0]
        query_embeddings = query_embeddings.reshape(1, -1)
        cache_key=f"search:{text}"
        cached_result=redis_client.get(cache_key)
        
        if cached_result:
            print("Cache hit")
            results=eval(cached_result)
        else:
            print("Cache miss")
            documents_x=session.query(Document).all()
            doc_embeddings = [pad_or_truncate(doc.embedding) for doc in documents_x]
            doc_embeddings = np.array([np.array(embed) for embed in doc_embeddings])
            doc_embeddings = doc_embeddings.T 
            similarity= cosine_similarity(query_embeddings,doc_embeddings)[0]
            print(similarity)
            incdices_top=np.argsort(similarity)[::-1][:top_k]
            results=[
               {"document_id":documents_x[idx].id,"score":similarity[idx]}
               for idx in incdices_top if similarity[idx] >threshold     
            ]
            redis_client.set(cache_key,str(results),ex=Cache_expiry)
        inference_time=time.time()-start_time
        log_inference_time(user_id,inference_time)
        return {'results':results,"inference_time":inference_time}
    except Exception as e:
        handle_error(e)
       
    finally:
       session.close()
def pad_or_truncate(embedding):
    arr = np.frombuffer(embedding, dtype=np.float32)
    if len(arr) > 384:
        return arr[:384]
    elif len(arr) < 384:
        return np.pad(arr, (0, 384 - len(arr)), 'constant')
    return arr       
       
def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)
def log_inference_time(user_id, inference_time):
    print(f"user:{user_id},inference_time:{inference_time} seconds")
          
            
            