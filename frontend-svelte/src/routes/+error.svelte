<script>
  export let error;
  export let status;
</script>

<section class="py-16 text-center">
  <h1 class="text-4xl font-bold">{status}</h1>
  <p class="mt-2 text-neutral-600">
    {error?.message || 'Something went wrong.'}
  </p>

  <div class="mt-6">
    <a href="/" class="inline-block px-4 py-2 rounded-md border hover:bg-neutral-50">
      Go home
    </a>
  </div>
</section>