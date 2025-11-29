<script>
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<nav class="sticky top-0 bg-white z-50 h-12 p-2 border-b-2" style="--header-h: 56px;">
	<a href="/balance" class="p-2">Balance</a>
	<a href="/transactions" class="p-2">Transactions</a>
	<a href="/categorization" class="p-2">Categories</a>
	<a href="/budget" class="p-2">Budget</a>
</nav>

{@render children?.()}
