<script>
	import Drawer from '$lib/components/common/Drawer.svelte';
</script>

<div class="flex flex-1 flex-col space-y-10">
	<div class="">
		<h1 class="mb-8 text-6xl font-bold tracking-tight text-gray-900 dark:text-white">Histórico</h1>
		<p class="text-justify leading-tight font-normal text-gray-700 dark:text-gray-400">
			Hola usuario, este es el aplicativo de exploración de respuestas y de resultados del Índice de
			Innovación Pública de la Veeduría Distrital. Aquí podrás explorar los resultados y las
			respuestas de todas las 85 entidades del Distrito de Bogotá que han participado del índice a
			lo largo de las diferentes mediciones. Tenga en cuenta que las preguntas han cambiado entre
			las diferentes mediciones y que por lo tanto no es posible realizar comparaciones directas.
		</p>
		<hr class="m-6 border-gray-200 sm:mx-auto lg:mb-8 dark:border-gray-700" />
	</div>
	<Drawer />
</div>
