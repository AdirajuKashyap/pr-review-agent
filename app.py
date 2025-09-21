from flask import Flask, request, jsonify, render_template
from pr_fetcher import fetch_github_pr
from github import GithubException

app = Flask(__name__)

# Serve the homepage
@app.route("/")
def home():
    return render_template("index.html")  # templates/index.html must exist

# Handle PR review requests
@app.route("/review", methods=["POST"])
def review():
    pr_url = request.form.get("pr_url")
    if not pr_url:
        return jsonify({"error": "PR URL is required"}), 400
    try:
        pr_data = fetch_github_pr(pr_url)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except GithubException.UnknownObjectException:
        return jsonify({"error": "PR not found or repository is private"}), 404
    except Exception as e:
        # Log error but don't crash
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Something went wrong fetching the PR"}), 500

    return jsonify(pr_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
