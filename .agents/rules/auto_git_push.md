# Automatic GitHub Push Rule

After completing any changes requested by the user, ALWAYS commit and push the changes to GitHub (`origin/main`).
The repository is directly integrated with Render for continuous deployment hosting.

Steps to execute after any code modifications:
1. Run test suite to ensure tests pass: `python -m pytest tests/`
2. Stage and commit all changes with a clear commit message.
3. Push to `origin/main`: `git push origin main`
