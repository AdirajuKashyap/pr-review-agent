from flask import Flask, request, render_template
from pr_fetcher import fetch_github_pr
from analyzer import analyze_pr

app = Flask(__name__)

@app.route("/")
def index():
    # Show the form to enter PR URL
    return render_template("index.html")

@app.route("/review", methods=["POST"])
def review():
    pr_url = request.form.get("pr_url", "").strip()
    if not pr_url:
        return "PR URL is required", 400

    try:
        # Fetch PR data from GitHub
        pr_data = fetch_github_pr(pr_url)

        # Analyze the PR using analyzer.py
        analysis = analyze_pr(pr_data)

        # Render the results using result.html
        return render_template("result.html", pr_data=pr_data, analysis=analysis)

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
