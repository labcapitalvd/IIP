<script lang="ts">
	import * as NavigationMenu from '$lib/components/ui/navigation-menu/index.ts';
	import ProfileDropdown from '$lib/components/common/ProfileDropdown.svelte';
</script>

<div class="flex flex-col">
	<div class="flex h-full bg-yellow-500">
		<enhanced:img class="h-full w-auto object-contain" src="$lib/images/logo.png" alt="Logo IIP" />
	</div>

	<div class="flex h-10 justify-between bg-green-500 p-2 md:h-17 md:p-3">
		<div class="display-block flex flex-row items-center gap-2 md:gap-3">
			<div class="h-full">
				<enhanced:img src="$lib/images/logo.png" alt="Logo IIP" class="h-full w-auto" />
			</div>
			<span class="text-white">Footer Content</span>
		</div>

		<div class="flex flex-col items-center">
			<h4>Todos los derechos reservados</h4>
			<p>2023</p>
		</div>
		<div class="flex flex-col items-center">
			<h4>Todos los derechos reservados</h4>
			<p>2023</p>
		</div>
	</div>
</div>
