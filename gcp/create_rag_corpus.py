#!/usr/bin/env python3

from vertexai.preview import rag
import vertexai

# Initialize Vertex AI
vertexai.init(project="tourgemini", location="europe-west1")

# Create RAG corpus
print("⏳ Creating RAG corpus...")
corpus = rag.create_corpus(
    display_name="hmda-nyc-corpus",
    description="HMDA housing/mortgage data for NYC MSA"
)

print(f"✅ RAG Corpus created: {corpus.name}")

# Import data from GCS
print("\n⏳ Importing HMDA data into RAG corpus...")
rag.import_files(
    corpus_name=corpus.name,
    paths=["gs://tourgemini-hmda-data/raw/"],
    chunk_size=512,
    chunk_overlap=100,
)

print("✅ HMDA data imported into RAG corpus")
print(f"\nCorpus Name: {corpus.name}")
print(f"Corpus Display Name: {corpus.display_name}")
