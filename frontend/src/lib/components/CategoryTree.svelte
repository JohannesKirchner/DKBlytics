<script>
    import CategoryTree from './CategoryTree.svelte';

    // receives node (category object) and depth from parent
    const {node, depth=0, last=false} = $props();

    let hovering = $state(false);
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div 
    class="row" 
    style={`padding-left: ${depth * 20}px`} 
    onmouseenter={() => hovering = true}
    onmouseleave={() => hovering = false}
>
    <span class="twig">{depth === 0 ? '•' : (last ? '└─' : '├─')}</span>
    <p class="name">{node.name}</p>

    {#if hovering}
        <form method="POST" action="?/deleteCategory" class="delete-form">
        <input type="hidden" name="name" value={node.name} />
        <button type="submit" title="Delete" class="delete-btn">×</button>
        </form>
    {/if}
</div>

{#if node.children && node.children.length}
    {#each node.children as child, i (child.name)}
        <CategoryTree node={child} depth={depth + 1} last={node.children.length - 1 === i}/>
    {/each}
{/if}

<style>
    .row {
        display: flex;
        align-items: center;
        gap: .35rem;
        line-height: 1.6;
        padding: 2px 0;
        border-radius: 6px;
    }

    .row:hover {
        background: rgba(0, 0, 0, .04);
    }

    .twig {
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        opacity: 0.6;
        width: 1.2rem;
        text-align: right;
    }

    .name {
        font-weight: 600;
    }

    .delete-form { margin-left: auto; }

    .delete-btn {
        background: none;
        border: none;
        color: #888;
        font-size: 1rem;
        line-height: 1;
        cursor: pointer;
        padding: 0 .25rem;
    }
    
    .delete-btn:hover { color: #b00; }
</style>