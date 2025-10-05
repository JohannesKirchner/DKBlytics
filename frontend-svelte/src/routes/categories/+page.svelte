<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { categoriesStore } from "$lib/stores/categories";
  import CategoryNode from "$lib/components/categories/CategoryNode.svelte";
  import CategoryModal from "$lib/components/categories/CategoryModal.svelte";
  import type { CategoryModalMode } from "$lib/components/categories/types";
  import { createCategory } from "$lib/api/categories";
  import type { CategoryTreeNode } from "$lib/types/category";

  type ModalState = { mode: CategoryModalMode; parent?: CategoryTreeNode } | null;

  let modal: ModalState = null;
  let modalError: string | null = null;
  let modalLoading = false;

  const handleAddRoot = () => {
    modal = { mode: "root" };
    modalError = null;
  };

  const handleAddChild = (parent: CategoryTreeNode) => {
    modal = { mode: "child", parent };
    modalError = null;
  };

  const handleRename = (node: CategoryTreeNode) => {
    console.log("Rename", node);
  };

  const handleDelete = (node: CategoryTreeNode) => {
    console.log("Delete", node);
  };

  const handleModalCancel = () => {
    modal = null;
    modalError = null;
    modalLoading = false;
  };

  const handleModalSubmit = async (event: CustomEvent<{ name: string }>) => {
    if (!modal) {
      return;
    }

    const { name } = event.detail;
    const parentName = modal.parent?.name ?? null;
    modalLoading = true;
    modalError = null;

    try {
      await createCategory(fetch, { name, parent_name: parentName });
      modal = null;
      await categoriesStore.refresh(fetch);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to create category";
      if (message.includes("409")) {
        modalError = "A category with this name already exists under the chosen parent.";
      } else {
        modalError = message;
      }
    } finally {
      modalLoading = false;
    }
  };

  onMount(() => {
    categoriesStore.refresh();
  });

  onDestroy(() => {
    categoriesStore.reset();
  });
</script>

<main class="categories-page space-y-4">
  <header class="flex items-center justify-between border-b pb-2">
    <div>
      <h1 class="text-2xl font-semibold">Categories</h1>
      <p class="text-sm text-neutral-600">Manage your hierarchy by adding, renaming, or removing nodes.</p>
    </div>
    <button
      class="rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white hover:bg-blue-500"
      on:click={handleAddRoot}
    >
      Add root category
    </button>
  </header>

  {#if $categoriesStore.isLoading}
    <p class="text-neutral-600">Loading categories…</p>
  {:else if $categoriesStore.error}
    <div class="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
      Failed to load categories: {$categoriesStore.error}
      <button
        class="ml-2 underline"
        on:click={() => categoriesStore.refresh()}
        type="button"
      >
        Retry
      </button>
    </div>
  {:else}
    <section class="rounded border bg-white p-4 shadow-sm">
      {#if $categoriesStore.tree.length === 0}
        <p class="text-sm text-neutral-600">No categories found yet. Start by adding a root category.</p>
      {:else}
        <ul class="space-y-2">
          {#each $categoriesStore.tree as node}
            <CategoryNode
              node={node}
              depth={0}
              onAddChild={handleAddChild}
              onRename={handleRename}
              onDelete={handleDelete}
            />
          {/each}
        </ul>
      {/if}
    </section>
  {/if}
</main>

{#if modal}
  <CategoryModal
    mode={modal.mode}
    parentName={modal.parent?.name ?? null}
    loading={modalLoading}
    error={modalError}
    on:cancel={handleModalCancel}
    on:submit={handleModalSubmit}
  />
{/if}
