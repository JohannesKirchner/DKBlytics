<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import type { CategoryModalMode } from "./types";

  export let mode: CategoryModalMode;
  export let parentName: string | null = null;
  export let loading = false;
  export let error: string | null = null;

  const dispatch = createEventDispatcher<{
    submit: { name: string };
    cancel: void;
  }>();

  let name = "";

  let heading: string;

  $: heading = mode === "root" ? "Add root category" : `Add child to ${parentName}`;

  function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      return;
    }
    dispatch("submit", { name: trimmed });
  }

  function handleCancel() {
    if (!loading) {
      dispatch("cancel");
    }
  }
</script>

<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
  <div class="w-full max-w-sm rounded-lg border bg-white p-5 shadow-xl">
    <header class="mb-4">
      <h2 class="text-lg font-semibold">{heading}</h2>
      {#if mode === "child" && parentName}
        <p class="text-sm text-neutral-600">Child categories inherit from <strong>{parentName}</strong>.</p>
      {/if}
    </header>

    <form class="space-y-3" on:submit|preventDefault={handleSubmit}>
      <div class="space-y-1">
        <label class="block text-sm font-medium" for="category-name">Name</label>
        <input
          id="category-name"
          class="w-full rounded border px-3 py-2 text-sm"
          bind:value={name}
          placeholder="e.g. Groceries"
          autocomplete="off"
          required
          disabled={loading}
        />
      </div>

      {#if error}
        <p class="text-sm text-red-600">{error}</p>
      {/if}

      <div class="flex justify-end space-x-2 text-sm">
        <button
          type="button"
          class="rounded border px-3 py-1"
          on:click={handleCancel}
          disabled={loading}
        >
          Cancel
        </button>
        <button
          type="submit"
          class="rounded bg-blue-600 px-3 py-1 font-medium text-white hover:bg-blue-500 disabled:opacity-60"
          disabled={loading}
        >
          {#if loading}
            Saving…
          {:else}
            Save
          {/if}
        </button>
      </div>
    </form>
  </div>
</div>
