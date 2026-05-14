"""
transform/schemas.py

Pydantic schemas untuk memvalidasi output dari LLM menggunakan Instructor.
Mendefinisikan struktur data untuk ketujuh metode belajar:
Mind Map, Cornell Notes, Boxing Method, Charting, Zettelkasten, Sketchnoting, dan Feynman.
"""

from typing import List

from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# 1. Mind Map
# -----------------------------------------------------------------------------
class MindMapNode(BaseModel):
    id: str = Field(description="Unique ID for the node, e.g., 'mm_root', 'mm_branch_1', 'mm_leaf_1_1'")
    label: str = Field(description="Short text label for the node")
    level: int = Field(description="Hierarchy level: 0 = root, 1 = branch, 2 = leaf")
    children: List["MindMapNode"] = Field(default_factory=list, description="Child nodes connected to this node")

class MindMapSchema(BaseModel):
    root: MindMapNode = Field(description="The central root node of the mind map")
    title: str = Field(description="Main title of the notes for the canvas header")

# Resolve forward references
MindMapNode.model_rebuild()

# -----------------------------------------------------------------------------
# 2. Cornell Notes
# -----------------------------------------------------------------------------
class CornellCue(BaseModel):
    id: str = Field(description="Unique ID for the cue, e.g., 'cc1'")
    keyword: str = Field(description="Short keyword or question (left column, 30%)")
    row_index: int = Field(description="Vertical alignment index starting from 0 to match with notes")

class CornellNote(BaseModel):
    id: str = Field(description="Unique ID for the note, e.g., 'cn1'")
    content: str = Field(description="Detailed text explanation (right column, 70%)")
    cue_id: str = Field(description="ID of the corresponding cue this note belongs to")

class CornellSchema(BaseModel):
    title: str = Field(description="Title of the Cornell notes")
    date: str = Field(description="Date in format: DD MMM YYYY")
    cues: List[CornellCue] = Field(description="List of cues (keywords/questions)")
    notes: List[CornellNote] = Field(description="List of detailed notes corresponding to cues")
    summary: str = Field(description="Summary paragraph of the entire material (bottom area)")

# -----------------------------------------------------------------------------
# 3. Boxing Method
# -----------------------------------------------------------------------------
class BoxingItem(BaseModel):
    id: str = Field(description="Unique ID for the item, e.g., 'bi1_1'")
    content: str = Field(description="Content of the bullet point or detail inside the box")

class BoxingGroup(BaseModel):
    id: str = Field(description="Unique ID for the box group, e.g., 'bg1'")
    topic: str = Field(description="Label or title at the top of the box")
    color: str = Field(description="Pastel hex color code for the box background, e.g., '#FEF3C7'")
    items: List[BoxingItem] = Field(description="List of details or bullet points inside this box")

class BoxingSchema(BaseModel):
    title: str = Field(description="Title of the Boxing Method notes")
    groups: List[BoxingGroup] = Field(description="List of thematic box groups")

# -----------------------------------------------------------------------------
# 4. Charting
# -----------------------------------------------------------------------------
class ChartingSchema(BaseModel):
    title: str = Field(description="Title of the Charting notes")
    headers: List[str] = Field(description="List of column names, e.g., ['Aspek', 'Mitosis', 'Meiosis']")
    rows: List[List[str]] = Field(description="Matrix of data cells. rows[i][j] is the value for row i, column j")

# -----------------------------------------------------------------------------
# 5. Zettelkasten
# -----------------------------------------------------------------------------
class ZettelAtom(BaseModel):
    id: str = Field(description="Unique code for the atom, e.g., '1a', '1b', '2a'")
    content: str = Field(description="Content of the atomic idea (1-2 sentences)")
    links: List[str] = Field(description="List of IDs this atom connects to, e.g., ['1a', '2b']")

class ZettelkastenSchema(BaseModel):
    atoms: List[ZettelAtom] = Field(description="List of atomic notes")

# -----------------------------------------------------------------------------
# 6. Sketchnoting
# -----------------------------------------------------------------------------
class SketchNode(BaseModel):
    id: str = Field(description="Unique ID for the sketch node, e.g., 'sk1'")
    content: str = Field(description="Text content of the node")
    importance: int = Field(ge=1, le=5, description="Importance level from 1 to 5, determines node size")
    icon: str = Field(description="Name of a simple SVG icon: 'lightbulb', 'star', 'arrow', 'book', etc.")
    position_hint: str = Field(description="Layout hint: 'top-left', 'center', 'bottom-right', etc.")

class SketchnotingSchema(BaseModel):
    title: str = Field(description="Title of the Sketchnoting canvas")
    nodes: List[SketchNode] = Field(description="List of nodes to be drawn on the canvas")

# -----------------------------------------------------------------------------
# 7. Feynman Technique
# -----------------------------------------------------------------------------
class FeynmanSchema(BaseModel):
    subject: str = Field(description="Name of the main concept being studied")
    concept: str = Field(description="Original, full explanation of the concept")
    simple_explanation: str = Field(description="Simplified explanation, suitable for a beginner")
    gaps: List[str] = Field(description="List of parts that are still hard to understand or missing")
    analogy: str = Field(description="An analogy to make the concept easier to grasp")
    refinement_notes: List[str] = Field(description="Research results or notes to fill the identified gaps")
