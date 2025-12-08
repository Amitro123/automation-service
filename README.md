# Project

Project description.

## Key Updates:

*   **Dashboard Enhancements:**
    *   Improved the logic for determining Pull Request (PR) runs in the dashboard.  Now correctly identifies PR runs if `trigger_type` starts with 'pr_' OR if a non-null, non-zero `pr_number` exists.
    *   Updated the appearance of the Architecture Panel, including:
        *   Dark mode theme for better visual consistency.
        *   Improved color scheme for readability and aesthetics.
        *   Increased font size for better clarity.
    *   Enhanced Metrics Panel:  Added tooltips to provide more information about LLM token usage and estimated costs.
    *   Updated TaskList component:
        *   Added a tooltip to the progress percentage.
        *   Improved the progress bar appearance.
        *   The progress bar now has a minimum width, ensuring it is always visible.
        *   The progress calculation is now based on ✅ markers in the local `spec.md` file.

*   **Progress Calculation:**
    *   The backend now reads the local `spec.md` file to calculate project progress.  If a local `spec.md` is not found, it falls back to fetching the file from GitHub.
    *   Progress is calculated based on:
        *   Checkbox tasks in `spec.md` (e.g., `- [ ]` and `- [x]`).
        *   ✅ markers indicating completed items in `spec.md`.
        *   Development Log entries (### [...] markers) in `spec.md`.