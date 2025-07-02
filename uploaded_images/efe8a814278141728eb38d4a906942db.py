from sentence_transformers import SentenceTransformer

# Load the model
model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dimensional embeddings

# Function to read and chunk a markdown file
def read_markdown(file_path, chunk_size=500, overlap=50):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Optional cleaning or markdown stripping can be added here
    chunks = []
    for i in range(0, len(content), chunk_size - overlap):
        chunk = content[i:i + chunk_size]
        chunks.append(chunk)
    return chunks

# Path to your .md file
file_path = "/home/npci/Desktop/slurmdbd.md"

# Get text chunks
chunks = read_markdown(file_path)

# Convert chunks into embeddings
embeddings = model.encode(chunks, convert_to_numpy=True)

# You now have: 
# - `chunks` → list of text segments
# - `embeddings` → corresponding list of vectors (shape: [n_chunks, 384])

# Print summary
for i, (text, emb) in enumerate(zip(chunks, embeddings)):
    print(f"Chunk {i+1}: {text[:60]}... -> Embedding shape: {emb.shape}")
