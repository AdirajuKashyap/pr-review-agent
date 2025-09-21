from flask import Flask, render_template, request
from pr_fetcher import fetch_github_pr  # your existing PR fetcher

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
    
    # Debug: print(pr_data.files)
    return render_template('result.html', pr_data=pr_data)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
