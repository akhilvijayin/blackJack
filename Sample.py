#!/usr/bin/env python3
import os
import base64
from datetime import datetime
from xml.etree import ElementTree as ET

def generate_dashboard(results_dir="robot-results", output_file="robot-results/dashboard.html"):
    log_path = os.path.join(results_dir, "log.html")
    report_path = os.path.join(results_dir, "report.html")
    output_xml = os.path.join(results_dir, "output.xml")
    screenshots_dir = os.path.join(results_dir, "screenshots")
    dashboard_path = os.path.join(results_dir, output_file)

    # Parse output.xml for stats
    tree = ET.parse(output_xml)
    root = tree.getroot()
    stats = root.find("statistics").find("total").find("stat")
    total = stats.find("all").text
    passed = stats.find("pass").text
    failed = stats.find("fail").text

    suite = root.find("suite")
    start_time = suite.get("starttime", "Unknown")
    end_time = suite.get("endtime", "Unknown")
    duration = root.find("suite").get("elapsedtime", "0")

    # Format duration
    try:
        secs = int(duration) / 1000
        duration_str = f"{int(secs // 3600)}h {int((secs % 3600) // 60)}m {int(secs % 60)}s"
    except:
        duration_str = duration

    # Read screenshots
    screenshots = []
    if os.path.exists(screenshots_dir):
        for file in sorted(os.listdir(screenshots_dir)):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                path = os.path.join(screenshots_dir, file)
                with open(path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                screenshots.append({
                    "name": file,
                    "data": b64,
                    "ext": file.split('.')[-1]
                })

    # Generate HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Robot Framework Test Dashboard</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {{
                --passed: #28a745;
                --failed: #dc3545;
                --bg: #f8f9fa;
                --card: white;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: var(--bg);
                color: #333;
                margin: 0;
                padding: 20px;
            }}
            .container {{ max-width: 1400px; margin: auto; }}
            .header {{
                text-align: center;
                padding: 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 15px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .stat-card {{
                background: var(--card);
                padding: 25px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                transition: transform 0.3s;
            }}
            .stat-card:hover {{ transform: translateY(-5px); }}
            .stat-card.passed {{ border-left: 5px solid var(--passed); }}
            .stat-card.failed {{ border-left: 5px solid var(--failed); }}
            .number {{ font-size: 3em; font-weight: bold; }}
            .iframe-container {{
                margin: 40px 0;
                border: 1px solid #ddd;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            }}
            iframe {{ width: 100%; height: 800px; border: none; }}
            .screenshots {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                margin: 40px 0;
            }}
            .screenshot {{
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .screenshot img {{ width: 100%; height: auto; }}
            .screenshot-caption {{ padding: 10px; background: #f1f1f1; font-weight: bold; }}
            footer {{ text-align: center; margin-top: 50px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><i class="fas fa-robot"></i> Robot Framework Test Dashboard</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Riyadh Time)</p>
            </div>

            <div class="stats-grid">
                <div class="stat-card passed">
                    <div class="number" style="color:var(--passed)">{passed}</div>
                    <div>Passed</div>
                </div>
                <div class="stat-card failed">
                    <div class="number" style="color:var(--failed)">{failed}</div>
                    <div>Failed</div>
                </div>
                <div class="stat-card">
                    <div class="number">{total}</div>
                    <div>Total Tests</div>
                </div>
                <div class="stat-card">
                    <div class="number">{duration_str}</div>
                    <div>Duration</div>
                </div>
            </div>

            <h2><i class="fas fa-file-alt"></i> Detailed Report</h2>
            <div class="iframe-container">
                <iframe src="report.html"></iframe>
            </div>

            <h2><i class="fas fa-list-ul"></i> Detailed Log</h2>
            <div class="iframe-container">
                <iframe src="log.html"></iframe>
            </div>

            <h2><i class="fas fa-images"></i> Test Execution Screenshots ({len(screenshots)})</h2>
            <div class="screenshots">
                {"".join(f'''
                <div class="screenshot">
                    <img src="data:image/{s["ext"]};base64,{s["data"]}" alt="{s["name"]}">
                    <div class="screenshot-caption">{s["name"]}</div>
                </div>
                ''' for s in screenshots)}
            </div>

            <footer>
                <p>Dashboard auto-generated • Robot Framework + Python</p>
            </footer>
        </div>
    </body>
    </html>
    """

    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard generated: {dashboard_path}")
    print(f"Open file://{os.path.abspath(dashboard_path)} in browser")

if __name__ == "__main__":
    generate_dashboard()
