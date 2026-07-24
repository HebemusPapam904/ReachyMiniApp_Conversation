import os
import chromadb
from chromadb.utils import embedding_functions

DOSSIER_DATA = "conversation_relay/src/conversation_relay/RAG/data_entreprise"

# 1. Modèle d'embedding multilingue (performant en français)
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)

# 2. Initialisation du client ChromaDB local
chroma_client = chromadb.PersistentClient(path="./chroma_db_reachy")
try:
    chroma_client.delete_collection(name="entreprise_docs")
except Exception:
    pass  # Si la collection n'existait pas encore, on ignore l'erreur
collection = chroma_client.get_or_create_collection(
    name="entreprise_docs",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}
)

# Fonction pour découper un texte en morceaux (chunks)
def decouper_texte(texte, taille_chunk=400):
    # 1. On sépare d'abord par paragraphe / ligne
    paragraphes = [p.strip() for p in texte.split('\n') if p.strip()]
    chunks = []

    for p in paragraphes:
        # Si la ligne est courte (ex: une phrase normale), on la garde entière sans la couper
        if len(p) <= taille_chunk:
            if len(p) > 20:  # Filtre les lignes trop courtes ou vides
                chunks.append(p)
        else:
            # Si le paragraphe est très long, on découpe au niveau des ESPACES (mots)
            mots = p.split(' ')
            chunk_courant = []
            longueur_courante = 0

            for mot in mots:
                if longueur_courante + len(mot) + 1 <= taille_chunk:
                    chunk_courant.append(mot)
                    longueur_courante += len(mot) + 1
                else:
                    chunks.append(" ".join(chunk_courant))
                    chunk_courant = [mot]
                    longueur_courante = len(mot)

            if chunk_courant:
                chunks.append(" ".join(chunk_courant))

    return chunks

# --- INGESTION DES FICHIERS .TXT ---
documents = []
metadatas = []
ids = []

# Parcourir uniquement les fichiers .txt du dossier
for fichier in os.listdir(DOSSIER_DATA):
    if not fichier.endswith(".txt"):
        continue

    chemin_fichier = os.path.join(DOSSIER_DATA, fichier)
    print(f"📄 Lecture de : {fichier}")

    with open(chemin_fichier, "r", encoding="utf-8") as f:
        contenu = f.read()

    # Découpage du fichier en morceaux
    chunks = decouper_texte(contenu, taille_chunk=400)

    for index_chunk, chunk in enumerate(chunks):
        chunk_clean = chunk.strip()
        if len(chunk_clean) > 20:  # Filtrer les morceaux vides
            documents.append(chunk_clean)
            metadatas.append({"fichier_source": fichier})
            ids.append(f"{fichier}_chunk_{index_chunk}")

# Insertion ou mise à jour dans ChromaDB
if documents:
    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"\n✅ {len(documents)} morceaux de texte ont été indexés dans ChromaDB !")
else:
    print("\n❌ Aucun fichier .txt trouvé dans le dossier 'data_entreprise'.")