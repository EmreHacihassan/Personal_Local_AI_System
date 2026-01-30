
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

try:
    from core.note_graph import get_note_graph
    from core.notes_manager import notes_manager
    
    print(f"Data Directory: {notes_manager.data_dir}")
    print(f"Notes File Exists: {notes_manager.notes_file.exists()}")
    
    # Try to load notes
    notes = notes_manager.get_all_notes()
    print(f"Loaded {len(notes)} notes.")
    
    if len(notes) == 0:
        print("WARNING: No notes loaded!")
    
    # Try to build graph
    print("Building graph...")
    graph = get_note_graph(notes_manager).build_graph()
    
    print("Graph built successfully.")
    print(f"Nodes: {len(graph['nodes'])}")
    print(f"Edges: {len(graph['edges'])}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
