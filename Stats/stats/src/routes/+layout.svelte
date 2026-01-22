<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	
	import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
	const queryClient = new QueryClient();

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div id="layout-root" class="flex min-h-screen flex-col">
	<QueryClientProvider client={queryClient}>
		{@render children?.()}
	</QueryClientProvider>
</div>
