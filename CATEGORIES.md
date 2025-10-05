# Categories Route Walkthrough

This roadmap breaks the Categories screen into small, teachable steps so we can build it confidently in Svelte.

## Goals
- Display the hierarchical category tree returned by the backend.
- Allow creating, renaming, and deleting categories with clear confirmations.
- Surface usage instructions so contributors can follow each step.

## Prerequisites
1. Read through `backend/src/services/categories.py` and the `/api/categories` endpoints so you know the request/response shapes.
2. Confirm the Svelte project runs (`cd frontend-svelte && npm install && npm run dev`) and note the default entry route.
3. Skim a Svelte + TypeScript primer covering components, props, stores, the `$:` reactive statement, and how to type data returned from `load` functions.

## Implementation Steps
1. **Create a Feature Directory**: Under `frontend-svelte/src/routes`, add a `categories/` folder with `+page.svelte` and `+page.ts`. Keeping everything in a dedicated directory makes routing explicit.
2. **Define API Types**: Add `frontend-svelte/src/lib/types/category.ts` exporting TypeScript interfaces (`Category`, `CategoryTreeNode`, etc.) that match the backend schema. These types power editor IntelliSense and guard against payload drift.
3. **Centralize Networking**: In `src/lib/api/`, add a reusable `apiFetch` helper (`index.ts`) and a `categories.ts` module exposing typed helpers (`fetchCategories`, `fetchCategoryTree`, `getCategoryByName`, `createCategory`, `deleteCategory`). Keep an `updateCategory` stub that throws until the backend supports updates, so the calling code can handle the missing capability explicitly.
4. **Add a Writable Store**: Implement `frontend-svelte/src/lib/stores/categories.ts` using Svelte's `writable`. Track `{ isLoading, error, list, tree }`, include a `refresh(fetchFn?)` method that loads both the flat list and the tree in parallel, provide `reset()` for teardown, and `optimisticallyReplace()` to stage UI updates before the server responds. Export a singleton `categoriesStore` for components that prefer importing a ready-made store.
5. **Plan the UI Layout**: Keep the layout focused on the tree. Use a single-column canvas for now with a toolbar above the tree list. Each node presents buttons for “Add child”, “Rename”, and “Delete”. Move detail panels or usage stats to a future enhancement if needed.
6. **Implement Initial Load**: In `frontend-svelte/src/routes/categories/+page.svelte`, import the store, call `categoriesStore.refresh()` inside `onMount`, and derive state with the `$categoriesStore` auto-subscription. Render loading and error states before the tree placeholder so we can verify the plumbing without styling. Use `onDestroy` to reset the store when leaving the page to avoid stale state.
7. **Render the Tree**: Build a recursive `CategoryNode.svelte` component that accepts a category, depth, and callbacks. Use indentation or a tree connector (border-left) to visualize hierarchy and propagate add/rename/delete events.
8. **Hook Up Creation Flow**: Implement a modal or inline form that lets users add root and child categories. Validate input, call `createCategory`, refresh the store (or apply an optimistic append), and close the form on success. Handle backend conflicts (409) by surfacing a friendly message.
9. **Implement Rename Support**: Add a rename form that toggles inline when the button is pressed. Because the backend lacks an update endpoint, decide whether to (a) add one in FastAPI and wire `updateCategory`, or (b) delete + recreate with the new name as a temporary workaround. Record whichever approach you choose.
10. **Wire Deletion**: Use `deleteCategory` to remove nodes. Confirm with the user before deleting, handle ambiguity errors from the backend, and refresh the tree afterward. Consider a soft confirmation (“Deleting '{{name}}' moves all children to root”) once reparenting is supported.
11. **Notification System** (Optional but recommended): Hook in a lightweight toast store (`lib/stores/toast.ts`) delivering success and error feedback. Trigger notifications after every mutation.
12. **Drag-and-Drop (Optional)**: Once create/rename/delete are solid, explore drag-and-drop to reparent nodes. This requires a backend update route, so keep it as a stretch goal.
13. **Accessibility & Keyboard Support**: Ensure buttons have labels, focus states are visible, and keyboard shortcuts (e.g., arrow keys to expand/collapse) are provided for power users.
14. **Testing**: Write Vitest/Playwright checks (if available) that mount the component, mock fetch responses, and verify tree interactions. At minimum, add a `categories.spec.ts` verifying the store logic.
15. **Documentation**: Update `USAGE.md` or create a new doc snippet with screenshots/gifs once the feature works. Annotate any environment variables or backend assumptions you needed.

Follow these steps sequentially; we will tackle each in the codebase with detailed explanations and commit-sized chunks.
