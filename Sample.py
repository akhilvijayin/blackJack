#!/usr/bin/env python3
import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import argparse

# Parse arguments
parser = argparse.ArgumentParser(description="Generate beautiful dashboard from Robot Framework log.html")
parser.add_argument("log_file", help="Path to Robot Framework log.html")
parser.add_argument("-o", "--output", default="robot_dashboard.html", help="Output HTML file (default: robot_dashboard.html)")
args = parser.parse_args()

LOG_FILE = args.log_file
OUTPUT_FILE = args.output

if not os.path.exists(LOG_FILE):
    print(f"Error: {LOG_FILE} not found!")
    exit(1)

# Parse log.html (it's actually XML with embedded JSON)
tree = ET.parse(LOG_FILE)
root = tree.getroot()

# Extract statistics and metadata
stats_total = root.find(".//total//all")
passed = int(stats_total.find("pass").text)
failed = int(stats_total.find("fail").text)
skipped = int(stats_total.find("skip").text)
total = passed + failed + skipped
pass_rate = (passed / total * 100) if total > 0 else 0

# Metadata
suite = root.find(".//suite")
start_time = root.get("generated")
executor = root.get("generator", "Unknown")
env_info = "Not specified"
robot_version = "Unknown"

# Try to extract from keywords or messages
for msg in root.findall(".//msg"):
    text = msg.text or ""
    if "Environment:" in text:
        env_info = text.split("Environment:")[-1].strip()
    if "Executed by:" in text:
        executor = text.split("Executed by:")[-1].strip()

# Extract suite and test structure
def parse_suite(element):
    suites = []
    for suite_elem in element.findall("suite"):
        suite_data = {
            "name": suite_elem.get("name"),
            "id": suite_elem.get("id"),
            "status": suite_elem.find("status").get("status"),
            "starttime": suite_elem.find("status").get("starttime"),
            "endtime": suite_elem.find("status").get("endtime"),
            "elapsed": suite_elem.find("status").text,
            "tests": [],
            "sub_suites": parse_suite(suite_elem)
        }
        for test_elem in suite_elem.findall("test"):
            test_data = {
                "name": test_elem.get("name"),
                "id": test_elem.get("id"),
                "status": test_elem.find("status").get("status"),
                "starttime": test_elem.find("status").get("starttime"),
                "endtime": test_elem.find("status").get("endtime"),
                "elapsed": test_elem.find("status").text,
                "critical": test_elem.get("critical", "yes")
            }
            suite_data["tests"].append(test_data)
        suites.append(suite_data)
    return suites

all_suites = parse_suite(root)

# Template (embedded)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Robot Framework Test Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root { --bs-primary-rgb: 13, 110, 253; }
        .dark-mode { background-color: #1a1a1a; color: #e0e0e0; }
        .dark-mode .card { background-color: #2d2d2d; border-color: #444; }
        .dark-mode .table { --bs-table-bg: #2d2d2d; color: #e0e0e0; }
        .dark-mode .table-striped > tbody > tr:nth-of-type(odd) { --bs-table-accent-bg: #333; }
        .status-pass { color: #28a745; }
        .status-fail { color: #dc3545; }
        .status-skip { color: #ffc107; }
        .suite-header { cursor: pointer; background-color: #f8f9fa; }
        .dark-mode .suite-header { background-color: #333; }
        .test-duration { font-size: 0.85em; color: #666; }
        .dark-mode .test-duration { color: #aaa; }
    </style>
</head>
<body class="{{ 'dark-mode' if dark else '' }}">
    <div class="container-fluid py-4">
        <div class="row">
            <div class="col-12 text-center mb-4">
                <h1 class="display-5 fw-bold"><i class="bi bi-robot"></i> Robot Framework Test Report</h1>
                <p class="text-muted">Generated on {{ generated }}</p>
                <button id="darkModeToggle" class="btn btn-outline-secondary btn-sm"><i class="bi bi-moon"></i> Dark Mode</button>
            </div>
        </div>

        <!-- Summary Cards -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-center border-primary">
                    <div class="card-body">
                        <h5 class="card-title">Total Tests</h5>
                        <h2 class="text-primary">{{ total }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center border-success">
                    <div class="card-body">
                        <h5 class="card-title">Passed</h5>
                        <h2 class="text-success">{{ passed }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center border-danger">
                    <div class="card-body">
                        <h5 class="card-title">Failed</h5>
                        <h2 class="text-danger">{{ failed }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center border-warning">
                    <div class="card-body">
                        <h5 class="card-title">Pass Rate</h5>
                        <h2 class="text-warning">{{ "%.2f"|format(pass_rate) }}%</h2>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts -->
        <div class="row mb-4">
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header">Test Status Distribution</div>
                    <div class="card-body">
                        <canvas id="pieChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header">Execution Details</div>
                    <div class="card-body">
                        <table class="table table-sm">
                            <tr><th>Executed By</th><td>{{ executor }}</td></tr>
                            <tr><th>Environment</th><td>{{ env_info }}</td></tr>
                            <tr><th>Start Time</th><td>{{ start_time }}</td></tr>
                            <tr><th>Total Duration</th><td>{{ total_time }}</td></tr>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Search & Suite Tree -->
        <div class="card">
            <div class="card-header">
                <div class="row">
                    <div class="col-md-6"><strong>Test Suites & Cases</strong></div>
                    <div class="col-md-6 text-end">
                        <input type="text" id="searchInput" class="form-control form-control-sm d-inline-block w-75" placeholder="Search tests...">
                    </div>
                </div>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-striped table-hover mb-0" id="testTable">
                        <thead class="table-light">
                            <tr>
                                <th>Suite / Test Case</th>
                                <th>Status</th>
                                <th>Duration</th>
                            </tr>
                        </thead>
                        <tbody id="suiteBody">
                            {% macro render_suite(suite, level=0) %}
                                <tr class="suite-header" data-suite-id="{{ suite.id }}">
                                    <td style="padding-left: {{ level * 25 }}px;">
                                        <i class="bi bi-chevron-right toggle-icon"></i>
                                        <strong>{{ suite.name }}</strong>
                                    </td>
                                    <td><span class="badge bg-{{ 'success' if suite.status == 'PASS' else 'danger' if suite.status == 'FAIL' else 'warning' }}">{{ suite.status }}</span></td>
                                    <td class="test-duration">{{ suite.elapsed }}</td>
                                </tr>
                                {% for test in suite.tests %}
                                    <tr class="test-row suite-{{ suite.id }} d-none">
                                        <td style="padding-left: {{ (level + 1) * 35 }}px;">├─ {{ test.name }}</td>
                                        <td><span class="badge bg-{{ 'success' if test.status == 'PASS' else 'danger' if test.status == 'FAIL' else 'secondary' }}">{{ test.status }}</span></td>
                                        <td class="test-duration">{{ test.elapsed }}</td>
                                    </tr>
                                {% endfor %}
                                {% for subsuite in suite.sub_suites %}
                                    {{ render_suite(subsuite, level + 1) }}
                                {% endfor %}
                            {% endmacro %}

                            {{ render_suite(suites[0]) if suites else "" }}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('darkModeToggle').addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            const icon = this.querySelector('i');
            icon.classList.toggle('bi-moon');
            icon.classList.toggle('bi-sun');
        });

        // Pie Chart
        new Chart(document.getElementById('pieChart'), {
            type: 'doughnut',
            data: {
                labels: ['Passed', 'Failed', 'Skipped'],
                datasets: [{
                    data: [{{ passed }}, {{ failed }}, {{ skipped }}],
                    backgroundColor: ['#28a745', '#dc3545', '#ffc107']
                }]
            },
            options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
        });

        // Toggle suites
        document.querySelectorAll('.suite-header').forEach(header => {
            header.addEventListener('click', function() {
                const suiteId = this.dataset.suiteId;
                document.querySelectorAll(`.suite-${suiteId}`).forEach(row => {
                    row.classList.toggle('d-none');
                });
                this.querySelector('.toggle-icon').classList.toggle('bi-chevron-down');
                this.querySelector('.toggle-icon').classList.toggle('bi-chevron-right');
            });
        });

        // Search
        document.getElementById('searchInput').addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            document.querySelectorAll('#testTable tr').forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            });
        });

        // Auto-expand failed tests
        document.querySelectorAll('.suite-header').forEach(header => {
            if (header.querySelector('.bg-danger')) {
                header.click();
            }
        });
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# Prepare data
total_time = root.find(".//statistics/total/all").text.split()[-1] if root.find(".//statistics/total/all") else "N/A"
generated_time = datetime.now().strftime("%B %d, %Y %I:%M %p")

template_data = {
    "total": total,
    "passed": passed,
    "failed": failed,
    "skipped": skipped,
    "pass_rate": pass_rate,
    "executor": executor,
    "env_info": env_info,
    "start_time": start_time,
    "total_time": total_time,
    "generated": generated_time,
    "suites": all_suites,
    "dark": False
}

# Render template
env = Environment()
template = env.from_string(HTML_TEMPLATE)
rendered_html = template.render(**template_data)

# Save output
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(rendered_html)

print(f"\nDashboard generated successfully!")
print(f"Open {os.path.abspath(OUTPUT_FILE)} in your browser.\n")
print(f"   Features:")
print(f"   • Responsive Design")
print(f"   • Interactive Charts")
print(f"   • Search & Filter")
print(f"   • Expand/Collapse Suites")
print(f"   • Dark Mode")
print(f"   • Auto-expand failed suites")
