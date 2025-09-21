PR Review Agent

Overview
PR Review Agent is an AI-powered tool that analyzes GitHub pull requests and provides constructive feedback on code quality, potential bugs, and adherence to coding standards. It supports both live GitHub PR URLs and local diff files.

Features
- Fetch and analyze PRs from GitHub.
- Rule-based analysis for code quality and scoring.
- Generates readable HTML reports of PR changes.
- Optional inline comments for better review.
- Supports local patch/diff analysis (demo_data/sample_diff.patch).

Folder Structure
pr-review-agent/
├─ app.py              # Flask web app
├─ pr_fetcher.py       # Fetch PR data from GitHub or parse local diff
├─ analyzer.py         # Rule-based analyzers
├─ reporter.py         # Generate reports
├─ requirements.txt    # Python dependencies
├─ README.md           # This file
├─ static/             # CSS & JS
├─ templates/          # HTML templates
└─ demo_data/          # Sample diff files

Setup Instructions

1. Clone the repository
git clone <YOUR_REPO_URL>
cd pr-review-agent

2. Create a virtual environment
python -m venv venv

3. Activate the virtual environment
- Windows PowerShell:
.\venv\Scripts\Activate.ps1
- Windows CMD:
.\venv\Scripts\activate.bat
- Linux/Mac:
source venv/bin/activate

4. Install dependencies
pip install -r requirements.txt

5. Set GitHub Token (Optional for private PRs)
- Windows PowerShell:
$env:GITHUB_TOKEN="your_token_here"
- Linux/Mac:
export GITHUB_TOKEN="your_token_here"

6. Run the Flask app
python app.py

7. Access in browser
http://127.0.0.1:8000

Usage
- Enter a GitHub PR URL (e.g., https://github.com/pallets/flask/pull/5618) in the form.
- View the analysis, score, and file-level changes.
- Optionally, analyze local diff files via demo_data/sample_diff.patch.

Contribution
Feel free to fork the repo and submit pull requests for improvements, bug fixes, or additional analysis rules.

License
MIT License
