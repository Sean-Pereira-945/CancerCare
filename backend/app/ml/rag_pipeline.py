from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader, DirectoryLoader
from langchain_core.documents import Document

BACKEND_DIR = Path(__file__).resolve().parents[2]
VECTOR_STORE_PATH = BACKEND_DIR / "data/vector_store"
KNOWLEDGE_BASE_PATH = BACKEND_DIR / "data/knowledge_base"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


_embeddings = None


def get_embeddings():
    """Load sentence-transformer embedding model (cached in memory)."""
    global _embeddings
    if _embeddings is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL}...")
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings


def build_knowledge_base():
    """Run this once to index all PDFs in data/knowledge_base/ into FAISS."""
    print("Loading documents...")
    loader = DirectoryLoader(
        str(KNOWLEDGE_BASE_PATH),
        glob="**/*.pdf",
        loader_cls=PyMuPDFLoader
    )
    docs = loader.load()
    print(f"Loaded {len(docs)} document pages")

    # Split into chunks for better retrieval
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " "]
    )
    chunks = splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks")

    # Create FAISS vector store
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)

    # Save to disk
    VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(VECTOR_STORE_PATH))
    print("Knowledge base built and saved!")


def load_vectorstore():
    """Load the pre-built FAISS vector store from disk."""
    embeddings = get_embeddings()
    return FAISS.load_local(
        str(VECTOR_STORE_PATH),
        embeddings,
        allow_dangerous_deserialization=True
    )


def add_patient_report(user_id: str, report_text: str):
    """Add a patient's parsed report to a user-specific FAISS index for personalized RAG."""
    doc = Document(
        page_content=report_text,
        metadata={"user_id": user_id, "source": "patient_report"}
    )
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents([doc])
    embeddings = get_embeddings()

    user_store_path = VECTOR_STORE_PATH / f"user_{user_id}"
    if user_store_path.exists():
        vs = FAISS.load_local(str(user_store_path), embeddings, allow_dangerous_deserialization=True)
        vs.add_documents(chunks)
    else:
        vs = FAISS.from_documents(chunks, embeddings)
    vs.save_local(str(user_store_path))


if __name__ == "__main__":
    build_knowledge_base()
