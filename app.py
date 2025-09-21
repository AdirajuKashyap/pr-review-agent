from flask import Flask, request, jsonify
from pr_fetcher import fetch_github_pr
from github import GithubException

app = Flask(__name__)

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
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    return jsonify(pr_data)
