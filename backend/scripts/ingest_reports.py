import os
import sys
from pathlib import Path

# Add backend to path so we can import app modules
# We assume this script is in the 'research' folder, which is a sibling to 'backend'
sys.path.append(str(Path(__file__).parent.parent / "backend"))

# Mock environment variables if needed before imports
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "dummy_key")

try:
    from app.ml.report_parser import parse_report
    from app.ml.rag_pipeline import add_patient_report
except ImportError as e:
    print(f"Error: Could not import backend modules. Make sure you are running this from the research folder. {e}")
    sys.exit(1)

def ingest_test_reports(user_id="test-user"):
    """
    Reads PDF reports from the 'test_reports' folder and indexes them
    into the vector store for a specific user.
    """
    # Define paths
    research_dir = Path(__file__).parent
    report_dir = research_dir / "test_reports"
    
    # Create directory if it doesn't exist
    if not report_dir.exists():
        report_dir.mkdir(parents=True)
        print(f"\n[CREATE] Created directory at: {report_dir}")
        print("--> Action Required: Please drop your PDF medical reports into this folder.")
        return

    # Find all PDFs
    pdf_files = list(report_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"\n[EMPTY] No PDF files found in: {report_dir}")
        print("--> Action Required: Drop some PDF reports there and run this script again.")
        return

    print(f"\n[START] Found {len(pdf_files)} reports. Indexing for user ID: '{user_id}'...")

    success_count = 0
    for pdf_path in pdf_files:
        print(f"  > Processing: {pdf_path.name}...")
        try:
            with open(pdf_path, "rb") as f:
                file_bytes = f.read()
            
            # 1. Parse text from PDF
            parsed = parse_report(file_bytes)
            
            # 2. Add to Personalized Vector Store
            # Note: add_patient_report creates/updates the index in data/vector_store/user_{user_id}
            add_patient_report(user_id, parsed["full_text"])
            
            print(f"    [OK] Successfully indexed.")
            success_count += 1
        except Exception as e:
            print(f"    [ERROR] Failed to index {pdf_path.name}: {e}")

    print(f"\n[COMPLETE] {success_count}/{len(pdf_files)} reports are now in the Personalized RAG system.")
    print(f"Your research experiments for Variant A2-A5 will now use this data when using token for '{user_id}'.")

if __name__ == "__main__":
    # You can change the user_id if you are testing with a specific account
    ingest_test_reports(user_id="test-user")
