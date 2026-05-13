import re

transformer_path = r"r:\CODING\WEB DEV\DICATATIN\ml-dicatatin\transform\transformer.py"
with open(transformer_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace _convert_mindmap
mindmap_new = """def _convert_mindmap(data: schemas.MindMapSchema) -> Tuple[list, list]:
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
    return nodes, edges"""
content = re.sub(r'def _convert_mindmap.*?return nodes, edges', mindmap_new, content, flags=re.DOTALL)

# Replace _convert_cornell
cornell_new = """def _convert_cornell(data: schemas.CornellSchema) -> Tuple[list, list]:
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
    return nodes, edges"""
content = re.sub(r'def _convert_cornell.*?return nodes, edges', cornell_new, content, flags=re.DOTALL)

# Replace _convert_boxing
boxing_new = """def _convert_boxing(data: schemas.BoxingSchema) -> Tuple[list, list]:
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
    return nodes, edges"""
content = re.sub(r'def _convert_boxing.*?return nodes, edges', boxing_new, content, flags=re.DOTALL)

# Replace _convert_charting
charting_new = """def _convert_charting(data: schemas.ChartingSchema) -> Tuple[list, list]:
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
    return nodes, edges"""
content = re.sub(r'def _convert_charting.*?return nodes, edges', charting_new, content, flags=re.DOTALL)

# Replace _convert_zettelkasten
zettel_new = """def _convert_zettelkasten(data: schemas.ZettelkastenSchema) -> Tuple[list, list]:
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
        
        for target_id in atom.links:
             edges.append({
                 "id": f"e-z_{atom.id}-z_{target_id}",
                 "source": f"z_{atom.id}", "target": f"z_{target_id}",
                 "type": "smoothstep",
                 "style": {"stroke": "#10B981", "strokeWidth": 2},
                 "markerEnd": {"type": "ArrowClosed", "color": "#10B981"}
             })
    return nodes, edges"""
content = re.sub(r'def _convert_zettelkasten.*?return nodes, edges', zettel_new, content, flags=re.DOTALL)

# Replace _convert_sketchnoting
sketch_new = """def _convert_sketchnoting(data: schemas.SketchnotingSchema) -> Tuple[list, list]:
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
    return nodes, edges"""
content = re.sub(r'def _convert_sketchnoting.*?return nodes, edges', sketch_new, content, flags=re.DOTALL)

# Replace _convert_feynman
feynman_new = """def _convert_feynman(data: schemas.FeynmanSchema) -> Tuple[list, list]:
    nodes, edges = [], []
    start_x, y_step = 200, 180
    
    steps = [
        {"id": "fy_concept", "label": "The Concept", "content": data.concept, "step": 1},
        {"id": "fy_simple", "label": "Simple Explanation", "content": data.simple_explanation, "step": 2},
        {"id": "fy_gap", "label": "Gap Identification", "content": "\\n".join(f"- {g}" for g in data.gaps), "step": 3},
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
    return nodes, edges"""
content = re.sub(r'def _convert_feynman.*?return nodes, edges', feynman_new, content, flags=re.DOTALL)

with open(transformer_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Styles and positions applied")
