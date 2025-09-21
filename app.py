from flask import Flask, render_template, request
from pr_fetcher import fetch_github_pr  # your existing PR fetcher
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/review', methods=['POST'])
def review():
    pr_url = request.form['pr_url']
    try:
        pr_data = fetch_github_pr(pr_url)
    except ValueError:
        return "Invalid GitHub PR URL. Use https://github.com/owner/repo/pull/123"
    
    if not pr_data['files']:
        return "No files found in this PR."

    return render_template('result.html', pr_data=pr_data)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
