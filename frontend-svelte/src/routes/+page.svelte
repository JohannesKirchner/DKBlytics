<script lang="ts">
  import { API_BASE } from "$lib/config";

  const cards = [
    { href: "/balance", title: "Balance Overview", blurb: "Accounts, totals, quick filters" },
    { href: "/categories", title: "Category Rules", blurb: "Assign categories and create rules" },
    { href: "/budget", title: "Budget Breakdown", blurb: "Monthly/Yearly spend by category" }
  ];
</script>

<section class="py-6">
  <h1 class="text-3xl font-bold">DKBlytics</h1>
  <p class="text-neutral-600 mt-1">Personal banking frontend (SvelteKit)</p>

  <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-6">
    {#each cards as c}
      <a
        href={c.href}
        sveltekit:prefetch
        class="block rounded-lg border p-4 hover:bg-neutral-50 transition"
      >
        <h2 class="font-semibold">{c.title}</h2>
        <p class="text-sm text-neutral-600 mt-1">{c.blurb}</p>
      </a>
    {/each}
  </div>
</section>
