<script lang="ts">
	import type { PageProps } from './$types';

	import { onMount, onDestroy } from 'svelte';

	import { DEFAULT_QUESTION } from '$lib/config/defaults';
	import { SEGMENTS } from '$lib/config/segments';

	let actor_segment = 'ActorSegment';

	let { data }: PageProps = $props();

	let actors = $state(data.actors);
	let forms = $state(data.forms);
	let questions = SEGMENTS;

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
	
	const questionOptions = questions.map((q) => ({
		name: q.name,
		value: q.id
	}));

	let selectedActor: string = $state(actor.id);
	let selectedForm: string = $state(form.id);
	let selectedQuestion: string = $state(DEFAULT_QUESTION.id);

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
			<Label for="selector_pregunta" class="mb-2">Segmento</Label>
			<Select
				id="selector_pregunta"
				placeholder="Selecciona un segmento"
				items={questionOptions}
				bind:value={selectedQuestion}
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

<div class="flex flex-col space-y-6">
	<div class="flex flex-col space-y-8 py-8">
		<div>
			<h1 class="text-6xl font-bold tracking-tight text-gray-900 dark:text-white">
				{actor.name}
			</h1>
			<h3 class="text-2xl font-medium tracking-tight text-gray-400 italic dark:text-white">
				{actor_segment}
			</h3>
			<p class="mt-4">{actor.description}</p>
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
		<div class="space-y-2">
			<h2 class=" text-4xl font-bold tracking-tight text-gray-900 dark:text-white">Pregunta 1</h2>
			<p>Texto plano de la pregunta</p>
		</div>

		{#if actors.length > 0}
			<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
				{#each actors as ent (ent.id)}
					<Card class="max-w-4xl justify-between p-4 sm:p-6 md:p-8">
						<div>
							<h5 class="mb-2 text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
								{ent.name}
							</h5>
							<p class="text-justify leading-tight font-normal text-gray-700 dark:text-gray-400">
								{ent.id}
							</p>
							<hr class="my-6 w-full border-gray-200 p-0 dark:border-gray-700" />
						</div>
						<div>
							<h1 class="pb-2 text-gray-600">Progreso:</h1>
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
</div>
