import psycopg2
import pymupdf  # PyMuPDF
from sentence_transformers import SentenceTransformer
import ollama


conn = psycopg2.connect(
    dbname="mydb",
    user="admin",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# โหลดโมเดลสำหรับแปลงข้อความเป็นเวกเตอร์
embedder = SentenceTransformer("BAAI/bge-m3")  # 1024-D vector

def extract_text_from_pdf(pdf_path, chunk_size=500):
    """ อ่าน PDF และแบ่งเป็น chunks (ขนาดละ 500 ตัวอักษร) """
    doc = pymupdf.open(pdf_path)
    full_text = "\n".join(page.get_text("text") for page in doc)
    
    # แบ่งข้อความเป็น chunks
    chunks = [full_text[i:i + chunk_size] for i in range(0, len(full_text), chunk_size)]
    return chunks


def insert_pdf_data(project_title, pdf_path):
    emb_project_title = embedder.encode(project_title).tolist()
    cur.execute(
        "INSERT INTO projects (project_title,emb_project_title,pdf_path) VALUES (%s,%s, %s) RETURNING id",
        (project_title,emb_project_title,pdf_path)
    )
    project_id = cur.fetchone()[0]  
    conn.commit()

    # แยก PDF เป็น chunks และแปลงเป็นเวกเตอร์
    chunks = extract_text_from_pdf(pdf_path)
    for chunk_id, chunk_text in enumerate(chunks):
        embedding = embedder.encode(chunk_text).tolist()
        cur.execute(
            "INSERT INTO embeddings (project_id, chunk_id, content, vector) VALUES (%s, %s, %s, %s)",
            (project_id, chunk_id, chunk_text, embedding)
        )
    conn.commit()

def query_postgresql(query_text, k=5):
    """ ค้นหา chunks ที่ใกล้เคียงที่สุดจาก `embeddings` """
    query_embedding = embedder.encode(query_text).tolist()
    
    sql_query = """
        SELECT projects.project_title, projects.pdf_path, embeddings.content, embeddings.vector <=> %s::vector AS similarity_score
        FROM embeddings
        JOIN projects ON projects.id = embeddings.project_id
        ORDER BY similarity_score ASC
        LIMIT %s;
    """
    cur.execute(sql_query, (query_embedding, k))
    result = cur.fetchall()
    return result
    
conversation_history = []  # เก็บประวัติการสนทนา

def generate_response(query_text):
    global conversation_history  
    
    retrieved_docs = query_postgresql(query_text)
    context = "\n".join([f"Title: {doc[0]}, File: {doc[1]}, Content: {doc[2]}" for doc in retrieved_docs])
    
    # สร้าง prompt สำหรับโมเดล
    prompt = f"Answer the question based on the following projects:\n{context}\n\nQuestion: {query_text}"
    
    # เพิ่มคำถามใหม่ในประวัติการสนทนา
    conversation_history.append({"role": "user", "content": query_text})
    
    
    response = ollama.chat(model="llama3.2", messages=[
        {"role": "system", "content": "You are an assistant."},
        *conversation_history,  # รวมประวัติการสนทนา
        {"role": "user", "content": prompt}
    ])
    
    # เก็บคำตอบในประวัติการสนทนา
    conversation_history.append({"role": "assistant", "content": response["message"]["content"]})
    
    return response["message"]["content"]



#insert_pdf_data("Workshop Risk Register", "data/Workshop Risk Register.pdf")  

for  i in range(3):
    question = input("Ask a question: ") 
    print(generate_response(question))