<script>
	import { Badge } from '$lib/components/ui/badge/index.ts';
	import { Button } from '$lib/components/ui/button/index.ts';
	import * as Card from '$lib/components/ui/card/index.ts';
</script>

<svelte:head>
	<title>Visualizador IIP - Índice de Innovación Pública</title>
	<meta
		name="description"
		content="Explora los resultados del Índice de Innovación Pública de la Veeduría Distrital de Bogotá"
	/>
</svelte:head>

<div class="flex min-h-screen flex-col">
	<!-- Hero Section -->
	<section
		class="bg-gradient-to-br from-blue-50 to-indigo-100 px-4 py-20 dark:from-gray-900 dark:to-gray-800"
	>
		<div class="mx-auto max-w-6xl text-center">
			<Badge color="blue" class="mb-6">Veeduría Distrital de Bogotá</Badge>
			<h1
				class="mb-6 text-5xl font-extrabold tracking-tight text-gray-900 md:text-7xl dark:text-white"
			>
				Visualizador
				<span class="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
					IIP
				</span>
			</h1>
			<p
				class="mx-auto mb-8 max-w-3xl text-xl leading-relaxed text-gray-600 md:text-2xl dark:text-gray-300"
			>
				Explora los resultados y respuestas del <strong>Índice de Innovación Pública</strong> de las
				85 entidades del Distrito de Bogotá
			</p>
			<div class="flex flex-col items-center justify-center gap-4 sm:flex-row">
				<Button href="/app" class="px-8 py-4">Comenzar exploración</Button>
				<Button href="#features" color="alternative" class="px-8 py-4">Conocer más</Button>
			</div>
		</div>
	</section>

	<!-- Stats Section -->
	<section class="bg-white px-4 py-16 dark:bg-gray-900">
		<div class="mx-auto max-w-6xl">
			<div class="grid grid-cols-1 gap-8 text-center md:grid-cols-3">
				<div class="p-6">
					<div class="mb-2 text-4xl font-bold text-blue-600 dark:text-blue-400">85</div>
					<div class="text-lg text-gray-600 dark:text-gray-400">Entidades del Distrito</div>
				</div>
				<div class="p-6">
					<div class="mb-2 text-4xl font-bold text-indigo-600 dark:text-indigo-400">Múltiples</div>
					<div class="text-lg text-gray-600 dark:text-gray-400">Mediciones Históricas</div>
				</div>
				<div class="p-6">
					<div class="mb-2 text-4xl font-bold text-purple-600 dark:text-purple-400">3</div>
					<div class="text-lg text-gray-600 dark:text-gray-400">Modos de Exploración</div>
				</div>
			</div>
		</div>
	</section>

	<!-- Features Section -->
	<section id="features" class="bg-gray-50 px-4 py-20 dark:bg-gray-800">
		<div class="mx-auto max-w-6xl">
			<div class="mb-16 text-center">
				<h2 class="mb-4 text-4xl font-bold text-gray-900 dark:text-white">
					Herramientas de Análisis
				</h2>
				<p class="mx-auto max-w-3xl text-xl text-gray-600 dark:text-gray-300">
					Explora los datos de innovación pública con herramientas especializadas para diferentes
					tipos de análisis
				</p>
			</div>

			<div class="grid grid-cols-1 gap-8 md:grid-cols-3">
				<Card.Root>
					<Card.Header>
						<Card.Title>Exploración Histórica</Card.Title>
						<Card.Description>Card Description</Card.Description>
					</Card.Header>
					<Card.Content>
						<p>
							Compara el desempeño de entidades a lo largo del tiempo con gráficos interactivos y
							análisis de tendencias.
						</p>
					</Card.Content>
					<Card.Footer>
						<p>Card Footer</p>
					</Card.Footer>
				</Card.Root>

				<Card.Root>
					<Card.Header>
						<Card.Title>Desglose de Resultados</Card.Title>
						<Card.Description>Card Description</Card.Description>
					</Card.Header>
					<Card.Content>
						<p>
							Analiza el desempeño detallado por componentes, variables, indicadores y preguntas
							específicas.
						</p>
					</Card.Content>
					<Card.Footer>
						<p>Card Footer</p>
					</Card.Footer>
				</Card.Root>

				<Card.Root>
					<Card.Header>
						<Card.Title>Exploración de Respuestas</Card.Title>
						<Card.Description>Card Description</Card.Description>
					</Card.Header>
					<Card.Content>
						<p>
							Revisa las respuestas originales de las entidades a preguntas específicas del índice.
						</p>
					</Card.Content>
					<Card.Footer>
						<p>Card Footer</p>
					</Card.Footer>
				</Card.Root>
			</div>
		</div>
	</section>

	<!-- About Section -->
	<section class="bg-white px-4 py-20 dark:bg-gray-900">
		<div class="mx-auto max-w-4xl">
			<div class="mb-12 text-center">
				<h2 class="mb-6 text-4xl font-bold text-gray-900 dark:text-white">
					Sobre el Índice de Innovación Pública
				</h2>
				<p class="text-lg leading-relaxed text-gray-600 dark:text-gray-300">
					El Índice de Innovación Pública (IIP) es una herramienta desarrollada por la Veeduría
					Distrital para medir y evaluar la capacidad de innovación de las entidades del Distrito de
					Bogotá. A través de diferentes mediciones, se analizan componentes clave que contribuyen
					al desarrollo de una cultura de innovación en el actor_segment público.
				</p>
			</div>

			<div
				class="rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50 p-8 dark:from-gray-800 dark:to-gray-700"
			>
				<h3 class="mb-4 text-2xl font-semibold text-gray-900 dark:text-white">
					Importante tener en cuenta:
				</h3>
				<ul class="space-y-3 text-gray-600 dark:text-gray-300">
					<li class="flex items-start">
						<span class="mt-1 mr-3 text-blue-500">•</span>
						Las preguntas han evolucionado entre diferentes mediciones
					</li>
					<li class="flex items-start">
						<span class="mt-1 mr-3 text-blue-500">•</span>
						No todas las comparaciones directas son posibles entre mediciones
					</li>
					<li class="flex items-start">
						<span class="mt-1 mr-3 text-blue-500">•</span>
						Los datos reflejan la evolución continua del marco metodológico
					</li>
				</ul>
			</div>
		</div>
	</section>

	<!-- CTA Section -->
	<section class="bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-16 text-white">
		<div class="mx-auto max-w-4xl text-center">
			<h2 class="mb-4 text-3xl font-bold md:text-4xl">¿Listo para explorar los datos?</h2>
			<p class="mb-8 text-xl opacity-90">
				Accede a las herramientas de análisis y descubre insights sobre la innovación pública en
				Bogotá
			</p>
			<Button href="/app" color="dark" class="px-8 py-4">Ir al aplicativo</Button>
		</div>
	</section>
</div>
