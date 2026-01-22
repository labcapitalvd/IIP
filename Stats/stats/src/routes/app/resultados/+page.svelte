<script lang="ts">
	import type { PageProps } from './$types';
	import { onMount, onDestroy } from 'svelte';
	
	import * as Card from "$lib/components/ui/card/index.ts";

	import { DEFAULT_QUESTION } from '$lib/config/defaults';

	let actor_segment = 'ActorSegment';

	let { data }: PageProps = $props();

	let actors = $state(data.actors);
	let forms = $state(data.forms);

	let actor = $state(data.actor);
	let form = $state(data.form);

	let openSearch = $state(false);

	const actorOptions = actors.map((e) => ({
		name: e.name,
		value: e.id
	}));

	const formOptions = forms.map((i) => ({
		name: i.anno,
		value: i.id
	}));

	let selectedActor: string = $state(actor.id);
	let selectedForm: string = $state(form.id);
	let selectedQuestion: string | null = $state(DEFAULT_QUESTION);

	const handleSubmit = async () => {
		try {
			const [actorRes, formRes] = await Promise.all([
				fetch('/api/answers/actor', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ actorId: selectedActor })
				}),
				fetch('/api/answers/form', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ formId: selectedForm })
				})
			]);

			if (!actorRes.ok || !formRes.ok) {
				console.error('One or both requests failed');
				return;
			}
			Object.assign(actor, await actorRes.json());
			Object.assign(form, await formRes.json());
		} catch (err) {
			console.error('Error during fetch:', err);
		}
	};
	
	function handleKeydown(event: KeyboardEvent) {
			if (event.key === 'F' && event.shiftKey) {
				event.preventDefault();
				openSearch = true;
			}
		}

		onMount(() => {
			window.addEventListener('keydown', handleKeydown);
		});

		onDestroy(() => {
			window.removeEventListener('keydown', handleKeydown);
		});
</script>

<div class="fixed right-5 bottom-5 z-50">
	<Button size="lg" class="rounded-full p-4 shadow-lg" onclick={() => (openSearch = true)}>
		<SearchOutline class="h-5 w-5" />
	</Button>
</div>

<Modal title="Selector" bind:open={openSearch} autoclose class="w-full max-w-4xl">
	<form onsubmit={handleSubmit} class="space-y-4">
		<div>
			<Label for="selector_entidad" class="mb-2">Entidad</Label>
			<Select
				id="selector_entidad"
				placeholder="Selecciona una entidad"
				items={actorOptions}
				bind:value={selectedActor}
			/>
		</div>
		<div>
			<Label for="selector_medicion" class="mb-2">Medición</Label>
			<Select
				id="selector_medicion"
				placeholder="Selecciona un año"
				items={formOptions}
				bind:value={selectedForm}
			/>
		</div>
		<div>
			<Button type="submit" class="w-full self-center">Obtener resultados</Button>
		</div>
	</form>
</Modal>

<div class="flex flex-1 flex-col space-y-6">
	<div class="flex flex-col space-y-8 py-8">
		<div>
			<h1 class="text-6xl font-bold tracking-tight text-gray-900 dark:text-white">
				{actor.name}
			</h1>
			<h3 class="text-2xl font-medium tracking-tight text-gray-400 italic dark:text-white">
				{actor_segment}
			</h3>
			<p class='mt-4'>{actor.description}</p>
		</div>

		<div class="flex flex-col space-y-8 space-x-0 md:flex-row md:space-y-0 md:space-x-8">
			<div class="flex grow flex-col">
				<h3 class="text-xl font-medium tracking-tight text-gray-400 italic dark:text-white">
					Misión
				</h3>
				<p>{actor.mission}</p>
			</div>

			<div class="flex grow flex-col">
				<h3 class="text-xl font-medium tracking-tight text-gray-400 italic dark:text-white">
					Visión
				</h3>
				<p>{actor.vision}</p>
			</div>
		</div>
	</div>

	<hr class="my-6 w-full border-gray-200 p-0 dark:border-gray-700" />

	<!-- {#if error}
	    <hr class="my-6 w-full border-gray-200 p-0 dark:border-gray-700" />
        <Alert color="red">
            <span class="font-medium">¡Error!</span> {error}
        </Alert>
    {:else}
        <div>

        </div>
    {/if}
	<hr class="my-6 w-full border-gray-200 p-0 dark:border-gray-700" />
	<div class="flex flex-col space-y-8 py-8">
		<div>
			<h2 class=" text-4xl font-bold tracking-tight text-gray-900 dark:text-white">
				{actor.name}
			</h2>
			<h3 class="text-2xl font-medium tracking-tight text-gray-400 italic dark:text-white">
				{actor.actor_segment}
			</h3>
		</div>

		<div>
			<h3 class="text-xl font-medium tracking-tight text-gray-400 italic dark:text-white">
				Detalle
			</h3>
			<p>{actor.description}</p>
		</div>
		<div class="flex flex-col space-y-8 space-x-0 md:flex-row md:space-y-0 md:space-x-8">
			<div class="flex grow flex-col">
				<h3 class="text-xl font-medium tracking-tight text-gray-400 italic dark:text-white">
					Misión
				</h3>
				<p>{actor.mission}</p>
			</div>

			<div class="flex grow flex-col">
				<h3 class="text-xl font-medium tracking-tight text-gray-400 italic dark:text-white">
					Visión
				</h3>
				<p>{actor.vision}</p>
			</div>
		</div>
	</div>
	<hr class="my-6 w-full border-gray-200 p-0 dark:border-gray-700" />
	<div class="flex flex-col space-y-8 py-8">
		<div>
			<h3 class="text-4xl font-bold tracking-tight text-gray-900 dark:text-white">
				Resultados por componente.
			</h3>
			<h3 class="text-2xl font-medium tracking-tight text-gray-400 italic dark:text-white">
				Desglose de los resultados de la entidad por componente.
			</h3>
		</div>

		{#if components.length > 0}
			<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
				{#each components as comp (comp.id)}
					<Card class="max-w-4xl justify-between p-4 sm:p-6 md:p-8">
						<div>
							<h5 class="mb-2 text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
								{comp.name}
							</h5>
							<p class="text-justify leading-tight font-normal text-gray-700 dark:text-gray-400">
								{comp.description}
							</p>
							<hr class="my-6 w-full border-gray-200 p-0 dark:border-gray-700" />
						</div>
						<div>
							<h1 class="pb-2 text-gray-600">Progreso:</h1>
							<Progressbar
								progress="75"
								size="h-6"
								labelInside
								labelInsideClass="text-base font-medium text-center p-1 leading-none rounded-full"
								class="my-4"
							/>
						</div>
					</Card>
				{/each}
			</div>
		{:else}
			<p class="mt-8 text-center text-gray-500 italic">
				No se encontraron componentes para este año.
			</p>
		{/if}
	</div>

	<hr class="my-6 w-full border-gray-200 p-0 dark:border-gray-700" />
	<div class="flex flex-col space-y-8 py-8">
		<div>
			<h3 class="text-4xl font-bold tracking-tight text-gray-900 dark:text-white">
				Desglose de resultados
			</h3>
			<h3 class="text-2xl font-medium tracking-tight text-gray-400 italic dark:text-white">
				Desglose de los resultados componente a componente.
			</h3>
		</div>
		{#if components.length > 0}
			<div class="grid grid-cols-1 gap-6">
				{#each components as comp (comp.id)}
					<Card class="max-w-8xl justify-between p-4 sm:p-6 md:p-8">
					<div>
						<h3 class="mb-2 text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
							{comp.name}
						</h3>
						<p class="leading-tight font-normal text-gray-700 dark:text-gray-400">
							{comp.description}
						</p>
						<hr class="my-6 w-full border-gray-200 p-0 dark:border-gray-700" />
					</div>

					<div>
						<Accordion>
						{#each components as comp (comp.id)}
    						<AccordionItem>
    							{#snippet header()}Variable {comp.name}{/snippet}
    							<p class="mb-2 text-gray-500 dark:text-gray-400">
    								Lorem ipsum dolor sit amet, consectetur adipisicing elit. Illo ab necessitatibus sint
    								explicabo ...
    							</p>
    						</AccordionItem>
						{/each}
						</Accordion>
					</div>
					</Card>
				{/each}
			</div>
		{:else}
			<p class="mt-8 text-center text-gray-500 italic">
				No se encontraron componentes para este año.
			</p>
		{/if}
	</div> -->
</div>
