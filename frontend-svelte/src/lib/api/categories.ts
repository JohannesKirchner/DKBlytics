import { apiFetch, type FetchFn } from "$lib/api";
import type {
  Category,
  CategoryCreatePayload,
  CategoryTreeNode,
} from "$lib/types/category";

const BASE_PATH = "/api/categories";

export async function fetchCategories(fetchFn: FetchFn): Promise<Category[]> {
  return apiFetch<Category[]>(fetchFn, `${BASE_PATH}/`);
}

export async function fetchCategoryTree(
  fetchFn: FetchFn,
  params: { name?: string } = {}
): Promise<CategoryTreeNode[]> {
  const search = params.name ? `?name=${encodeURIComponent(params.name)}` : "";
  return apiFetch<CategoryTreeNode[]>(fetchFn, `${BASE_PATH}/tree${search}`);
}

export async function getCategoryByName(
  fetchFn: FetchFn,
  name: string
): Promise<Category> {
  return apiFetch<Category>(fetchFn, `${BASE_PATH}/${encodeURIComponent(name)}`);
}

export async function createCategory(
  fetchFn: FetchFn,
  payload: CategoryCreatePayload
): Promise<Category> {
  return apiFetch<Category>(fetchFn, `${BASE_PATH}/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function deleteCategory(fetchFn: FetchFn, name: string): Promise<void> {
  await apiFetch(fetchFn, `${BASE_PATH}/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
}

export async function updateCategory(): Promise<never> {
  throw new Error(
    "updateCategory is not implemented yet; extend the backend with an update endpoint before calling this helper."
  );
}
