/** Shared TypeScript interfaces for working with backend categories. */

export type CategoryId = number;

/**
 * Category payload returned by `/api/categories`.
 * A category is uniquely identified by its `id` and by a combination
 * of `name` + parent.
 */
export interface Category {
  id: CategoryId;
  name: string;
  parent_name: string | null;
}

/**
 * Recursive node returned by `/api/categories/tree`.
 * Each node only contains its children; parent metadata is implied
 * by the nesting structure.
 */
export interface CategoryTreeNode {
  id: CategoryId;
  name: string;
  children: CategoryTreeNode[];
}

/**
 * Request payload for creating a category through the API.
 * `parent_name` can be omitted to create a root-level category.
 */
export interface CategoryCreatePayload {
  name: string;
  parent_name?: string | null;
}

/**
 * Shape we expect once we extend the API to include usage stats for deletion warnings.
 * These values can remain optional until the backend provides them.
 */
export interface CategoryUsageSummary {
  transaction_count?: number;
  rule_count?: number;
}

/**
 * Convenience union for components that need either a flat list or tree data.
 */
export type CategoryCollection = Category[] | CategoryTreeNode[];
