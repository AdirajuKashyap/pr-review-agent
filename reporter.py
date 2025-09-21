from jinja2 import Template

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>PR Review Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 30px; }
    .file { border:1px solid #ddd; padding:12px; margin-bottom:10px; border-radius:6px; }
    .issue { color: #b22222; }
    .score { font-size: 1.4em; font-weight: bold; }
  </style>
</head>
<body>
  <h1>PR Review — {{ pr.repo }} #{{ pr.pr_number }}</h1>
  <p><strong>Title:</strong> {{ pr.title }}</p>
  <p class="score">Score: {{ analysis.final_score }} / 100</p>
  {% for f in analysis.files %}
  <div class="file">
    <h3>{{ f.filename }}</h3>
    {% if f.issues %}
      <ul>
      {% for i in f.issues %}
        <li class="issue">{{ i }}</li>
      {% endfor %}
      </ul>
    {% else %}
      <p>No issues found.</p>
    {% endif %}
  </div>
  {% endfor %}
</body>
</html>
"""

def build_html_report(pr_data, analysis):
    t = Template(HTML_TEMPLATE)
    return t.render(pr=pr_data, analysis=analysis)
