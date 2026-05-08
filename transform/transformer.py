import asyncio
import logging
import math
from pathlib import Path
from typing import Any, Dict, Tuple

import instructor
from openai import AsyncOpenAI
from openai import AsyncAPITimeoutError, APIError

from core.config import get_settings
from core.exceptions import InvalidMethodError, LLMTimeoutError
from transform import schemas

logger = logging.getLogger(__name__)
settings = get_settings()

# Inisialisasi client OpenAI dengan Instructor
# Gunakan mode asinkron karena dipanggil dari endpoint FastAPI
client = instructor.from_openai(AsyncOpenAI(api_key=settings.openai_api_key))

PROMPTS_DIR = Path(__file__).parent / "prompts"

# Peta metode ke tuple (PydanticSchema, NamaFilePrompt)
METHOD_REGISTRY = {
    "mind_map": (schemas.MindMapSchema, "mind_map.txt"),
    "cornell": (schemas.CornellSchema, "cornell.txt"),
    "boxing": (schemas.BoxingSchema, "boxing.txt"),
    "charting": (schemas.ChartingSchema, "charting.txt"),
    "zettelkasten": (schemas.ZettelkastenSchema, "zettelkasten.txt"),
    "sketchnoting": (schemas.SketchnotingSchema, "sketchnoting.txt"),
    "feynman": (schemas.FeynmanSchema, "feynman.txt"),
}

def load_prompt(method: str) -> str:
    """Membaca isi file prompt berdasarkan metode."""
    if method not in METHOD_REGISTRY:
        raise InvalidMethodError(method)
    
    _, prompt_file = METHOD_REGISTRY[method]
    prompt_path = PROMPTS_DIR / prompt_file
    
    if not prompt_path.exists():
        logger.error(f"Prompt file {prompt_path} tidak ditemukan.")
        # Fallback sementara jika terjadi masalah
        return "Tolong format teks berikut: {clean_text}"
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

async def transform_notes(clean_text: str, method: str) -> Dict[str, Any]:
    """
    Mengubah teks bersih menjadi format struktur React Flow 
    berdasarkan metode belajar yang dipilih.
    """
    if method not in METHOD_REGISTRY:
        raise InvalidMethodError(method)

    schema_class, _ = METHOD_REGISTRY[method]
    prompt_template = load_prompt(method)
    prompt = prompt_template.replace("{clean_text}", clean_text)
    
    logger.info(f"Transforming notes with method: {method}")
    
    try:
        # Gunakan asyncio.wait_for untuk membatasi waktu eksekusi LLM
        structured_output = await asyncio.wait_for(
            client.chat.completions.create(
                model=settings.openai_model_transform,
                response_model=schema_class,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2, # Sedikit deterministik tapi masih punya ruang untuk ide
                max_retries=3
            ),
            timeout=settings.transform_timeout
        )
    except asyncio.TimeoutError:
         raise LLMTimeoutError(stage=f"transform ({method})")
    except Exception as e:
        logger.error(f"Error calling LLM for transform: {e}")
        # Tangani atau bungkus kembali error jika perlu, 
        # untuk saat ini re-raise agar bisa ditangkap oleh exception handler FastAPI
        raise 
        
    # Konversi output Pydantic menjadi format React Flow
    nodes, edges = convert_to_reactflow(structured_output, method)
    
    return {
        "method": method,
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            # Tambahan metadata kalau diperlukan bisa disisipkan disini
        }
    }


def convert_to_reactflow(data: Any, method: str) -> Tuple[list, list]:
    """
    Mengubah output terstruktur (Pydantic schema) menjadi format 
    nodes dan edges untuk React Flow.
    """
    nodes = []
    edges = []
    
    if method == "mind_map":
        nodes, edges = _convert_mindmap(data)
    elif method == "cornell":
        nodes, edges = _convert_cornell(data)
    elif method == "boxing":
        nodes, edges = _convert_boxing(data)
    elif method == "charting":
        nodes, edges = _convert_charting(data)
    elif method == "zettelkasten":
        nodes, edges = _convert_zettelkasten(data)
    elif method == "sketchnoting":
        nodes, edges = _convert_sketchnoting(data)
    elif method == "feynman":
        nodes, edges = _convert_feynman(data)
        
    return nodes, edges

# -----------------------------------------------------------------------------
# Konversi Spesifik per Metode (dengan kalkulasi posisi otomatis)
# -----------------------------------------------------------------------------

def _convert_mindmap(data: schemas.MindMapSchema) -> Tuple[list, list]:
    nodes = []
    edges = []
    
    # Tambahkan title node (Opsional, tergantung butuh dirender atau tidak)
    # nodes.append({"id": "mm_title", "type": "title", "position": {"x": 400, "y": 50}, "data": {"label": data.title}})

    canvas_center = (400, 300)
    
    # Hitung posisi secara radial
    positions = {}
    positions[data.root.id] = canvas_center
    
    branches = data.root.children
    n_branches = len(branches)
    
    for i, branch in enumerate(branches):
        # Distribusi melingkar
        angle = (2 * math.pi / max(1, n_branches)) * i - (math.pi / 2)
        radius = 200
        x = canvas_center[0] + radius * math.cos(angle)
        y = canvas_center[1] + radius * math.sin(angle)
        positions[branch.id] = (round(x), round(y))
        
        # Edge Root -> Branch
        edges.append({
            "id": f"e-{data.root.id}-{branch.id}",
            "source": data.root.id,
            "target": branch.id,
            "type": "straight",
            "style": { "stroke": "#93C5FD", "strokeWidth": 2 }
        })
        
        n_leaves = len(branch.children)
        for j, leaf in enumerate(branch.children):
            # Posisi daun menyebar dari cabangnya
            # Jika 1 daun, sejajar lurus. Jika banyak, menyebar kipas.
            if n_leaves > 1:
                leaf_angle = angle + (math.pi / 4) * (j - (n_leaves - 1) / 2)
            else:
                 leaf_angle = angle
                 
            leaf_radius = 150
            leaf_x = x + leaf_radius * math.cos(leaf_angle)
            leaf_y = y + leaf_radius * math.sin(leaf_angle)
            positions[leaf.id] = (round(leaf_x), round(leaf_y))
            
            # Edge Branch -> Leaf
            edges.append({
                "id": f"e-{branch.id}-{leaf.id}",
                "source": branch.id,
                "target": leaf.id,
                "type": "straight",
                "style": { "stroke": "#D1D5DB", "strokeWidth": 1 }
            })
            
            nodes.append({
                "id": leaf.id,
                "type": "mindMapLeaf",
                "position": {"x": positions[leaf.id][0], "y": positions[leaf.id][1]},
                "data": {"label": leaf.label, "depth": 2}
            })
            
        nodes.append({
            "id": branch.id,
            "type": "mindMapBranch",
            "position": {"x": positions[branch.id][0], "y": positions[branch.id][1]},
            "data": {"label": branch.label, "depth": 1}
        })

    # Tambahkan Root terakhir supaya dirender paling atas (atau sesuai order ReactFlow)
    nodes.append({
        "id": data.root.id,
        "type": "mindMapRoot",
        "position": {"x": canvas_center[0], "y": canvas_center[1]},
        "data": {"label": data.root.label}
    })
    
    return nodes, edges

def _convert_cornell(data: schemas.CornellSchema) -> Tuple[list, list]:
    nodes = []
    edges = [] # Cornell tidak butuh edge
    
    start_y = 80
    row_height = 100 # Jarak antar baris
    
    # Cues
    for i, cue in enumerate(data.cues):
         # Menggunakan row_index dari AI atau urutan indeks
         y_pos = start_y + (cue.row_index * row_height)
         nodes.append({
             "id": cue.id,
             "type": "cornellCue",
             "position": {"x": 20, "y": y_pos},
             "data": {"label": cue.keyword, "rowIndex": cue.row_index}
         })
         
    # Notes
    for note in data.notes:
        # Cari cue yang pasangannya untuk menentukan y_pos
        cue_match = next((c for c in data.cues if c.id == note.cue_id), None)
        y_pos = start_y + (cue_match.row_index * row_height) if cue_match else start_y
        nodes.append({
             "id": note.id,
             "type": "cornellNote",
             "position": {"x": 230, "y": y_pos},
             "data": {"label": note.content, "cueId": note.cue_id}
         })
        
    # Summary (Paling Bawah)
    max_row = max((c.row_index for c in data.cues), default=0)
    summary_y = start_y + ((max_row + 2) * row_height)
    nodes.append({
        "id": "cs_summary",
        "type": "cornellSummary",
        "position": {"x": 20, "y": summary_y},
        "data": {"label": data.summary}
    })
    
    return nodes, edges

def _convert_boxing(data: schemas.BoxingSchema) -> Tuple[list, list]:
    nodes = []
    edges = [] # Boxing tidak butuh edge, melainkan hirarki parent-child
    
    # Layout kotak-kotak secara grid
    cols = 2
    box_width = 350
    box_height = 250
    margin_x = 50
    margin_y = 50
    
    for i, group in enumerate(data.groups):
        col = i % cols
        row = i // cols
        
        group_x = 20 + col * (box_width + margin_x)
        group_y = 80 + row * (box_height + margin_y)
        
        # Parent Node (Box)
        nodes.append({
            "id": group.id,
            "type": "boxingGroup",
            "position": {"x": group_x, "y": group_y},
            "data": {"label": group.topic, "color": group.color},
            "style": {"width": box_width, "height": box_height}
        })
        
        # Child Nodes (Items di dalam box)
        item_start_y = 50 # Relatif terhadap Parent
        for j, item in enumerate(group.items):
             nodes.append({
                 "id": item.id,
                 "type": "boxingItem",
                 "position": {"x": 20, "y": item_start_y + (j * 40)},
                 "data": {"label": item.content},
                 "parentId": group.id,
                 "extent": "parent" # Membatasi drag item di dalam parent
             })
             
    return nodes, edges

def _convert_charting(data: schemas.ChartingSchema) -> Tuple[list, list]:
    nodes = []
    edges = []
    
    col_width = 200
    row_height = 80
    start_x = 0
    start_y = 0
    
    # Headers
    for i, header in enumerate(data.headers):
        nodes.append({
            "id": f"ch_header_{i}",
            "type": "chartingHeader",
            "position": {"x": start_x + (i * col_width), "y": start_y},
            "data": {"label": header}
        })
        
    # Data Rows
    for r_idx, row_data in enumerate(data.rows):
        y_pos = start_y + ((r_idx + 1) * row_height)
        for c_idx, cell_value in enumerate(row_data):
             nodes.append({
                 "id": f"ch_cell_{r_idx}_{c_idx}",
                 "type": "chartingCell",
                 "position": {"x": start_x + (c_idx * col_width), "y": y_pos},
                 "data": {"label": cell_value}
             })
             
    return nodes, edges

def _convert_zettelkasten(data: schemas.ZettelkastenSchema) -> Tuple[list, list]:
    nodes = []
    edges = []
    
    # Simple grid layout (krn perhitungan force-directed layout susah kalau murni algoritma sini, 
    # bisa dilempar ke FE atau ditata simpel)
    cols = 3
    margin = 300
    
    for i, atom in enumerate(data.atoms):
        col = i % cols
        row = i // cols
        nodes.append({
            "id": f"z_{atom.id}",
            "type": "zettelAtom",
            "position": {"x": 50 + col * margin, "y": 80 + row * margin},
            "data": {"label": atom.content, "code": atom.id}
        })
        
        # Buat koneksi dari links
        for target_id in atom.links:
             edges.append({
                 "id": f"e-z_{atom.id}-z_{target_id}",
                 "source": f"z_{atom.id}",
                 "target": f"z_{target_id}",
                 "type": "step",
                 "markerEnd": {"type": "ArrowClosed"}
             })
             
    return nodes, edges

def _convert_sketchnoting(data: schemas.SketchnotingSchema) -> Tuple[list, list]:
    nodes = []
    edges = []
    
    # Pemetaan hint ke koordinat (kasar)
    # Layar diasumsikan lebar 800x600
    hint_map = {
        "top-left": (50, 50),
        "top-center": (350, 50),
        "top-right": (650, 50),
        "center-left": (50, 250),
        "center": (350, 250),
        "center-right": (650, 250),
        "bottom-left": (50, 450),
        "bottom-center": (350, 450),
        "bottom-right": (650, 450),
    }
    
    for i, sk in enumerate(data.nodes):
        # Ambil posisi dari hint, fallback ke tengah
        base_x, base_y = hint_map.get(sk.position_hint, (350, 250))
        
        # Tambahkan sedikit offset berdasar index agar tidak persis bertumpuk
        # jika hintnya sama
        offset = i * 20 
        
        nodes.append({
            "id": sk.id,
            "type": "sketchNode",
            "position": {"x": base_x + offset, "y": base_y + offset},
            "data": {
                "label": sk.content, 
                "icon": sk.icon, 
                "importance": sk.importance
            }
        })
        
    return nodes, edges

def _convert_feynman(data: schemas.FeynmanSchema) -> Tuple[list, list]:
    nodes = []
    edges = []
    
    start_x = 200
    y_step = 140
    
    steps = [
        {"id": "fy_concept", "label": "The Concept", "content": data.concept, "step": 1},
        {"id": "fy_simple", "label": "Simple Explanation", "content": data.simple_explanation, "step": 2},
        {"id": "fy_gap", "label": "Gap Identification", "content": "\n".join(f"- {g}" for g in data.gaps), "step": 3},
        {"id": "fy_analogy", "label": "Analogy", "content": data.analogy, "step": 4},
    ]
    
    for i, step_data in enumerate(steps):
        nodes.append({
            "id": step_data["id"],
            "type": "feynmanStep",
            "position": {"x": start_x, "y": 20 + i * y_step},
            "data": step_data
        })
        
        # Edge berurutan dari atas ke bawah
        if i > 0:
            edges.append({
                "id": f"e-{steps[i-1]['id']}-{step_data['id']}",
                "source": steps[i-1]["id"],
                "target": step_data["id"],
                "type": "bezier",
                "style": {"strokeWidth": 3}
            })
            
    # Refinement Notes (Mendampingi step 3 - Gap)
    ref_y_start = 20 + 2 * y_step 
    for i, ref in enumerate(data.refinement_notes):
        ref_id = f"fy_ref_{i}"
        nodes.append({
            "id": ref_id,
            "type": "feynmanRef",
            "position": {"x": start_x + 350, "y": ref_y_start + (i * 60)},
            "data": {"label": ref}
        })
        # Hubungkan ke node gap
        edges.append({
            "id": f"e-{ref_id}-fy_gap",
            "source": ref_id,
            "target": "fy_gap",
            "type": "straight"
        })
        
    return nodes, edges
