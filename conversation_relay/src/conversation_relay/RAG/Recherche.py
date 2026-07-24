import chromadb
from chromadb.utils import embedding_functions

# 1. Utiliser le même modèle d'embedding
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)

# 2. Connexion à la base créée par ingest.py
chroma_client = chromadb.PersistentClient(path="./chroma_db_reachy")
collection = chroma_client.get_collection(
    name="entreprise_docs",
    embedding_function=embedding_fn
)

# 3. Poser une question piège (reformulée sans les mots exacts du fichier)
question = "C'est quoi la réalité mixte ?"

print(f"🔍 Question posée : '{question}'\n")

# 4. Rechercher le résultat le plus proche (n_results=1)
results = collection.query(
    query_texts=[question],
    n_results=1
)

# 5. Afficher le résultat trouvé
texte_trouve = results['documents'][0][0]
source = results['metadatas'][0][0]['fichier_source']

print(f"💡 Extrait trouvé par ChromaDB (depuis {source}) :")
print(f"   --> \"{texte_trouve}\"")