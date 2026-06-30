---
name: drawio-diagrams
description: >
  Create professional draw.io (diagrams.net) diagrams in XML format (.drawio files).
  Use when asked to create flowcharts, swimlane/cross-functional diagrams, org charts,
  network/system architecture diagrams, UML, BPMN, WBS, Gantt, RACI matrices, risk
  matrices, or any visual diagram in draw.io format — including diagram sources for
  the report (assets/diagram_sources). See references/shape-reference.md for the
  style catalog and examples/ecole-platform-examples.md for project-specific patterns.
---

# Draw.io Diagram Creation

Create professional, pixel-perfect diagrams in draw.io's native XML format.

## Draw.io File Format

Draw.io files are XML-based with the `.drawio` extension (or `.xml`). Basic structure:

```xml
<mxfile host="app.diagrams.net" modified="[timestamp]" agent="Claude" version="24.7.17">
  <diagram id="[unique-id]" name="Page-1">
    <mxGraphModel dx="1434" dy="759" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- Shapes and connectors go here -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Core Concepts

### 1. Cells (mxCell)

Everything is a cell — shapes, connectors, containers, and the root elements.

**Shape:**
```xml
<mxCell id="2" value="Process Step" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
</mxCell>
```

**Connector:**
```xml
<mxCell id="3" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" edge="1" parent="1" source="2" target="4">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### 2. ID Management
- Each cell must have a unique ID; use sequential integers ("2", "3", "4"…)
- IDs "0" and "1" are reserved for the root cells
- Connector `source`/`target` must reference existing shape IDs

### 3. Geometry (mxGeometry)
- `x`, `y`: position (top-left corner); `width`, `height`: dimensions
- `relative="1"` for connectors

### 4. Styling
Semicolon-separated key-value pairs:
- **Shape type**: `rounded=1`, `ellipse`, `rhombus`
- **Colors**: `fillColor=#dae8fc`, `strokeColor=#6c8ebf`, `fontColor=#000000`
- **Text**: `fontSize=12`, `fontStyle=1` (bold=1, italic=2, underline=4)
- **Alignment**: `align=center`, `verticalAlign=middle`

## Common Shape Styles

See `references/shape-reference.md` for the full catalog. Essentials:

- **Process**: `rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;`
- **Decision**: `rhombus;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;`
- **Start/End**: `ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;`
- **Document**: `shape=document;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;`
- **Data**: `shape=parallelogram;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;`
- **Database**: `shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;`
- **Horizontal swimlane**: `swimlane;html=1;startSize=20;fillColor=#f5f5f5;strokeColor=#666666;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;horizontalStack=0;resizeParent=1;collapsible=0;`

## Project-Management Diagram Patterns

### Work Breakdown Structure (WBS)
Hierarchical tree of boxes connected by orthogonal lines, numbered (1.0, 1.1, 1.1.1):
- Level 0 (project): 200x80, dark blue `#1ba1e2`, bold
- Level 1 (deliverables): 160x60, green `#60a917`
- Level 2 (work packages): 140x50, light green `#d5e8d4`
- 40px vertical, 20px horizontal spacing between levels

### RACI Matrix
Grid with tasks as rows, roles as columns. Color coding:
- R (Responsible): `fillColor=#d5e8d4;strokeColor=#82b366;`
- A (Accountable): `fillColor=#dae8fc;strokeColor=#6c8ebf;` (exactly one A per row)
- C (Consulted): `fillColor=#fff2cc;strokeColor=#d6b656;`
- I (Informed): `fillColor=#e1d5e7;strokeColor=#9673a6;`

### Gantt / Network (PERT)
- Timeline bar: `rounded=0;whiteSpace=wrap;html=1;fillColor=#60a917;strokeColor=#2D7600;fontColor=#ffffff;`
- Milestone: `rhombus;whiteSpace=wrap;html=1;fillColor=#fa6800;strokeColor=#C73500;`
- Critical path: `strokeWidth=3;strokeColor=#b85450;` on edges and `fillColor=#f8cecc;strokeColor=#b85450;strokeWidth=3;` on nodes
- Dependencies: `dashed=1;dashPattern=5 5;`

### Risk Matrix (Probability × Impact)
5x5 grid, color-coded zones:
- Low: `#d5e8d4`/`#82b366` · Medium: `#fff2cc`/`#d6b656` · High: `#ffe6cc`/`#d79b00` · Critical: `#f8cecc`/`#b85450`

## Connector Styles

- **Orthogonal**: `edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;`
- **With arrow**: append `endArrow=classic;endFill=1;`
- **Dashed (dependency)**: append `dashed=1;dashPattern=5 5;`
- **Curved**: `curved=1;rounded=1;html=1;jettySize=auto;orthogonalLoop=1;`

## Best Practices

### Layout
- Grid alignment: x/y coordinates in multiples of 10
- Spacing: 20-30px between shapes, 40-50px between rows
- Shape sizes: small 80x40, medium 120x60, large 160x80, XL 200x80
- Swimlane heights: 120-150px single row, +100px per additional row

### Visual Hierarchy
- Start shapes green, end shapes red/dark, decisions orange/yellow, regular processes blue
- Critical path always red with strokeWidth=3
- Use progressively lighter shades for deeper WBS levels

### Readability
- Keep diagrams under 20-25 shapes when possible
- Label all connectors in complex flows (Oui/Non on decisions for French diagrams)
- Consistent shape sizes within the same category
- Add legends for symbols/colors in complex diagrams
- **Language**: report diagrams are in French — match the terminology in `.ai/context/TERMINOLOGY.md`

## Validation Checklist

- [ ] All IDs unique; root cells (0, 1) exist
- [ ] All connectors have valid source/target
- [ ] Swimlane children reference the swimlane as parent
- [ ] Coordinates positive; style strings end with semicolon
- [ ] XML well-formed
- [ ] WBS numbering consistent (1.0, 1.1, 1.1.1)
- [ ] RACI: exactly one A per row, at least one R

## Project Integration

- Save diagram sources to `assets/diagram_sources/` and exported PDFs/PNGs to `assets/diagrams/`
- Follow `.ai/diagrams/RULES.md` (project diagram rules) — it takes precedence on conflicts
- Diagrams referenced in LaTeX via `\cref{fig:...}` — coordinate with the latex-writing skill

## Custom Shape Libraries

When a diagram benefits from specific icons, note the libraries to enable:

```
https://app.diagrams.net/?clibs=Uhttps://jgraph.github.io/drawio-libs/libs/templates.xml
```

Available libraries: Material Design icons, Font Awesome, AWS/Azure/GCP, Kubernetes, Cisco network shapes, wireframe components, avatars. Repository: https://github.com/jgraph/drawio-libs

---

*Adapted for Ecole Platform from a PMP/PMBOK-enhanced drawio skill: foreign examples (BIR tax workflow, InsightPulse architecture) replaced by project examples; PMP exam formulas and charter/RACI text templates dropped as out of scope.*
