<script>
	import '../app.css';
	import { page } from '$app/stores';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();

	const links = [
    { href: '/balance', label: 'Balance' },
    { href: '/budget', label: 'Budget' },
    { href: '/transactions', label: 'Transactions' },
    { href: '/categories', label: 'Categories' }
  ];
</script>


<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>


<div class="min-h-screen bg-white text-neutral-900">
  <header class="border-b">
    <nav class="max-w-5xl mx-auto flex items-center gap-4 p-3">
      <a href="/" class="font-semibold mr-2 px-10">DKBlytics</a>
      <div class="flex gap-1">
        {#each links as l}
          <a
            href={l.href}
            sveltekit:prefetch
            class="px-3 py-1.5 rounded-md hover:bg-neutral-100 transition"
            class:bg-neutral-200={$page.url.pathname.startsWith(l.href)}
            class:font-semibold={$page.url.pathname.startsWith(l.href)}
          >
            {l.label}
          </a>
        {/each}
      </div>
    </nav>
  </header>

  <main class="max-w-5xl mx-auto p-4">
    {@render children()}
  </main>
</div>
