import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

from conversation_relay.tools.core_tools import Tool, ToolDependencies

logger = logging.getLogger(__name__)

# Initialisation de ChromaDB (on pointe vers le dossier à la racine du projet)
DOSSIER_CHROMA = Path("chroma_db_reachy").resolve()

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)
chroma_client = chromadb.PersistentClient(path=str(DOSSIER_CHROMA))
collection = chroma_client.get_collection(
    name="entreprise_docs",
    embedding_function=embedding_fn
)


class ChercherInfoEntreprise(Tool):
    """Outil de recherche RAG dans la base de données de l'entreprise."""

    name = "chercher_info_entreprise"
    description = (
        "Search for official information about the company "
        "(activities, figures, clients, innovations, presentation, products, sectors, sharing, technologies, immersion). "
        "Use this whenever the user asks a specific question about the company."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "La question ou les mots-clés de la recherche.",
            },
        },
        "required": ["query"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> dict[str, Any]:
        """Exécute la recherche dans ChromaDB quand le LLM l'appelle."""
        query = kwargs.get("query", "")
        logger.info(f"🔍 Recherche RAG déclenchée avec la requête : {query}")

        try:
            # Recherche des 2 morceaux les plus pertinents
            results = collection.query(query_texts=[query], n_results=2)
            chunks = results["documents"][0] if results.get("documents") else []

            if not chunks:
                return {"resultat": "Aucune information trouvée dans la base de données."}

            contexte = "\n---\n".join(chunks)
            return {"resultat": contexte}

        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche RAG : {e}")
            return {"error": f"Erreur de recherche : {e}"}