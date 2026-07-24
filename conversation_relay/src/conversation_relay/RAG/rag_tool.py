import chromadb
from pathlib import Path
from typing import Any, Dict
from chromadb.utils import embedding_functions

# Import de la classe de base Tool de Pollen Robotics
from conversation_relay.tools.core_tools import Tool, ToolDependencies

# Configuration des chemins
BASE_DIR = Path(__file__).resolve().parent.parent
DOSSIER_CHROMA = BASE_DIR / "chroma_db_reachy"

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)
chroma_client = chromadb.PersistentClient(path=str(DOSSIER_CHROMA))
collection = chroma_client.get_collection(
    name="entreprise_docs",
    embedding_function=embedding_fn
)


class ChercherInfoEntreprise(Tool):
    # Identifiants lus par le LLM
    name = "chercher_info_entreprise"
    description = (
        "Recherche des informations officielles sur l'entreprise "
        "(activites, chiffres, clients, innovations, presentation, produits, secteurs , sharing, technologies, immersion). "
        "À utiliser dès que l'utilisateur pose une question spécifique sur l'entreprise."
    )
    
    # Schéma JSON des arguments attendus par la fonction
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "La question ou les mots-clés de la recherche.",
            }
        },
        "required": ["query"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        query = kwargs.get("query", "")
        
        # Recherche ChromaDB
        results = collection.query(query_texts=[query], n_results=2)
        chunks = results['documents'][0] if results['documents'] else []

        if not chunks:
            return {"resultat": "Aucune information trouvée dans la base."}

        return {"resultat": "\n---\n".join(chunks)}