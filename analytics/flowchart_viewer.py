import streamlit as st
import streamlit.components.v1 as components
import json

def render_interactive_mermaid(mermaid_code: str, height: int = 650) -> None:
    """
    Renders an interactive, vector-based Mermaid.js flowchart with pan-and-zoom
    controls, high-resolution SVG/PNG downloads, and clean Inter typography.
    Uses native GPU CSS transform pan/zoom to prevent matrix inversion bugs on hidden tabs.
    """
    # Sanitize string for embedding inside JavaScript template literal
    escaped_code = mermaid_code.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
      <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
      <style>
        * {{
          box-sizing: border-box;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }}
        body {{
          margin: 0;
          padding: 0;
          background-color: transparent;
          color: #f8fafc;
          overflow: hidden;
        }}
        #diagram-wrapper {{
          position: relative;
          width: 100%;
          height: {height}px;
          background: linear-gradient(180deg, rgba(15, 23, 42, 0.75) 0%, rgba(30, 41, 59, 0.55) 100%);
          border: 1px solid rgba(148, 163, 184, 0.2);
          border-radius: 10px;
          overflow: hidden;
          box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.25);
        }}
        #toolbar {{
          position: absolute;
          top: 12px;
          right: 12px;
          z-index: 100;
          display: flex;
          gap: 6px;
          background: rgba(15, 23, 42, 0.85);
          backdrop-filter: blur(8px);
          padding: 4px 6px;
          border-radius: 8px;
          border: 1px solid rgba(148, 163, 184, 0.25);
        }}
        .tool-btn {{
          background: rgba(255, 255, 255, 0.06);
          color: #cbd5e1;
          border: 1px solid rgba(148, 163, 184, 0.2);
          padding: 5px 10px;
          border-radius: 5px;
          font-size: 11px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s ease;
          display: inline-flex;
          align-items: center;
          gap: 4px;
        }}
        .tool-btn:hover {{
          background: rgba(56, 189, 248, 0.15);
          color: #38bdf8;
          border-color: rgba(56, 189, 248, 0.4);
        }}
        #hint {{
          position: absolute;
          bottom: 10px;
          left: 14px;
          font-size: 11px;
          color: #94a3b8;
          pointer-events: none;
          z-index: 90;
          background: rgba(15, 23, 42, 0.7);
          padding: 3px 8px;
          border-radius: 4px;
          border: 1px solid rgba(148, 163, 184, 0.15);
        }}
        #viewport-stage {{
          width: 100%;
          height: 100%;
          overflow: hidden;
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: grab;
          user-select: none;
        }}
        #viewport-stage:active {{
          cursor: grabbing;
        }}
        #panzoom-layer {{
          transform-origin: center center;
          transition: transform 0.05s ease-out;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 100%;
          height: 100%;
        }}
        #mermaid-target {{
          display: flex;
          align-items: center;
          justify-content: center;
          width: 100%;
          height: 100%;
        }}
        #mermaid-target svg {{
          max-width: 95% !important;
          max-height: 90% !important;
          width: auto !important;
          height: auto !important;
          display: block !important;
          filter: drop-shadow(0 4px 12px rgba(0,0,0,0.35));
        }}
        .error-box {{
          padding: 24px;
          color: #f87171;
          font-size: 13px;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          border-radius: 8px;
          max-width: 80%;
          line-height: 1.5;
        }}
      </style>
    </head>
    <body>
      <div id="diagram-wrapper">
        <div id="toolbar">
          <button class="tool-btn" id="btn-zoom-in" title="Zoom In">➕ In</button>
          <button class="tool-btn" id="btn-zoom-out" title="Zoom Out">➖ Out</button>
          <button class="tool-btn" id="btn-reset" title="Reset View">⟲ Reset</button>
          <button class="tool-btn" id="btn-fit" title="Fit to Canvas">↔ Fit</button>
          <button class="tool-btn" id="btn-svg" title="Download SVG">📥 SVG</button>
          <button class="tool-btn" id="btn-png" title="Download PNG">📥 PNG</button>
        </div>
        <div id="hint">💡 Drag canvas to pan &bull; Scroll wheel to zoom</div>
        <div id="viewport-stage">
          <div id="panzoom-layer">
            <div id="mermaid-target"></div>
          </div>
        </div>
      </div>

      <script>
        const rawCode = `{escaped_code}`;
        let isPanning = false;
        let startX = 0, startY = 0;
        let panX = 0, panY = 0;
        let zoom = 1.0;

        const stage = document.getElementById('viewport-stage');
        const layer = document.getElementById('panzoom-layer');

        function applyTransform() {{
          if (layer) {{
            layer.style.transform = `translate(${{panX}}px, ${{panY}}px) scale(${{zoom}})`;
          }}
        }}

        mermaid.initialize({{
          startOnLoad: false,
          theme: 'dark',
          securityLevel: 'loose',
          fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
          themeVariables: {{
            darkMode: true,
            background: 'transparent',
            primaryColor: '#1e293b',
            primaryTextColor: '#f8fafc',
            primaryBorderColor: '#64748b',
            lineColor: '#38bdf8',
            secondaryColor: '#334155',
            tertiaryColor: '#0f172a'
          }},
          flowchart: {{
            curve: 'basis',
            useMaxWidth: true,
            htmlLabels: true,
            nodeSpacing: 45,
            rankSpacing: 60,
            padding: 15
          }}
        }});

        async function renderDiagram() {{
          try {{
            const renderId = 'mermaid_' + Math.random().toString(36).substring(2, 9);
            const {{ svg }} = await mermaid.render(renderId, rawCode);
            const container = document.getElementById('mermaid-target');
            container.innerHTML = svg;

            // Bind panning gestures
            stage.addEventListener('mousedown', (e) => {{
              if (e.target.closest('#toolbar') || e.target.closest('button')) return;
              isPanning = true;
              startX = e.clientX - panX;
              startY = e.clientY - panY;
              stage.style.cursor = 'grabbing';
            }});

            window.addEventListener('mousemove', (e) => {{
              if (!isPanning) return;
              panX = e.clientX - startX;
              panY = e.clientY - startY;
              applyTransform();
            }});

            window.addEventListener('mouseup', () => {{
              isPanning = false;
              stage.style.cursor = 'grab';
            }});

            // Wheel zoom
            stage.addEventListener('wheel', (e) => {{
              e.preventDefault();
              const factor = e.deltaY < 0 ? 1.15 : 0.87;
              zoom = Math.min(Math.max(zoom * factor, 0.2), 6.0);
              applyTransform();
            }}, {{ passive: false }});

            // Toolbar buttons
            document.getElementById('btn-zoom-in').onclick = () => {{
              zoom = Math.min(zoom * 1.25, 6.0);
              applyTransform();
            }};
            document.getElementById('btn-zoom-out').onclick = () => {{
              zoom = Math.max(zoom * 0.8, 0.2);
              applyTransform();
            }};
            document.getElementById('btn-reset').onclick = () => {{
              zoom = 1.0;
              panX = 0;
              panY = 0;
              applyTransform();
            }};
            document.getElementById('btn-fit').onclick = () => {{
              zoom = 1.0;
              panX = 0;
              panY = 0;
              applyTransform();
            }};

            // Download SVG
            document.getElementById('btn-svg').onclick = () => {{
              const svgElement = container.querySelector('svg');
              if (!svgElement) return;
              const serializer = new XMLSerializer();
              let source = serializer.serializeToString(svgElement);
              if (!source.match(/^<svg[^>]+xmlns="http\\:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)) {{
                source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
              }}
              const blob = new Blob([source], {{ type: 'image/svg+xml;charset=utf-8' }});
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = 'FieldAI_Process_Flowchart.svg';
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              setTimeout(() => URL.revokeObjectURL(url), 1000);
            }};

            // Download PNG via canvas
            document.getElementById('btn-png').onclick = () => {{
              const svgElement = container.querySelector('svg');
              if (!svgElement) return;
              const serializer = new XMLSerializer();
              const svgString = serializer.serializeToString(svgElement);
              const svgBlob = new Blob([svgString], {{ type: 'image/svg+xml;charset=utf-8' }});
              const blobURL = URL.createObjectURL(svgBlob);
              const image = new Image();
              image.onload = () => {{
                const canvas = document.createElement('canvas');
                const scale = 2.0; // High resolution
                const w = (svgElement.viewBox && svgElement.viewBox.baseVal && svgElement.viewBox.baseVal.width) || svgElement.clientWidth || 1000;
                const h = (svgElement.viewBox && svgElement.viewBox.baseVal && svgElement.viewBox.baseVal.height) || svgElement.clientHeight || 1200;
                canvas.width = w * scale;
                canvas.height = h * scale;
                const context = canvas.getContext('2d');
                context.fillStyle = '#0f172a';
                context.fillRect(0, 0, canvas.width, canvas.height);
                context.drawImage(image, 0, 0, canvas.width, canvas.height);
                const pngUrl = canvas.toDataURL('image/png');
                const a = document.createElement('a');
                a.href = pngUrl;
                a.download = 'FieldAI_Process_Flowchart.png';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                setTimeout(() => URL.revokeObjectURL(blobURL), 1000);
              }};
              image.src = blobURL;
            }};

          }} catch (err) {{
            console.error('Mermaid render error:', err);
            document.getElementById('mermaid-target').innerHTML = `
              <div class="error-box">
                <h4 style="margin: 0 0 8px 0; color: #f87171;">Diagram Rendering Notice</h4>
                <div style="font-size: 12px; color: #cbd5e1;">${{err.message || 'Syntax or rendering error in flowchart specification.'}}</div>
              </div>
            `;
          }}
        }}

        if (document.readyState === 'loading') {{
          document.addEventListener('DOMContentLoaded', renderDiagram);
        }} else {{
          renderDiagram();
        }}
      </script>
    </body>
    </html>
    """

    components.html(html_content, height=height + 15, scrolling=False)
                image.onload = () => {{
                  const canvas = document.createElement('canvas');
                  const scale = 2.0; // High resolution
                  canvas.width = (svgElement.clientWidth || 1200) * scale;
                  canvas.height = (svgElement.clientHeight || 800) * scale;
                  const context = canvas.getContext('2d');
                  context.fillStyle = '#ffffff';
                  context.fillRect(0, 0, canvas.width, canvas.height);
                  context.drawImage(image, 0, 0, canvas.width, canvas.height);
                  const pngUrl = canvas.toDataURL('image/png');
                  const a = document.createElement('a');
                  a.href = pngUrl;
                  a.download = 'FieldAI_Process_Flowchart.png';
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                }};
                image.src = blobURL;
              }};
            }}
          }} catch (err) {{
            console.error('Mermaid render error:', err);
            document.getElementById('mermaid-target').innerHTML = `
              <div class="error-box">
                <h4 style="margin: 0 0 8px 0; color: #f87171;">Diagram Rendering Notice</h4>
                <div style="font-size: 12px; color: #cbd5e1;">${{err.message || 'Syntax or rendering error in flowchart specification.'}}</div>
              </div>
            `;
          }}
        }}

        // Listen for container resize / tab visibility switch
        if (typeof ResizeObserver !== 'undefined') {{
          const observer = new ResizeObserver((entries) => {{
            for (let entry of entries) {{
              if (entry.contentRect.width > 20 && entry.contentRect.height > 20) {{
                if (!panZoomInstance && svgElement) {{
                  setupPanZoom();
                }} else if (panZoomInstance) {{
                  panZoomInstance.resize();
                  panZoomInstance.fit();
                  panZoomInstance.center();
                }}
              }}
            }}
          }});
          observer.observe(document.getElementById('diagram-wrapper'));
        }}

        if (document.readyState === 'loading') {{
          document.addEventListener('DOMContentLoaded', renderDiagram);
        }} else {{
          renderDiagram();
        }}
      </script>
    </body>
    </html>
    """

    components.html(html_content, height=height + 15, scrolling=False)

def render_interactive_cytoscape(
    elements: list,
    orientation: str = "TB",
    curve_style: str = "bezier",
    height: int = 650
) -> None:
    """
    Renders an interactive, high-performance Cytoscape.js flowchart with Dagre hierarchical
    swimlane layout, curved Bézier lines, compact node geometry, draggable elements,
    visible labels, and click-to-inspect audit properties.
    Handles hidden-tab mounting gracefully via ResizeObserver.
    """
    elements_json = json.dumps(elements)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
      <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/dagre@0.8.5/dist/dagre.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.min.js"></script>
      <style>
        * {{
          box-sizing: border-box;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }}
        body {{
          margin: 0;
          padding: 0;
          background-color: transparent;
          color: #f8fafc;
          overflow: hidden;
        }}
        #cy-wrapper {{
          position: relative;
          width: 100%;
          height: {height}px;
          background: linear-gradient(180deg, rgba(15, 23, 42, 0.75) 0%, rgba(30, 41, 59, 0.55) 100%);
          border: 1px solid rgba(148, 163, 184, 0.2);
          border-radius: 10px;
          overflow: hidden;
          box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.25);
        }}
        #cy {{
          width: 100%;
          height: 100%;
          display: block;
        }}
        #toolbar {{
          position: absolute;
          top: 12px;
          right: 12px;
          z-index: 100;
          display: flex;
          gap: 6px;
          background: rgba(15, 23, 42, 0.85);
          backdrop-filter: blur(8px);
          padding: 4px 6px;
          border-radius: 8px;
          border: 1px solid rgba(148, 163, 184, 0.25);
        }}
        .tool-btn {{
          background: rgba(255, 255, 255, 0.06);
          color: #cbd5e1;
          border: 1px solid rgba(148, 163, 184, 0.2);
          padding: 5px 10px;
          border-radius: 5px;
          font-size: 11px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s ease;
          display: inline-flex;
          align-items: center;
          gap: 4px;
        }}
        .tool-btn:hover {{
          background: rgba(56, 189, 248, 0.15);
          color: #38bdf8;
          border-color: rgba(56, 189, 248, 0.4);
        }}
        #hint {{
          position: absolute;
          bottom: 10px;
          left: 14px;
          font-size: 11px;
          color: #94a3b8;
          pointer-events: none;
          z-index: 90;
          background: rgba(15, 23, 42, 0.7);
          padding: 3px 8px;
          border-radius: 4px;
          border: 1px solid rgba(148, 163, 184, 0.15);
        }}
        #inspector {{
          position: absolute;
          bottom: 12px;
          right: 12px;
          width: 320px;
          max-height: 220px;
          background: rgba(15, 23, 42, 0.95);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(56, 189, 248, 0.3);
          border-radius: 8px;
          padding: 12px 14px;
          display: none;
          z-index: 95;
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
          font-size: 12px;
          overflow-y: auto;
        }}
        #inspector h4 {{
          margin: 0 0 6px 0;
          font-size: 13px;
          color: #38bdf8;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }}
        #inspector .close-btn {{
          cursor: pointer;
          color: #94a3b8;
          font-size: 14px;
        }}
        #inspector .close-btn:hover {{
          color: #f87171;
        }}
        .badge-tag {{
          display: inline-block;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 10px;
          margin-top: 4px;
        }}
        .badge-risk {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); }}
        .badge-ctrl {{ background: rgba(34, 197, 94, 0.2); color: #86efac; border: 1px solid rgba(34, 197, 94, 0.4); }}
      </style>
    </head>
    <body>
      <div id="cy-wrapper">
        <div id="toolbar">
          <button class="tool-btn" id="btn-zoom-in" title="Zoom In">➕ In</button>
          <button class="tool-btn" id="btn-zoom-out" title="Zoom Out">➖ Out</button>
          <button class="tool-btn" id="btn-fit" title="Fit to Screen">↔ Fit</button>
          <button class="tool-btn" id="btn-reset" title="Reset View">⟲ Reset</button>
          <button class="tool-btn" id="btn-layout" title="Toggle Layout (Hierarchical vs Organic)">📐 Layout</button>
          <button class="tool-btn" id="btn-png" title="Download High-Res PNG">📥 PNG</button>
          <button class="tool-btn" id="btn-json" title="Download Cytoscape JSON">📥 JSON</button>
        </div>
        <div id="hint">💡 Drag nodes to reposition &bull; Click step to inspect attributes &bull; Scroll wheel to zoom</div>
        <div id="cy"></div>
        <div id="inspector">
          <h4>
            <span id="insp-title">[Step Code]</span>
            <span class="close-btn" id="insp-close">&times;</span>
          </h4>
          <div id="insp-role" style="color: #94a3b8; font-size: 11px; margin-bottom: 6px;"></div>
          <div id="insp-desc" style="line-height: 1.4; color: #e2e8f0;"></div>
          <div id="insp-badges" style="margin-top: 8px;"></div>
        </div>
      </div>

      <script>
        const elementsData = {elements_json};
        const defaultOrientation = '{orientation}';
        const defaultCurve = '{curve_style}';

        let currentLayoutName = 'dagre';
        let cy = null;

        function initCytoscape() {{
          try {{
            if (typeof cytoscapeDagre !== 'undefined') {{
              try {{
                cytoscape.use(cytoscapeDagre);
              }} catch (e) {{
                console.warn('cytoscapeDagre already registered');
              }}
            }}

            cy = cytoscape({{
              container: document.getElementById('cy'),
              elements: elementsData,
              boxSelectionEnabled: false,
              autounselectify: false,
              wheelSensitivity: 0.25,
              style: [
                {{
                  selector: 'node',
                  style: {{
                    'label': 'data(label)',
                    'font-family': 'Inter, sans-serif',
                    'font-weight': 400
                  }}
                }},
                {{
                  selector: 'node.swimlane',
                  style: {{
                    'shape': 'round-rectangle',
                    'background-color': '#1e293b',
                    'background-opacity': 0.65,
                    'border-width': 1.5,
                    'border-color': 'rgba(148, 163, 184, 0.45)',
                    'label': 'data(label)',
                    'text-valign': 'top',
                    'text-halign': 'left',
                    'text-margin-y': 14,
                    'text-margin-x': 18,
                    'font-family': 'Inter, sans-serif',
                    'font-size': 12,
                    'font-weight': 500,
                    'color': '#38bdf8',
                    'padding': 30
                  }}
                }},
                {{
                  selector: 'node.processStep',
                  style: {{
                    'shape': 'round-rectangle',
                    'background-color': '#ffffff',
                    'border-width': 1.5,
                    'border-color': '#475569',
                    'label': 'data(label)',
                    'color': '#0f172a',
                    'font-family': 'Inter, sans-serif',
                    'font-size': 10,
                    'font-weight': 400,
                    'text-wrap': 'wrap',
                    'text-max-width': 180,
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'padding': 12,
                    'width': 'label',
                    'height': 'label',
                    'overlay-opacity': 0
                  }}
                }},
                {{
                  selector: 'node.decisionStep',
                  style: {{
                    'shape': 'diamond',
                    'background-color': '#fffbeb',
                    'border-width': 1.5,
                    'border-color': '#d97706',
                    'label': 'data(label)',
                    'color': '#92400e',
                    'font-family': 'Inter, sans-serif',
                    'font-size': 9,
                    'font-weight': 400,
                    'text-wrap': 'wrap',
                    'text-max-width': 140,
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'padding': 16,
                    'width': 'label',
                    'height': 'label',
                    'overlay-opacity': 0
                  }}
                }},
                {{
                  selector: 'node.startEnd',
                  style: {{
                    'shape': 'round-rectangle',
                    'background-color': '#10b981',
                    'border-width': 1.5,
                    'border-color': '#059669',
                    'label': 'data(label)',
                    'color': '#ffffff',
                    'font-family': 'Inter, sans-serif',
                    'font-size': 11,
                    'font-weight': 500,
                    'padding': 8,
                    'width': 70,
                    'height': 34,
                    'text-valign': 'center',
                    'text-halign': 'center'
                  }}
                }},
                {{
                  selector: 'node.endNode',
                  style: {{
                    'shape': 'round-rectangle',
                    'background-color': '#ef4444',
                    'border-width': 1.5,
                    'border-color': '#dc2626',
                    'label': 'data(label)',
                    'color': '#ffffff',
                    'font-family': 'Inter, sans-serif',
                    'font-size': 11,
                    'font-weight': 500,
                    'padding': 8,
                    'width': 70,
                    'height': 34,
                    'text-valign': 'center',
                    'text-halign': 'center'
                  }}
                }},
                {{
                  selector: 'node.riskBadge',
                  style: {{
                    'shape': 'round-rectangle',
                    'background-color': '#fee2e2',
                    'border-width': 1,
                    'border-color': '#ef4444',
                    'label': 'data(label)',
                    'color': '#991b1b',
                    'font-family': 'Inter, sans-serif',
                    'font-size': 8.5,
                    'font-weight': 400,
                    'padding': 5,
                    'width': 'label',
                    'height': 'label',
                    'text-valign': 'center',
                    'text-halign': 'center'
                  }}
                }},
                {{
                  selector: 'node.unmitigatedRisk',
                  style: {{
                    'shape': 'round-rectangle',
                    'background-color': '#fee2e2',
                    'border-width': 1.5,
                    'border-style': 'dashed',
                    'border-color': '#ef4444',
                    'label': 'data(label)',
                    'color': '#991b1b',
                    'font-family': 'Inter, sans-serif',
                    'font-size': 8.5,
                    'font-weight': 400,
                    'padding': 5,
                    'width': 'label',
                    'height': 'label',
                    'text-valign': 'center',
                    'text-halign': 'center'
                  }}
                }},
                {{
                  selector: 'node.controlBadge',
                  style: {{
                    'shape': 'round-rectangle',
                    'background-color': '#dcfce7',
                    'border-width': 1,
                    'border-color': '#22c55e',
                    'label': 'data(label)',
                    'color': '#166534',
                    'font-family': 'Inter, sans-serif',
                    'font-size': 8.5,
                    'font-weight': 400,
                    'padding': 5,
                    'width': 'label',
                    'height': 'label',
                    'text-valign': 'center',
                    'text-halign': 'center'
                  }}
                }},
                {{
                  selector: 'node:selected',
                  style: {{
                    'border-color': '#38bdf8',
                    'border-width': 2.5,
                    'shadow-blur': 12,
                    'shadow-color': 'rgba(56, 189, 248, 0.4)',
                    'shadow-opacity': 0.8
                  }}
                }},
                {{
                  selector: 'edge.sequenceEdge',
                  style: {{
                    'width': 2,
                    'line-color': '#38bdf8',
                    'target-arrow-color': '#38bdf8',
                    'target-arrow-shape': 'triangle',
                    'curve-style': defaultCurve,
                    'arrow-scale': 1
                  }}
                }},
                {{
                  selector: 'edge.badgeEdge',
                  style: {{
                    'width': 1.2,
                    'line-style': 'dashed',
                    'line-color': '#94a3b8',
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'none'
                  }}
                }}
              ],
              layout: {{
                name: 'dagre',
                rankDir: defaultOrientation,
                nodeSep: 45,
                rankSep: 65,
                edgeSep: 25,
                padding: 35
              }}
            }});

            // Click node to inspect
            cy.on('tap', 'node', function(evt) {{
              const node = evt.target;
              const data = node.data();
              if (data.is_lane) return; // Don't inspect lane container

              const insp = document.getElementById('inspector');
              document.getElementById('insp-title').innerText = data.step_code ? `Step [${{data.step_code}}]` : (data.label || '').replace('\\n', ' ');
              document.getElementById('insp-role').innerText = data.responsible_role ? `Role: ${{data.responsible_role}} | Dept: ${{data.department || 'N/A'}}` : '';
              document.getElementById('insp-desc').innerText = data.description || (data.label || '').replace('\\n', ' ');

              let badgesHtml = '';
              if (data.is_decision) badgesHtml += '<span class="badge-tag badge-ctrl">Decision Gateway</span> ';
              document.getElementById('insp-badges').innerHTML = badgesHtml;

              insp.style.display = 'block';
            }});

            // Click canvas background to close inspector
            cy.on('tap', function(evt) {{
              if (evt.target === cy) {{
                document.getElementById('inspector').style.display = 'none';
              }}
            }});

            document.getElementById('insp-close').onclick = () => {{
              document.getElementById('inspector').style.display = 'none';
            }};

            // Toolbar action listeners
            document.getElementById('btn-zoom-in').onclick = () => cy.zoom(cy.zoom() * 1.25);
            document.getElementById('btn-zoom-out').onclick = () => cy.zoom(cy.zoom() * 0.8);
            document.getElementById('btn-fit').onclick = () => cy.fit(null, 35);
            document.getElementById('btn-reset').onclick = () => {{
              cy.fit(null, 35);
              cy.center();
            }};

            // Toggle Layout
            document.getElementById('btn-layout').onclick = () => {{
              if (currentLayoutName === 'dagre') {{
                currentLayoutName = 'cose';
                cy.layout({{ name: 'cose', animate: true, padding: 35, nodeOverlap: 30 }}).run();
              }} else {{
                currentLayoutName = 'dagre';
                cy.layout({{ name: 'dagre', rankDir: defaultOrientation, nodeSep: 45, rankSep: 65, animate: true, padding: 35 }}).run();
              }}
            }};

            // Export PNG
            document.getElementById('btn-png').onclick = () => {{
              const png64 = cy.png({{ full: true, scale: 2.0, bg: '#0f172a' }});
              const a = document.createElement('a');
              a.href = png64;
              a.download = 'FieldAI_Process_Cytoscape.png';
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
            }};

            // Export JSON
            document.getElementById('btn-json').onclick = () => {{
              const jsonStr = JSON.stringify(cy.json(), null, 2);
              const blob = new Blob([jsonStr], {{ type: 'application/json' }});
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = 'FieldAI_Process_Cytoscape.json';
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
            }};

            // Auto-fit on initial render
            cy.fit(null, 35);

          }} catch (err) {{
            console.error('Cytoscape render error:', err);
            document.getElementById('cy').innerHTML = `<div style="padding:20px; color:#f87171;">Failed to load Cytoscape diagram: ${{err.message}}</div>`;
          }}
        }}

        // Listen for container resize / tab visibility switch
        if (typeof ResizeObserver !== 'undefined') {{
          const cyObserver = new ResizeObserver((entries) => {{
            for (let entry of entries) {{
              if (entry.contentRect.width > 20 && entry.contentRect.height > 20) {{
                if (cy) {{
                  cy.resize();
                  cy.fit(null, 35);
                }}
              }}
            }}
          }});
          cyObserver.observe(document.getElementById('cy-wrapper'));
        }}

        if (document.readyState === 'loading') {{
          document.addEventListener('DOMContentLoaded', initCytoscape);
        }} else {{
          initCytoscape();
        }}
      </script>
    </body>
    </html>
    """

    components.html(html_content, height=height + 15, scrolling=False)
