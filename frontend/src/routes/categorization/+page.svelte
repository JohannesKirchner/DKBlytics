<script>
    import CategoryTree from "$lib/components/CategoryTree.svelte";
    let { data, form } = $props();

    let name = $state(form?.values?.name ?? '');
    let parent_name = $state(form?.values?.parent_name ?? '');
</script>

<form method="POST" action="?/createCategory" onsubmit={(e) => {if (!name.trim()) { e.preventDefault(); }}}>
    <div style="display:flex; gap:.5rem; flex-wrap:wrap; align-items:end;">
        <label>
        <div>Name</div>
        <input name="name" value={name} oninput={(e)=>name = e.currentTarget.value} required />
        </label>

        <label>
        <div>Parent (optional)</div>
        <input name="parent_name" value={parent_name} oninput={(e)=>parent_name = e.currentTarget.value}
                list="known-cats" placeholder="leave empty for top-level" />
        </label>

        <button type="submit" disabled={!name.trim()}>Add</button>
    </div>

    {#if form?.error}
        <p style="color:#b00; margin:.5rem 0 0;">{form.error}</p>
    {/if}
</form>

<hr style="margin:1rem 0;" />

{#if data.categoryTree && data.categoryTree.length}
    {#each data.categoryTree as root (root.name)}
        <CategoryTree node={root} depth={0}/>
    {/each}
{/if}