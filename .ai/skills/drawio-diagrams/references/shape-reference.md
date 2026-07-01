# Draw.io Shape Reference Guide

## Flowchart Shapes

**Process Box (Rectangle)**
```
style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
geometry: width="120" height="60"
```

**Decision Diamond**
```
style="rhombus;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;"
geometry: width="100" height="80"
```

**Start/End (Ellipse)**
```
style="ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"
geometry: width="120" height="60"
```

**Document**
```
style="shape=document;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;"
geometry: width="120" height="60"
```

**Data (Parallelogram)**
```
style="shape=parallelogram;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;"
geometry: width="120" height="60"
```

**Manual Process**
```
style="shape=manualInput;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
geometry: width="120" height="60"
```

**Database**
```
style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
geometry: width="60" height="80"
```

## Project-Management Shapes

**WBS Package Box**
```
style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;"
geometry: width="140" height="50"
```

**RACI Cells**
```
R: style="rounded=0;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;fontSize=16;"
A: style="rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;fontSize=16;"
C: style="rounded=0;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontStyle=1;fontSize=16;"
I: style="rounded=0;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontStyle=1;fontSize=16;"
geometry: width="120" height="50"
```

**Risk Cells (low → critical)**
```
Low:      fillColor=#d5e8d4;strokeColor=#82b366;
Medium:   fillColor=#fff2cc;strokeColor=#d6b656;
High:     fillColor=#ffe6cc;strokeColor=#d79b00;
Critical: fillColor=#f8cecc;strokeColor=#b85450;
geometry: width="100" height="100"
```

**Milestone Diamond**
```
style="rhombus;whiteSpace=wrap;html=1;fillColor=#fa6800;strokeColor=#C73500;fontColor=#ffffff;fontStyle=1;"
geometry: width="120" height="80"
```

**Gantt Bar**
```
style="rounded=0;whiteSpace=wrap;html=1;fillColor=#60a917;strokeColor=#2D7600;fontColor=#ffffff;"
geometry: width="200" height="30"
```

## Swimlane Containers

**Horizontal Swimlane**
```
style="swimlane;html=1;startSize=20;fillColor=#f5f5f5;strokeColor=#666666;fontStyle=1;align=center;verticalAlign=top;"
geometry: x="40" y="40" width="760" height="150"
```

**Vertical Swimlane**
```
style="swimlane;html=1;startSize=20;fillColor=#f5f5f5;strokeColor=#666666;horizontal=0;fontStyle=1;"
geometry: x="40" y="40" width="150" height="600"
```

## Connector Styles

```
Basic orthogonal:  edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;
With arrow:        edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=classic;endFill=1;
Dashed:            edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;dashed=1;dashPattern=5 5;
Critical path:     edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=3;strokeColor=#b85450;
Curved:            curved=1;rounded=1;html=1;jettySize=auto;orthogonalLoop=1;endArrow=classic;
Bidirectional:     edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;startArrow=classic;endArrow=classic;
```

## Color Schemes

**Professional Blue** — primary `#dae8fc`/`#6c8ebf`, secondary `#b1ddf0`/`#10739e`, accent `#f8cecc`/`#b85450`

**Green/Natural** — primary `#d5e8d4`/`#82b366`, secondary `#fff2cc`/`#d6b656`, accent `#e1d5e7`/`#9673a6`

**Corporate Gray** — primary `#f5f5f5`/`#666666`, secondary `#e1d5e7`/`#9673a6`, highlight `#ffe6cc`/`#d79b00`

**Ecole Platform layers** (architecture diagrams)
- Frontend (web/mobile): blue `#dae8fc`/`#6c8ebf`
- Backend/API: green `#d5e8d4`/`#82b366`
- Database/storage: purple `#e1d5e7`/`#9673a6`
- Infra/Docker/CI: gray `#f5f5f5`/`#666666`
- External services: orange `#ffe6cc`/`#d79b00`

## Standard Sizes

- Boxes: small 80x40, medium 120x60, large 160x80, XL 200x80
- Diamonds: small 80x60, medium 100x80, large 120x100
- Swimlanes: height 120-150px single row (+100px/row), width 760-800px

## Spacing Guidelines

- Between shapes: 20-30px · between rows: 40-50px
- Swimlanes touch (0px gap)
- Grid alignment: multiples of 10
- Connector padding: 10px from shape edge

## Font Styles

- Title/headers: `fontStyle=1`, `fontSize=14`
- Normal text: `fontStyle=0`, `fontSize=12`
- Small text: `fontSize=10` · code/IDs: `fontSize=9`

## Best Practices

1. Grid alignment (x/y multiples of 10), consistent spacing
2. Appropriate shape for purpose, color consistency within a diagram
3. Label connectors in complex flows (Oui/Non for French decision diagrams)
4. Swimlanes for cross-functional processes
5. Legends for complex diagrams; keep under 25 shapes
6. Test in draw.io before finalizing
