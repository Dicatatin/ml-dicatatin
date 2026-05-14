import asyncio
import logging
import math
from pathlib import Path
from typing import Any, Dict, Tuple

import instructor
from openai import AsyncOpenAI
from openai import APITimeoutError, APIError

from app.core.config import get_settings
from app.core.exceptions import InvalidMethodError, LLMTimeoutError
from app.transform import schemas

logger = logging.getLogger(__name__)
settings = get_settings()

# Inisialisasi client OpenAI dengan Instructor
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
        base_prompt = f.read()
        
    latex_instruction = """
PENTING - FORMAT RUMUS & ESTETIKA:
1. Jika terdapat rumus matematika, fisika, atau kimia, WAJIB gunakan format LaTeX dengan mengapit rumus menggunakan $$ (misal: $$E=mc^2$$). Jangan gunakan karakter Unicode khusus, selalu gunakan LaTeX murni.
"""
    return base_prompt + "\n" + latex_instruction

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
        model_name = settings.model_transform
        structured_output = await asyncio.wait_for(
            client.chat.completions.create(
                model=model_name,
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
        


    # Determine bounds for background and header
    if nodes:
        min_x = min(n["position"]["x"] for n in nodes if "position" in n)
        max_x = max(n["position"]["x"] + int(n.get("style", {}).get("width", 200)) for n in nodes if "position" in n)
        min_y = min(n["position"]["y"] for n in nodes if "position" in n)
        max_y = max(n["position"]["y"] + int(n.get("style", {}).get("height", 100)) for n in nodes if "position" in n)
        
        width = max_x - min_x + 400
        height = max_y - min_y + 400
        center_x = min_x + (max_x - min_x) / 2
        
        bg_colors = {
            "mind_map": "#F0F9FF",
            "cornell": "#FAFAF9",
            "boxing": "#F3F4F6",
            "charting": "#F0FDFA",
            "zettelkasten": "#F0FDF4",
            "sketchnoting": "#FEFCE8",
            "feynman": "#FFF1F2"
        }
        bg_color = bg_colors.get(method, "#F8FAFC")
        
        # Add Background Node
        nodes.insert(0, {
            "id": "global_background",
            "type": "methodBackground",
            "position": {"x": min_x - 200, "y": min_y - 200},
            "data": {"label": ""},
            "style": {
                "width": width,
                "height": height,
                "backgroundColor": bg_color,
                "zIndex": -10,
                "borderRadius": "24px",
                "border": "2px dashed #CBD5E1"
            },
            "draggable": False,
            "selectable": False
        })
        
        # Determine Title
        title_text = getattr(data, "title", None)
        if not title_text:
            title_text = getattr(data, "subject", "Catatan AI")
            
        # Add Header Node
        nodes.append({
            "id": "global_header",
            "type": "methodHeader",
            "position": {"x": center_x - 200, "y": min_y - 150},
            "data": {"label": title_text},
            "style": {
                "width": 400,
                "backgroundColor": "#1E293B",
                "color": "#F8FAFC",
                "fontSize": "24px",
                "fontWeight": "bold",
                "textAlign": "center",
                "padding": "15px",
                "borderRadius": "12px",
                "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"
            }
        })
        
    return nodes, edges

# -----------------------------------------------------------------------------
# Konversi Spesifik per Metode (dengan kalkulasi posisi otomatis)
# -----------------------------------------------------------------------------

def _convert_mindmap(data: schemas.MindMapSchema) -> Tuple[list, list]:
    nodes = []
    edges = []
    canvas_center = (400, 300)
    positions = {data.root.id: canvas_center}
    branches = data.root.children
    n_branches = len(branches)
    
    for i, branch in enumerate(branches):
        angle = (2 * math.pi / max(1, n_branches)) * i - (math.pi / 2)
        radius = 250
        x = canvas_center[0] + radius * math.cos(angle)
        y = canvas_center[1] + radius * math.sin(angle)
        positions[branch.id] = (round(x), round(y))
        
        edges.append({
            "id": f"e-{data.root.id}-{branch.id}",
            "source": data.root.id, "target": branch.id,
            "type": "smoothstep",
            "style": { "stroke": "#3B82F6", "strokeWidth": 3 }
        })
        
        n_leaves = len(branch.children)
        for j, leaf in enumerate(branch.children):
            if n_leaves > 1:
                leaf_angle = angle + (math.pi / 3) * (j - (n_leaves - 1) / 2) / max(1, (n_leaves - 1))
            else:
                 leaf_angle = angle
            leaf_radius = 200 + (n_leaves * 10)
            leaf_x = x + leaf_radius * math.cos(leaf_angle)
            leaf_y = y + leaf_radius * math.sin(leaf_angle)
            positions[leaf.id] = (round(leaf_x), round(leaf_y))
            
            edges.append({
                "id": f"e-{branch.id}-{leaf.id}",
                "source": branch.id, "target": leaf.id,
                "type": "smoothstep",
                "style": { "stroke": "#93C5FD", "strokeWidth": 2 }
            })
            
            nodes.append({
                "id": leaf.id, "type": "mindMapLeaf",
                "position": {"x": positions[leaf.id][0], "y": positions[leaf.id][1]},
                "data": {"label": leaf.label, "depth": 2},
                "style": {"backgroundColor": "#EFF6FF", "color": "#1E40AF", "border": "1px solid #BFDBFE", "padding": "10px", "borderRadius": "8px", "width": 150}
            })
            
        nodes.append({
            "id": branch.id, "type": "mindMapBranch",
            "position": {"x": positions[branch.id][0], "y": positions[branch.id][1]},
            "data": {"label": branch.label, "depth": 1},
            "style": {"backgroundColor": "#BFDBFE", "color": "#1E3A8A", "border": "2px solid #60A5FA", "padding": "12px", "borderRadius": "10px", "width": 180, "fontWeight": "bold"}
        })

    nodes.append({
        "id": data.root.id, "type": "mindMapRoot",
        "position": {"x": canvas_center[0], "y": canvas_center[1]},
        "data": {"label": data.root.label},
        "style": {"backgroundColor": "#3B82F6", "color": "#FFFFFF", "border": "3px solid #1D4ED8", "padding": "15px", "borderRadius": "12px", "width": 200, "fontWeight": "bold", "textAlign": "center"}
    })
    return nodes, edges

def _convert_cornell(data: schemas.CornellSchema) -> Tuple[list, list]:
    nodes, edges = [], []
    start_y = 80
    row_height = 150
    
    for i, cue in enumerate(data.cues):
         y_pos = start_y + (i * row_height)
         cue.row_index = i # override to prevent overlapping
         nodes.append({
             "id": cue.id, "type": "cornellCue",
             "position": {"x": 20, "y": y_pos},
             "data": {"label": cue.keyword, "rowIndex": i},
             "style": {"backgroundColor": "#FDBA74", "color": "#7C2D12", "padding": "15px", "borderRadius": "8px", "width": 200, "fontWeight": "bold", "border": "2px solid #EA580C"}
         })
         
    for note in data.notes:
        cue_match = next((c for c in data.cues if c.id == note.cue_id), None)
        y_pos = start_y + (cue_match.row_index * row_height) if cue_match else start_y
        nodes.append({
             "id": note.id, "type": "cornellNote",
             "position": {"x": 260, "y": y_pos},
             "data": {"label": note.content, "cueId": note.cue_id},
             "style": {"backgroundColor": "#FFEDD5", "color": "#9A3412", "padding": "15px", "borderRadius": "8px", "width": 400, "border": "1px solid #FDBA74"}
         })
        
    summary_y = start_y + (len(data.cues) * row_height) + 50
    nodes.append({
        "id": "cs_summary", "type": "cornellSummary",
        "position": {"x": 20, "y": summary_y},
        "data": {"label": data.summary},
        "style": {"backgroundColor": "#F97316", "color": "#FFFFFF", "padding": "20px", "borderRadius": "12px", "width": 640, "fontWeight": "bold", "textAlign": "center"}
    })
    return nodes, edges

def _convert_boxing(data: schemas.BoxingSchema) -> Tuple[list, list]:
    nodes, edges = [], []
    cols = 2
    box_width = 380
    margin_x, margin_y = 60, 60
    
    for i, group in enumerate(data.groups):
        col, row = i % cols, i // cols
        group_x = 20 + col * (box_width + margin_x)
        group_y = 80 + row * (400 + margin_y)
        box_height = max(250, 80 + len(group.items) * 60)
        
        nodes.append({
            "id": group.id, "type": "boxingGroup",
            "position": {"x": group_x, "y": group_y},
            "data": {"label": group.topic, "color": group.color},
            "style": {"width": box_width, "height": box_height, "backgroundColor": "#F8FAFC", "border": f"4px solid {group.color or '#94A3B8'}", "borderRadius": "16px", "paddingTop": "20px"}
        })
        
        item_start_y = 60
        for j, item in enumerate(group.items):
             nodes.append({
                 "id": item.id, "type": "boxingItem",
                 "position": {"x": 20, "y": item_start_y + (j * 55)},
                 "data": {"label": item.content},
                 "parentId": group.id, "extent": "parent",
                 "style": {"backgroundColor": "#FFFFFF", "color": "#1E293B", "padding": "10px", "borderRadius": "8px", "width": box_width - 40, "border": "1px solid #E2E8F0"}
             })
    return nodes, edges

def _convert_charting(data: schemas.ChartingSchema) -> Tuple[list, list]:
    nodes, edges = [], []
    col_width, row_height = 250, 120
    start_x, start_y = 20, 80
    
    for i, header in enumerate(data.headers):
        nodes.append({
            "id": f"ch_header_{i}", "type": "chartingHeader",
            "position": {"x": start_x + (i * col_width), "y": start_y},
            "data": {"label": header},
            "style": {"backgroundColor": "#0F766E", "color": "#FFFFFF", "padding": "15px", "borderRadius": "8px", "width": col_width - 20, "fontWeight": "bold", "textAlign": "center"}
        })
        
    for r_idx, row_data in enumerate(data.rows):
        y_pos = start_y + ((r_idx + 1) * row_height)
        for c_idx, cell_value in enumerate(row_data):
             nodes.append({
                 "id": f"ch_cell_{r_idx}_{c_idx}", "type": "chartingCell",
                 "position": {"x": start_x + (c_idx * col_width), "y": y_pos},
                 "data": {"label": cell_value},
                 "style": {"backgroundColor": "#CCFBF1", "color": "#115E59", "padding": "15px", "borderRadius": "8px", "width": col_width - 20, "border": "1px solid #5EEAD4"}
             })
    return nodes, edges

def _convert_zettelkasten(data: schemas.ZettelkastenSchema) -> Tuple[list, list]:
    nodes, edges = [], []
    cols = max(3, math.ceil(math.sqrt(len(data.atoms))))
    margin = 350
    
    for i, atom in enumerate(data.atoms):
        col, row = i % cols, i // cols
        nodes.append({
            "id": f"z_{atom.id}", "type": "zettelAtom",
            "position": {"x": 50 + col * margin, "y": 80 + row * margin},
            "data": {"label": atom.content, "code": atom.id},
            "style": {"backgroundColor": "#D1FAE5", "color": "#065F46", "padding": "15px", "borderRadius": "12px", "width": 250, "border": "2px solid #059669"}
        })
        
        if not atom.links and i > 0:
             # Fallback if LLM forgets to link
             prev_id = data.atoms[i-1].id
             edges.append({
                 "id": f"e-z_{atom.id}-z_{prev_id}",
                 "source": f"z_{atom.id}", "target": f"z_{prev_id}",
                 "type": "smoothstep",
                 "style": {"stroke": "#10B981", "strokeWidth": 2, "strokeDasharray": "4,4"},
                 "markerEnd": {"type": "ArrowClosed", "color": "#10B981"}
             })
        else:
             for target_id in atom.links:
                  edges.append({
                      "id": f"e-z_{atom.id}-z_{target_id}",
                      "source": f"z_{atom.id}", "target": f"z_{target_id}",
                      "type": "smoothstep",
                      "style": {"stroke": "#10B981", "strokeWidth": 2},
                      "markerEnd": {"type": "ArrowClosed", "color": "#10B981"}
                  })
    return nodes, edges

def _convert_sketchnoting(data: schemas.SketchnotingSchema) -> Tuple[list, list]:
    nodes, edges = [], []
    hint_map = {
        "top-left": (50, 50), "top-center": (350, 50), "top-right": (650, 50),
        "center-left": (50, 300), "center": (350, 300), "center-right": (650, 300),
        "bottom-left": (50, 550), "bottom-center": (350, 550), "bottom-right": (650, 550),
    }
    
    used_positions = []
    for i, sk in enumerate(data.nodes):
        base_x, base_y = hint_map.get(sk.position_hint, (350, 300))
        
        # Collision avoidance
        while any(abs(base_x - ux) < 150 and abs(base_y - uy) < 100 for ux, uy in used_positions):
            base_x += 160
            if base_x > 900:
                base_x = 50
                base_y += 120
                
        used_positions.append((base_x, base_y))
        size = 120 + (sk.importance * 20)
        
        nodes.append({
            "id": sk.id, "type": "sketchNode",
            "position": {"x": base_x, "y": base_y},
            "data": {"label": sk.content, "icon": sk.icon, "importance": sk.importance},
            "style": {"backgroundColor": "#FEF08A", "color": "#854D0E", "padding": "15px", "borderRadius": "16px", "width": size, "border": "2px dashed #EAB308", "textAlign": "center", "fontWeight": "bold"}
        })
        
        # Connect nodes sequentially to create a reading path
        if i > 0:
            prev_id = data.nodes[i-1].id
            edges.append({
                "id": f"e-{prev_id}-{sk.id}",
                "source": prev_id, "target": sk.id,
                "type": "bezier",
                "style": {"stroke": "#CA8A04", "strokeWidth": 3, "strokeDasharray": "5,5"},
                "animated": True
            })
    return nodes, edges

def _convert_feynman(data: schemas.FeynmanSchema) -> Tuple[list, list]:
    nodes, edges = [], []
    start_x, y_step = 200, 180
    
    steps = [
        {"id": "fy_concept", "label": "The Concept", "content": data.concept, "step": 1},
        {"id": "fy_simple", "label": "Simple Explanation", "content": data.simple_explanation, "step": 2},
        {"id": "fy_gap", "label": "Gap Identification", "content": "\n".join(f"- {g}" for g in data.gaps), "step": 3},
        {"id": "fy_analogy", "label": "Analogy", "content": data.analogy, "step": 4},
    ]
    
    for i, step_data in enumerate(steps):
        nodes.append({
            "id": step_data["id"], "type": "feynmanStep",
            "position": {"x": start_x, "y": 80 + i * y_step},
            "data": step_data,
            "style": {"backgroundColor": "#FECDD3", "color": "#881337", "padding": "20px", "borderRadius": "12px", "width": 350, "border": "2px solid #F43F5E", "fontWeight": "bold"}
        })
        
        if i > 0:
            edges.append({
                "id": f"e-{steps[i-1]['id']}-{step_data['id']}",
                "source": steps[i-1]["id"], "target": step_data["id"],
                "type": "smoothstep",
                "style": {"strokeWidth": 3, "stroke": "#FDA4AF"}
            })
            
    ref_y_start = 80 + 2 * y_step 
    for i, ref in enumerate(data.refinement_notes):
        ref_id = f"fy_ref_{i}"
        nodes.append({
            "id": ref_id, "type": "feynmanRef",
            "position": {"x": start_x + 450, "y": ref_y_start + (i * 80)},
            "data": {"label": ref},
            "style": {"backgroundColor": "#FFE4E6", "color": "#9F1239", "padding": "15px", "borderRadius": "8px", "width": 250, "border": "1px dashed #E11D48"}
        })
        edges.append({
            "id": f"e-{ref_id}-fy_gap",
            "source": ref_id, "target": "fy_gap",
            "type": "smoothstep",
            "style": {"stroke": "#FB7185", "strokeDasharray": "5,5"}
        })
    return nodes, edges
