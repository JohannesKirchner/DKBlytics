<script lang="ts">
  import type { CategoryTreeNode } from "$lib/types/category";

  export let node: CategoryTreeNode;
  export let depth = 0;
  export let onAddChild: (parent: CategoryTreeNode) => void;
  export let onRename: (target: CategoryTreeNode) => void;
  export let onDelete: (target: CategoryTreeNode) => void;

  const hasChildren = node.children.length > 0;
  const avatar = node.name.charAt(0).toUpperCase();
</script>

<li class="node-container" style={`--depth:${depth}`}>
  <div class="node-card group">
    <div class="node-meta">
      <span class="node-avatar" aria-hidden="true">{avatar}</span>
      <div class="node-text">
        <span class="node-name">{node.name}</span>
        {#if hasChildren}
          <span class="node-subtitle">
            {node.children.length} subcategor{node.children.length === 1 ? "y" : "ies"}
          </span>
        {/if}
      </div>
    </div>

    <div class="node-actions">
      <button class="ghost-button" on:click={() => onAddChild(node)}>
        <span aria-hidden="true">＋</span>
        Add child
      </button>
      <button class="ghost-button" on:click={() => onRename(node)}>
        <span aria-hidden="true">✎</span>
        Rename
      </button>
      <button class="ghost-button danger" on:click={() => onDelete(node)}>
        <span aria-hidden="true">✕</span>
        Delete
      </button>
    </div>
  </div>

  {#if hasChildren}
    <ul class="child-list">
      {#each node.children as child}
        <svelte:self
          node={child}
          depth={depth + 1}
          onAddChild={onAddChild}
          onRename={onRename}
          onDelete={onDelete}
        />
      {/each}
    </ul>
  {/if}
</li>

<style>
  .node-container {
    list-style: none;
    display: grid;
    gap: 0.75rem;
  }

  .node-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    border-radius: 1rem;
    border: 1px solid rgba(148, 163, 184, 0.35);
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(241, 245, 249, 0.9));
    padding: 0.9rem 1.1rem;
    box-shadow: 0 16px 35px -24px rgba(15, 23, 42, 0.45);
    transition: all 0.2s ease;
    margin-left: calc(var(--depth) * 0.75rem);
  }

  .node-card:hover {
    border-color: rgba(59, 130, 246, 0.4);
    box-shadow: 0 20px 42px -22px rgba(37, 99, 235, 0.45);
    transform: translateY(-1px);
  }

  .node-meta {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    min-width: 0;
  }

  .node-avatar {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.4rem;
    height: 2.4rem;
    border-radius: 9999px;
    background: rgba(59, 130, 246, 0.12);
    color: rgb(37, 99, 235);
    font-weight: 600;
    font-size: 1rem;
  }

  .node-text {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    min-width: 0;
  }

  .node-name {
    font-weight: 600;
    color: rgb(30, 41, 59);
    word-break: break-word;
  }

  .node-subtitle {
    color: rgb(100, 116, 139);
    font-size: 0.78rem;
  }

  .node-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .ghost-button {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.45rem 0.85rem;
    border-radius: 9999px;
    border: 1px solid rgba(148, 163, 184, 0.35);
    background: rgba(255, 255, 255, 0.72);
    color: rgb(71, 85, 105);
    font-size: 0.82rem;
    font-weight: 500;
    transition: all 0.15s ease;
  }

  .ghost-button:hover {
    border-color: rgba(37, 99, 235, 0.5);
    color: rgb(37, 99, 235);
    background: rgba(59, 130, 246, 0.1);
  }

  .ghost-button.danger {
    border-color: rgba(248, 113, 113, 0.45);
    color: rgb(220, 38, 38);
  }

  .ghost-button.danger:hover {
    background: rgba(254, 226, 226, 0.65);
    border-color: rgba(248, 113, 113, 0.7);
  }

  .child-list {
    margin-left: 1.2rem;
    padding-left: 1.2rem;
    border-left: 1px solid rgba(148, 163, 184, 0.3);
    display: grid;
    gap: 0.75rem;
  }

  @media (max-width: 640px) {
    .node-card {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .node-actions {
      width: 100%;
      justify-content: flex-start;
    }
  }
</style>
