#!/usr/bin/env python3
"""
ChromaDB Veri Analizi ve Temizleme Aracı
=========================================

Mevcut verileri analiz eder, duplicate'leri tespit eder ve temizler.

Özellikler:
1. Duplicate Detection (Hash + Semantic)
2. Near-Duplicate Detection
3. Quality Analysis
4. Content Statistics
5. Auto-Cleanup (opsiyonel)

Kullanım:
    python analyze_and_clean.py analyze     # Analiz yap
    python analyze_and_clean.py duplicates  # Duplicate'leri bul
    python analyze_and_clean.py clean       # Temizle (dry-run)
    python analyze_and_clean.py clean --apply  # Gerçekten temizle
    python analyze_and_clean.py stats       # İstatistikler
    python analyze_and_clean.py export      # Dışa aktar
"""

import sys
import os
import json
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Set, Tuple

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def compute_hash(content: str) -> str:
    """İçerik hash'i hesapla."""
    normalized = ' '.join(content.lower().split())
    return hashlib.md5(normalized.encode()).hexdigest()


def compute_shingles(content: str, size: int = 5) -> Set[str]:
    """Shingle seti oluştur."""
    words = content.lower().split()
    if len(words) < size:
        return {content.lower()}
    return {' '.join(words[i:i+size]) for i in range(len(words) - size + 1)}


def jaccard_similarity(s1: Set[str], s2: Set[str]) -> float:
    """Jaccard benzerliği."""
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)


def analyze_documents():
    """Tüm dökümanları analiz et."""
    console.print("\n[bold blue]📊 ChromaDB Veri Analizi[/bold blue]\n")
    
    try:
        from core.chromadb_manager import get_chromadb_manager, ChromaDBConfig
        from core.config import settings
        
        config = ChromaDBConfig(
            persist_directory=str(settings.DATA_DIR / "chroma_db"),
            collection_name="enterprise_knowledge",
        )
        manager = get_chromadb_manager(config)
        manager.initialize()
        
        # Get all data
        all_data = manager.get(include=["documents", "metadatas", "embeddings"])
        
        ids = all_data.get("ids", [])
        documents = all_data.get("documents", [])
        metadatas = all_data.get("metadatas", [])
        
        console.print(f"[green]✅ Toplam {len(ids)} döküman bulundu[/green]\n")
        
        # Analysis results
        analysis = {
            "total_documents": len(ids),
            "unique_contents": 0,
            "exact_duplicates": [],
            "near_duplicates": [],
            "low_quality": [],
            "sources": defaultdict(int),
            "languages": defaultdict(int),
            "quality_scores": [],
            "lengths": [],
        }
        
        # Hash map for exact duplicate detection
        hash_map: Dict[str, List[Tuple[int, str]]] = defaultdict(list)
        
        # Shingle map for near-duplicate detection
        shingle_map: Dict[int, Set[str]] = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Step 1: Hash and shingle calculation
            task1 = progress.add_task("Hash ve shingle hesaplanıyor...", total=len(ids))
            
            for i, doc in enumerate(documents):
                if doc:
                    content = doc.strip()
                    content_hash = compute_hash(content)
                    hash_map[content_hash].append((i, ids[i]))
                    shingle_map[i] = compute_shingles(content)
                    
                    # Length and quality
                    analysis["lengths"].append(len(content))
                    
                    # Metadata analysis
                    meta = metadatas[i] if metadatas and i < len(metadatas) else {}
                    if meta:
                        source = meta.get("source") or meta.get("filename", "unknown")
                        analysis["sources"][source] += 1
                        
                        lang = meta.get("language", "unknown")
                        analysis["languages"][lang] += 1
                        
                        quality = meta.get("quality_score")
                        if quality is not None:
                            analysis["quality_scores"].append(quality)
                
                progress.advance(task1)
            
            # Step 2: Find exact duplicates
            task2 = progress.add_task("Exact duplicate'ler tespit ediliyor...", total=1)
            
            for content_hash, doc_list in hash_map.items():
                if len(doc_list) > 1:
                    # Keep first, mark rest as duplicates
                    original_idx, original_id = doc_list[0]
                    for idx, doc_id in doc_list[1:]:
                        analysis["exact_duplicates"].append({
                            "duplicate_id": doc_id,
                            "duplicate_index": idx,
                            "original_id": original_id,
                            "original_index": original_idx,
                            "hash": content_hash,
                            "preview": documents[idx][:80] + "..." if documents[idx] else "",
                        })
            
            analysis["unique_contents"] = len(hash_map)
            progress.advance(task2)
            
            # Step 3: Find near-duplicates (semantic)
            task3 = progress.add_task("Near-duplicate'ler tespit ediliyor...", total=len(ids))
            
            checked_pairs = set()
            
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    pair_key = (min(i, j), max(i, j))
                    if pair_key in checked_pairs:
                        continue
                    checked_pairs.add(pair_key)
                    
                    # Skip if already exact duplicate
                    is_exact_dup = any(
                        d["duplicate_index"] == i or d["duplicate_index"] == j 
                        for d in analysis["exact_duplicates"]
                    )
                    if is_exact_dup:
                        continue
                    
                    # Calculate Jaccard similarity
                    if i in shingle_map and j in shingle_map:
                        similarity = jaccard_similarity(shingle_map[i], shingle_map[j])
                        
                        if similarity >= 0.7:  # 70% benzerlik
                            analysis["near_duplicates"].append({
                                "doc1_id": ids[i],
                                "doc1_index": i,
                                "doc2_id": ids[j],
                                "doc2_index": j,
                                "similarity": similarity,
                                "preview1": documents[i][:60] + "..." if documents[i] else "",
                                "preview2": documents[j][:60] + "..." if documents[j] else "",
                            })
                
                progress.advance(task3)
        
        # Display results
        console.print("\n" + "="*60)
        console.print("[bold cyan]📈 ANALİZ SONUÇLARI[/bold cyan]")
        console.print("="*60 + "\n")
        
        # Summary table
        summary_table = Table(title="Özet İstatistikler", show_header=True)
        summary_table.add_column("Metrik", style="cyan")
        summary_table.add_column("Değer", style="green")
        
        summary_table.add_row("Toplam Döküman", str(analysis["total_documents"]))
        summary_table.add_row("Benzersiz İçerik", str(analysis["unique_contents"]))
        summary_table.add_row("Exact Duplicate", str(len(analysis["exact_duplicates"])))
        summary_table.add_row("Near Duplicate", str(len(analysis["near_duplicates"])))
        summary_table.add_row("Benzersiz Kaynak", str(len(analysis["sources"])))
        
        if analysis["lengths"]:
            avg_len = sum(analysis["lengths"]) / len(analysis["lengths"])
            summary_table.add_row("Ortalama Uzunluk", f"{avg_len:.0f} karakter")
        
        if analysis["quality_scores"]:
            avg_quality = sum(analysis["quality_scores"]) / len(analysis["quality_scores"])
            summary_table.add_row("Ortalama Kalite", f"{avg_quality:.2f}")
        
        console.print(summary_table)
        
        # Exact duplicates
        if analysis["exact_duplicates"]:
            console.print(f"\n[bold red]⚠️ {len(analysis['exact_duplicates'])} EXACT DUPLICATE BULUNDU:[/bold red]\n")
            
            dup_table = Table(show_header=True)
            dup_table.add_column("Duplicate ID", style="red")
            dup_table.add_column("Original ID", style="green")
            dup_table.add_column("İçerik Önizleme")
            
            for dup in analysis["exact_duplicates"][:10]:  # İlk 10
                dup_table.add_row(
                    dup["duplicate_id"][:16] + "...",
                    dup["original_id"][:16] + "...",
                    dup["preview"][:50] + "..."
                )
            
            console.print(dup_table)
            
            if len(analysis["exact_duplicates"]) > 10:
                console.print(f"... ve {len(analysis['exact_duplicates']) - 10} duplicate daha")
        else:
            console.print("\n[green]✅ Exact duplicate bulunamadı![/green]")
        
        # Near duplicates
        if analysis["near_duplicates"]:
            console.print(f"\n[bold yellow]⚠️ {len(analysis['near_duplicates'])} NEAR-DUPLICATE BULUNDU:[/bold yellow]\n")
            
            near_table = Table(show_header=True)
            near_table.add_column("Döküman 1", style="yellow")
            near_table.add_column("Döküman 2", style="yellow")
            near_table.add_column("Benzerlik", style="cyan")
            
            for nd in sorted(analysis["near_duplicates"], key=lambda x: x["similarity"], reverse=True)[:10]:
                near_table.add_row(
                    nd["doc1_id"][:16] + "...",
                    nd["doc2_id"][:16] + "...",
                    f"{nd['similarity']:.1%}"
                )
            
            console.print(near_table)
        else:
            console.print("\n[green]✅ Near-duplicate bulunamadı![/green]")
        
        # Sources breakdown
        if analysis["sources"]:
            console.print("\n[bold blue]📁 KAYNAK DAĞILIMI:[/bold blue]\n")
            
            source_table = Table(show_header=True)
            source_table.add_column("Kaynak", style="blue")
            source_table.add_column("Döküman Sayısı", style="green")
            
            for source, count in sorted(analysis["sources"].items(), key=lambda x: x[1], reverse=True):
                source_table.add_row(source[:50], str(count))
            
            console.print(source_table)
        
        # Save analysis report
        report_path = Path(__file__).parent / "data" / "analysis_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert defaultdict to dict for JSON
        analysis["sources"] = dict(analysis["sources"])
        analysis["languages"] = dict(analysis["languages"])
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        console.print(f"\n[dim]📄 Rapor kaydedildi: {report_path}[/dim]")
        
        return analysis
        
    except Exception as e:
        console.print(f"[red]❌ Hata: {e}[/red]")
        import traceback
        traceback.print_exc()
        return None


def clean_duplicates(apply: bool = False):
    """Duplicate'leri temizle."""
    console.print("\n[bold blue]🧹 Duplicate Temizleme[/bold blue]\n")
    
    if apply:
        console.print("[bold red]⚠️ APPLY MODE - Gerçekten silinecek![/bold red]\n")
    else:
        console.print("[yellow]ℹ️ DRY-RUN MODE - Sadece simülasyon[/yellow]\n")
    
    analysis = analyze_documents()
    
    if not analysis:
        return
    
    exact_dups = analysis.get("exact_duplicates", [])
    
    if not exact_dups:
        console.print("[green]✅ Silinecek duplicate yok![/green]")
        return
    
    console.print(f"\n[yellow]🗑️ {len(exact_dups)} duplicate silinecek...[/yellow]\n")
    
    if not apply:
        console.print("[dim]Gerçekten silmek için: python analyze_and_clean.py clean --apply[/dim]")
        return
    
    # Actually delete
    try:
        from core.chromadb_manager import get_chromadb_manager, ChromaDBConfig
        from core.config import settings
        
        config = ChromaDBConfig(
            persist_directory=str(settings.DATA_DIR / "chroma_db"),
            collection_name="enterprise_knowledge",
        )
        manager = get_chromadb_manager(config)
        
        ids_to_delete = [d["duplicate_id"] for d in exact_dups]
        
        manager.delete(ids=ids_to_delete)
        
        console.print(f"[green]✅ {len(ids_to_delete)} duplicate silindi![/green]")
        
        # Verify
        new_count = manager.count()
        console.print(f"[blue]ℹ️ Yeni toplam: {new_count} döküman[/blue]")
        
    except Exception as e:
        console.print(f"[red]❌ Silme hatası: {e}[/red]")


def show_stats():
    """İstatistikleri göster."""
    console.print("\n[bold blue]📊 Detaylı İstatistikler[/bold blue]\n")
    
    try:
        from core.enterprise_vector_store import get_enterprise_vector_store
        
        store = get_enterprise_vector_store()
        store._ensure_initialized()
        
        # Get analytics
        analytics = store.get_analytics()
        
        console.print(Panel(
            json.dumps(analytics, indent=2, ensure_ascii=False, default=str),
            title="Analytics",
            border_style="blue",
        ))
        
    except Exception as e:
        console.print(f"[red]❌ Hata: {e}[/red]")
        import traceback
        traceback.print_exc()


def export_data():
    """Verileri export et."""
    console.print("\n[bold blue]📤 Veri Export[/bold blue]\n")
    
    try:
        from core.enterprise_vector_store import get_enterprise_vector_store
        
        store = get_enterprise_vector_store()
        
        output_path = Path(__file__).parent / "data" / "export" / f"documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        result = store.export_documents(str(output_path))
        
        if result["success"]:
            console.print(f"[green]✅ {result['document_count']} döküman export edildi![/green]")
            console.print(f"[dim]📄 Dosya: {result['path']}[/dim]")
        else:
            console.print(f"[red]❌ Export hatası: {result.get('error')}[/red]")
        
    except Exception as e:
        console.print(f"[red]❌ Hata: {e}[/red]")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="ChromaDB Veri Analizi ve Temizleme")
    parser.add_argument(
        "command",
        choices=["analyze", "duplicates", "clean", "stats", "export"],
        help="Çalıştırılacak komut",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Değişiklikleri uygula (clean komutu için)",
    )
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        analyze_documents()
    elif args.command == "duplicates":
        analyze_documents()
    elif args.command == "clean":
        clean_duplicates(apply=args.apply)
    elif args.command == "stats":
        show_stats()
    elif args.command == "export":
        export_data()


if __name__ == "__main__":
    main()
