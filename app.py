import logging
import os
from flask import Flask, request, render_template, jsonify
from pr_fetcher import fetch_github_pr
from analyzer import analyze_pr

# ------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Read configuration from environment
DEBUG_MODE = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
PORT = int(os.environ.get("PORT", 10000))

# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index() -> str:
    """Render home page with form to submit PR URL."""
    return render_template("index.html")

@app.route("/review", methods=["POST"])
def review():
    """Handle PR review requests."""
    pr_url = (request.form.get("pr_url") or "").strip()
    if not pr_url:
        logger.warning("No PR URL provided")
        return jsonify({"error": "No PR URL provided"}), 400

    try:
        logger.info("Fetching PR: %s", pr_url)
        pr_data = fetch_github_pr(pr_url)
        logger.info("Analyzing PR")
        analysis = analyze_pr(pr_data)
        # Pass data to template
        return render_template("result.html", pr_data=pr_data, analysis=analysis)

    except Exception as exc:
        logger.exception("Error while processing PR")
        if DEBUG_MODE:
            # Show detailed error in debug
            return jsonify({"error": str(exc)}), 500
        return jsonify({"error": "Internal Server Error"}), 500

# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG_MODE)
