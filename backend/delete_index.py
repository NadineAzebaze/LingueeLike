from opensearchpy import OpenSearch

INDEX_NAME = "segments"

os = OpenSearch("http://localhost:9200")

if os.indices.exists(INDEX_NAME):
    os.indices.delete(INDEX_NAME)
    print(f"Index '{INDEX_NAME}' supprimé.")
else:
    print(f"L'index '{INDEX_NAME}' n'existe pas.")