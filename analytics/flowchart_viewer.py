import streamlit as st
import streamlit.components.v1 as components
import json

def render_interactive_mermaid(mermaid_code: str, height: int = 650) -> None:
    """
    Renders an interactive, vector-based Mermaid.js flowchart with pan-and-zoom
    controls, high-resolution SVG/PNG downloads, and clean Inter typography.
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
      <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
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
          background: linear-gradient(180deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.4) 100%);
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
        #mermaid-container {{
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
        }}
        svg {{
          max-width: none !important;
        }}
        .error-box {{
          padding: 20px;
          color: #f87171;
          font-size: 13px;
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
        <div id="mermaid-container">
          <div id="mermaid-target"></div>
        </div>
      </div>

      <script>
        const rawCode = `{escaped_code}`;
        let panZoomInstance = null;

        mermaid.initialize({{
          startOnLoad: false,
          theme: 'neutral',
          securityLevel: 'loose',
          fontFamily: 'Inter, sans-serif',
          fontSize: 12,
          flowchart: {{
            curve: 'basis',
            useMaxWidth: false,
            htmlLabels: true,
            nodeSpacing: 45,
            rankSpacing: 60,
            padding: 15
          }}
        }});

        async function renderDiagram() {{
          try {{
            const {{ svg }} = await mermaid.render('mermaid-svg-render', rawCode);
            const container = document.getElementById('mermaid-target');
            container.innerHTML = svg;

            const svgElement = container.querySelector('svg');
            if (svgElement) {{
              svgElement.style.width = '100%';
              svgElement.style.height = '100%';

              // Initialize pan-zoom
              panZoomInstance = svgPanZoom(svgElement, {{
                zoomEnabled: true,
                controlIconsEnabled: false,
                fit: true,
                center: true,
                minZoom: 0.1,
                maxZoom: 10,
                zoomScaleSensitivity: 0.25,
                dblClickZoomEnabled: false
              }});

              // Toolbar bindings
              document.getElementById('btn-zoom-in').onclick = () => panZoomInstance.zoomIn();
              document.getElementById('btn-zoom-out').onclick = () => panZoomInstance.zoomOut();
              document.getElementById('btn-reset').onclick = () => {{
                panZoomInstance.resetZoom();
                panZoomInstance.center();
              }};
              document.getElementById('btn-fit').onclick = () => {{
                panZoomInstance.fit();
                panZoomInstance.center();
              }};

              // Download SVG
              document.getElementById('btn-svg').onclick = () => {{
                const serializer = new XMLSerializer();
                let source = serializer.serializeToString(svgElement);
                if(!source.match(/^<svg[^>]+xmlns="http\\:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)){{
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
              }};

              // Download PNG via canvas
              document.getElementById('btn-png').onclick = () => {{
                const serializer = new XMLSerializer();
                const svgString = serializer.serializeToString(svgElement);
                const svgBlob = new Blob([svgString], {{ type: 'image/svg+xml;charset=utf-8' }});
                const URL = window.URL || window.webkitURL || window;
                const blobURL = URL.createObjectURL(svgBlob);
                const image = new Image();
                image.onload = () => {{
                  const canvas = document.createElement('canvas');
                  const scale = 2.0; // Higher resolution
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
                <b>Unable to render interactive diagram:</b> ${{err.message}}
              </div>
            `;
          }}
        }}

        window.addEventListener('DOMContentLoaded', renderDiagram);
      </script>
    </body>
    </html>
    """

    components.html(html_content, height=height + 15, scrolling=False)
