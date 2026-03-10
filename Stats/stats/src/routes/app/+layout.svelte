<script lang="ts">
	import Navbar from '$lib/components/common/Navbar.svelte';
	
	
	import Footer from '$lib/components/common/Footer.svelte';

	let { children } = $props();
</script>

<div id="layout root" class="flex min-h-screen flex-col">
	<Navbar />
	<main class="max-w-7xl flex flex-col flex-1 w-full mx-auto p-4 bg-red-500">
		{@render children()}
	</main>
	<Footer />
</div>
