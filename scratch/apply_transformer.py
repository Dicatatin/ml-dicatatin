import re

transformer_path = r"r:\CODING\WEB DEV\DICATATIN\ml-dicatatin\transform\transformer.py"
with open(transformer_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update load_prompt
latex_instruction = """
PENTING - FORMAT RUMUS:
Jika terdapat rumus matematika, fisika, atau kimia, WAJIB gunakan format LaTeX dengan mengapit rumus menggunakan $$ (misal: $$E=mc^2$$ atau $$\\frac{1}{2}$$). Jangan gunakan karakter Unicode khusus, selalu gunakan LaTeX murni.
"""

load_prompt_replacement = """    with open(prompt_path, "r", encoding="utf-8") as f:
        base_prompt = f.read()
        
    latex_instruction = \"\"\"
PENTING - FORMAT RUMUS & ESTETIKA:
1. Jika terdapat rumus matematika, fisika, atau kimia, WAJIB gunakan format LaTeX dengan mengapit rumus menggunakan $$ (misal: $$E=mc^2$$). Jangan gunakan karakter Unicode khusus, selalu gunakan LaTeX murni.
\"\"\"
    return base_prompt + "\\n" + latex_instruction"""

content = content.replace('    with open(prompt_path, "r", encoding="utf-8") as f:\n        return f.read()', load_prompt_replacement)

# 2. Wrap convert_to_reactflow to add global header, background, and handles
wrapper = """
def calculate_handles(source_x, source_y, target_x, target_y):
    dx = target_x - source_x
    dy = target_y - source_y
    if abs(dx) > abs(dy):
        if dx > 0:
            return "right", "left"
        else:
            return "left", "right"
    else:
        if dy > 0:
            return "bottom", "top"
        else:
            return "top", "bottom"

def convert_to_reactflow(data: Any, method: str) -> Tuple[list, list]:
    \"\"\"
    Mengubah output terstruktur (Pydantic schema) menjadi format 
    nodes dan edges untuk React Flow.
    \"\"\"
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
        
    # Add handles to edges based on position
    node_positions = {n["id"]: n["position"] for n in nodes if "position" in n and n.get("type") != "boxingItem"}
    for e in edges:
        source_id = e.get("source")
        target_id = e.get("target")
        if source_id in node_positions and target_id in node_positions:
            s_pos = node_positions[source_id]
            t_pos = node_positions[target_id]
            sh, th = calculate_handles(s_pos["x"], s_pos["y"], t_pos["x"], t_pos["y"])
            e["sourceHandle"] = sh
            e["targetHandle"] = th

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
"""

content = re.sub(
    r'def convert_to_reactflow.*?return nodes, edges', 
    wrapper.strip(), 
    content, 
    flags=re.DOTALL
)

with open(transformer_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Transformation applied")
