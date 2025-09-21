from jinja2 import Template

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>PR Review Report</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    pre { background-color: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; }
    .additions { color: green; font-weight: bold; }
    .deletions { color: red; font-weight: bold; }
    .issue { color: #b22222; }
    .score-bar { height: 25px; font-weight: bold; }
    .card-header strong { font-size: 1rem; }
  </style>
</head>
<body>
<div class="container my-5">
  <h1 class="mb-4">PR Review — {{ pr.repo_name }} #{{ pr.pr_number }}</h1>
  <h4>{{ pr.title }}</h4>

  <div class="my-3">
    <strong>Score:</strong> {{ analysis.final_score }} / 100
    <div class="progress mt-2">
      <div class="progress-bar" role="progressbar" style="width: {{ analysis.final_score }}%;" aria-valuenow="{{ analysis.final_score }}" aria-valuemin="0" aria-valuemax="100">
        {{ analysis.final_score }}%
      </div>
    </div>
  </div>

  <div class="mt-4">
    <h3>File Analysis:</h3>
    {% for file in analysis.files %}
    <div class="card mb-3">
      <div class="card-header">
        <strong>{{ file.filename }}</strong>
        &nbsp; — <span class="additions">+{{ file.additions }}</span> / <span class="deletions">-{{ file.deletions }}</span>
      </div>
      <div class="card-body">
        {% if file.issues %}
          <ul>
          {% for issue in file.issues %}
            <li class="issue"><strong>{{ issue.type }}</strong>: {{ issue.detail }}</li>
          {% endfor %}
          </ul>
        {% else %}
          <p>No issues found.</p>
        {% endif %}
        {% if file.patch %}
        <button class="btn btn-sm btn-outline-primary mt-2" type="button" data-bs-toggle="collapse" data-bs-target="#patch{{ loop.index }}" aria-expanded="false" aria-controls="patch{{ loop.index }}">
          Show Patch
        </button>
        <div class="collapse mt-2" id="patch{{ loop.index }}">
          <pre>{{ file.patch }}</pre>
        </div>
        {% endif %}
      </div>
    </div>
    {% endfor %}
  </div>

  <a href="/" class="btn btn-secondary mt-3">Analyze another PR</a>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

def build_html_report(pr_data, analysis):
    t = Template(HTML_TEMPLATE)
    return t.render(pr=pr_data, analysis=analysis)
