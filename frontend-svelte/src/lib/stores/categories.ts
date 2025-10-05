import { writable } from "svelte/store";
import type { Readable } from "svelte/store";
import type { FetchFn } from "$lib/api";
import {
  fetchCategories,
  fetchCategoryTree,
} from "$lib/api/categories";
import type { Category, CategoryTreeNode } from "$lib/types/category";

export interface CategoriesState {
  isLoading: boolean;
  error: string | null;
  list: Category[];
  tree: CategoryTreeNode[];
}

const defaultState: CategoriesState = {
  isLoading: false,
  error: null,
  list: [],
  tree: [],
};

function ensureFetch(fetchFn?: FetchFn): FetchFn {
  if (fetchFn) {
    return fetchFn;
  }
  if (typeof fetch !== "undefined") {
    return fetch;
  }
  throw new Error("No fetch implementation available. Pass a fetch function when calling refresh().");
}

export interface CategoriesStore extends Readable<CategoriesState> {
  refresh(fetchFn?: FetchFn): Promise<void>;
  reset(): void;
  optimisticallyReplace(list: Category[], tree?: CategoryTreeNode[]): void;
}

export function createCategoriesStore(): CategoriesStore {
  const { subscribe, set, update } = writable<CategoriesState>({ ...defaultState });

  return {
    subscribe,
    async refresh(fetchFn?: FetchFn) {
      const requestFetch = ensureFetch(fetchFn);
      update((state) => ({ ...state, isLoading: true, error: null }));

      try {
        const [list, tree] = await Promise.all([
          fetchCategories(requestFetch),
          fetchCategoryTree(requestFetch),
        ]);

        set({ isLoading: false, error: null, list, tree });
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load categories";
        update((state) => ({ ...state, isLoading: false, error: message }));
      }
    },
    reset() {
      set({ ...defaultState });
    },
    optimisticallyReplace(list: Category[], tree: CategoryTreeNode[] = []) {
      update((state) => ({ ...state, list, tree: tree.length ? tree : state.tree }));
    },
  };
}

export const categoriesStore = createCategoriesStore();
