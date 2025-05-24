import os
import sys
import json
import time  
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec  
from sentence_transformers import SentenceTransformer  

if sys.platform == 'win32':
    try:
        import readline
    except ImportError:
        class DummyReadline:
            def __getattr__(self, name):
                return lambda *args, **kwargs: None
        
        sys.modules['readline'] = DummyReadline()

load_dotenv()


PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found in .env file.")
pc = Pinecone(api_key=PINECONE_API_KEY)

print("Loading sentence-transformers model 'all-MiniLM-L6-v2'...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
EMBEDDING_DIMENSION = embedding_model.get_sentence_embedding_dimension()  # Should be 384
print(f"Model loaded. Embedding dimension: {EMBEDDING_DIMENSION}")

index_name = "kroolo"


if index_name not in [idx.name for idx in pc.list_indexes()]:
    print(f"Index '{index_name}' not found. Creating new index with dimension {EMBEDDING_DIMENSION}...")
    pc.create_index(
        name=index_name,
        dimension=EMBEDDING_DIMENSION,
        metric="cosine",  
        spec=ServerlessSpec(cloud='aws', region='us-east-1') 
    )
    print("Waiting for index to be ready...")
    while not pc.describe_index(index_name).status['ready']:
        time.sleep(5)
    print(f"Index '{index_name}' created and ready.")
else:
   
    index_description = pc.describe_index(index_name)
    actual_dimension = index_description.dimension
    print(f"Using existing index '{index_name}' with dimension {actual_dimension}.")
    if actual_dimension != EMBEDDING_DIMENSION:
        print(f"CRITICAL WARNING: Existing index dimension {actual_dimension} does not match model dimension {EMBEDDING_DIMENSION}.")
        print("This script expects the index to be compatible with 'all-MiniLM-L6-v2'.")
        print("Please delete the index and re-run this script if you want to use 'all-MiniLM-L6-v2'.")


def load_records_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        records = json.load(f)
    print(f"Successfully loaded {len(records)} records from {file_path}")
    return records


def batch_records(records, batch_size=50):  
    """Split records into batches of specified size"""
    for i in range(0, len(records), batch_size):
        yield records[i:i + batch_size]


json_file_path = "c:\\Users\\npuni\\Desktop\\Kroolo\\app\\combined-kroolo-records.json"
records_data = load_records_from_json(json_file_path)  


index = pc.Index(index_name)


def prepare_batch_for_upsert(batch_data, model):
    vectors_to_upsert = []
    
    print(f"DEBUG: Preparing batch with {len(batch_data)} records.")
    if not batch_data:
        return []

    for record_index, record in enumerate(batch_data):
        text_to_embed = record.get("chunk_text")
        record_id = record.get("_id")

        if not text_to_embed:
            if record_index < 5: 
                 print(f"Skipping record (ID: {record_id if record_id else 'Unknown'}) due to missing or empty text. Text field value: '{text_to_embed}'")
            continue
        if not record_id:
            if record_index < 5: 
                print(f"Skipping record (Text: {'<text available>' if text_to_embed else '<text missing>'}) due to missing or empty ID. ID field value: '{record_id}'")
            continue
            
        embedding = model.encode(text_to_embed).tolist()
        metadata = {key: value for key, value in record.items() if key not in ['id', 'text']}
        metadata['text'] = text_to_embed
        
        vectors_to_upsert.append({
            "id": str(record_id),
            "values": embedding,
            "metadata": metadata
        })
            
    return vectors_to_upsert


if records_data:
    total_upserted = 0
    print(f"Starting to embed and upsert {len(records_data)} records...")
    for i, batch in enumerate(batch_records(records_data)):
        print(f"Processing batch {i+1}/{len(records_data)//50 + 1}...")
        vectors_for_pinecone = prepare_batch_for_upsert(batch, embedding_model)
        if vectors_for_pinecone:
            index.upsert(vectors=vectors_for_pinecone, namespace="kroolo-docs")  
            total_upserted += len(vectors_for_pinecone)
            print(f"Successfully embedded and upserted batch {i+1} ({len(vectors_for_pinecone)} records)")
        else:
            print(f"Batch {i+1} resulted in no vectors to upsert.")
    
    print(f"Total records successfully embedded and upserted: {total_upserted} out of {len(records_data)}")
else:
    print("No records were loaded. Please check your JSON file.")

print("Vector storage script finished.")

