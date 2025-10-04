# Categories Route Walkthrough

This roadmap breaks the Categories screen into small, teachable steps so we can build it confidently in Svelte.

## Goals
- Display the hierarchical category tree returned by the backend.
- Allow creating, renaming, reparenting, and deleting categories with clear confirmations.
- Surface usage statistics and rule links so users understand the impact of edits before saving.

## Prerequisites
1. Read through `backend/src/services/categories.py` and the `/api/categories` endpoints so you know the request/response shapes.
2. Confirm the Svelte project runs (`cd frontend-svelte && npm install && npm run dev`) and note the default entry route.
3. Skim a Svelte tutorial on components, props, stores, and the `$:` reactive statement; we will rely on those concepts.

## Implementation Steps
1. **Create a Feature Directory**: Under `frontend-svelte/src/routes`, add a `categories/` folder with `+page.svelte` and `+page.js` (if we need server data). Keeping everything in a dedicated directory makes routing explicit.
2. **Define API Shapes**: Add a `category.js` helper in `frontend-svelte/src/lib/types/` that documents the backend payload using JSDoc typedefs. Even without TypeScript, the comments guide development and keep the structure clear.
3. **Centralize Networking**: In `src/lib/api/`, create a `categories.js` module with helper functions (`fetchCategories`, `createCategory`, `updateCategory`, `deleteCategory`). Each should wrap `fetch`, handle JSON parsing, and throw meaningful errors.
4. **Add a Writable Store**: Use Svelte’s `writable` to hold the category list and loading state. Expose actions like `refresh()` and `optimisticallyUpdate()` so any component consuming the tree stays in sync.
5. **Plan the UI Layout**: Sketch the page hierarchy on paper—sidebar for metadata, main panel for the tree, modal slots for editing. This quick design avoids churn once we write markup.
6. **Implement Initial Load**: In `+page.svelte`, call `refresh()` on mount (`onMount`) and show a loading skeleton or spinner until data arrives. Handle network errors with a visible banner describing retry options.
7. **Render the Tree**: Build a recursive `CategoryNode.svelte` component that accepts a category, depth, and callbacks. Use indentation or a tree connector (border-left) to visualize hierarchy. Include action buttons (add child, rename, delete) per node.
8. **Support Drag-and-Drop**: Integrate a lightweight drag library (e.g., the HTML5 API or a Svelte helper) to move nodes. When a drop occurs, call `updateCategory` with the new parent ID and update the store optimistically while showing a toast.
9. **Inline Rename Workflow**: Toggle an editable text input in `CategoryNode` when “Rename” is clicked. On blur or Enter, validate the name, call the API, and restore view mode. Cancel resets to the previous value.
10. **Create Category Modal**: Implement a `CategoryForm.svelte` component with name and parent selectors. Reuse it for both “add root” (parent null) and “add child” flows by passing props.
11. **Deletion Safeguards**: Before deleting, fetch usage counts (or read from cached data). Show a confirmation dialog summarizing affected transactions/rules. Only send `deleteCategory` if the user acknowledges.
12. **Usage and Rules Panel**: Add a detail pane that updates when a node is selected. Display `usage_count`, a link to view related rules, and a list of child counts. This reinforces the impact of edits.
13. **Batch Changes (Optional)**: If we want a diff preview, stage edits locally (array of pending operations) and show them in a footer bar with “Apply” and “Discard” actions. Ensure API calls execute sequentially with rollback on failure.
14. **Notification System**: Hook in a lightweight toast store (`lib/stores/toast.js`) delivering success and error feedback. Trigger notifications after every mutation.
15. **Accessibility & Keyboard Support**: Ensure buttons have labels, focus states are visible, and keyboard shortcuts (e.g., arrow keys to expand/collapse) are provided for power users.
16. **Testing**: Write Vitest/Playwright checks (if available) that mount the component, mock fetch responses, and verify tree interactions. At minimum, add a `categories.spec.js` verifying the store logic.
17. **Documentation**: Update `USAGE.md` or create a new doc snippet with screenshots/gifs once the feature works. Annotate any environment variables or backend assumptions you needed.

Follow these steps sequentially; we will tackle each in the codebase with detailed explanations and commit-sized chunks.
