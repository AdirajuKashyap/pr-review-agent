from flask import Flask, request, render_template, jsonify
from pr_fetcher import fetch_github_pr
from github import GithubException
import os

app = Flask(__name__)

# Home page
@app.route("/")
def index():
    return render_template("index.html")

# Review PR endpoint
@app.route("/review", methods=["POST"])
def review():
    pr_url = request.form.get("pr_url")
    if not pr_url:
        return jsonify({"error": "PR URL is required"}), 400

    try:
        pr_data = fetch_github_pr(pr_url)
        return jsonify(pr_data)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except GithubException.UnknownObjectException:
        return jsonify({"error": "PR not found or repository is private"}), 404
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

# Run with gunicorn on Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
