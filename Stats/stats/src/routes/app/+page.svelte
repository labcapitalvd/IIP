<script>
	import * as Card from '$lib/components/ui/card/index.ts';
</script>

<div class="flex flex-1 flex-col space-y-10">
	<div>
		<h1 class="mb-8 text-6xl font-bold tracking-tight text-gray-900 dark:text-white">
			¡Bienvenido!
		</h1>
		<p class="text-justify leading-tight font-normal text-gray-700 dark:text-gray-400">
			Hola usuario, este es el aplicativo de exploración de respuestas y de resultados del Índice de
			Innovación Pública de la Veeduría Distrital. Aquí podrás explorar los resultados y las
			respuestas de todas las 85 entidades del Distrito de Bogotá que han participado del índice a
			lo largo de las diferentes mediciones. Tenga en cuenta que las preguntas han cambiado entre
			las diferentes mediciones y que por lo tanto no es posible realizar comparaciones directas.
		</p>
	</div>

	<div>
		<div>
			<h2 class="mb-8 text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
				Selecciona un modo
			</h2>
			<p class="text-justify leading-tight font-normal text-gray-700 dark:text-gray-400">
				El aplicativo te permite explorar los datos de varias maneras. Por favor selecciona la
				tarjeta que mejor representa la consulta que quieres realizar. Si tienes una cuenta por
				favor haz click en el ícono en forma de persona de la esquina superior derecha.
			</p>
			<p class="pt-3 pb-8 text-justify leading-tight font-normal text-gray-700 dark:text-gray-400">
				Selecciona entre:
			</p>
		</div>
		<div class="flex flex-col items-center justify-between space-y-6 md:flex-row md:items-stretch md:space-y-0 md:space-x-6">
			<Card.Root>
				<Card.Header>
					<Card.Title>Exploración histórica</Card.Title>
					<Card.Description>Card Description</Card.Description>
				</Card.Header>
				<Card.Content>
					<p>
						Explorar los datos desde un comparativo histórico para una o varias entidades. Aquí
						podra generar gráficos controlando la variable a cruzar.
					</p>
				</Card.Content>
				<Card.Footer>
					<p>Card Footer</p>
				</Card.Footer>
			</Card.Root>

			<Card.Root>
				<Card.Header>
					<Card.Title>Desglose de resultados</Card.Title>
					<Card.Description>Card Description</Card.Description>
				</Card.Header>
				<Card.Content>
					<p>
						Revisar a detalle el desempeño de una entidad para una medición a nivel de componente,
						variable, indicador y pregunta.
					</p>
				</Card.Content>
				<Card.Footer>
					<p>Card Footer</p>
				</Card.Footer>
			</Card.Root>

			<Card.Root>
				<Card.Header>
					<Card.Title>Exploración de respuestas</Card.Title>
					<Card.Description>Card Description</Card.Description>
				</Card.Header>
				<Card.Content>
					<p>
						Revisar las respuestas de una o varias entidades a una pregunta específica. Al
						seleccionar una pregunta el aplicativo le mostrará las respuestas originales.
					</p>
				</Card.Content>
				<Card.Footer>
					<p>Card Footer</p>
				</Card.Footer>
			</Card.Root>
		</div>
	</div>

	<div>
		<div>
			<h2 class="mb-8 text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
				Análisis actor_segmentiales
			</h2>
			<p class="text-justify leading-tight font-normal text-gray-700 dark:text-gray-400">
				Interesado en hacer meta análisis para diferentes variables del índice para actor_segmentes
				completos?
			</p>
			<p class="pt-3 pb-8 text-justify leading-tight font-normal text-gray-700 dark:text-gray-400">
				Selecciona entre:
			</p>
		</div>
		<div class="flex flex-col items-center justify-between space-y-6 md:flex-row md:items-stretch md:space-y-0 md:space-x-6">
			<Card.Root>
				<Card.Header>
					<Card.Title>Exploración histórica</Card.Title>
					<Card.Description>Card Description</Card.Description>
				</Card.Header>
				<Card.Content>
					<p>
						Explorar los datos desde un comparativo histórico para una o varias entidades. Aquí
						podra generar gráficos controlando la variable a cruzar.
					</p>
				</Card.Content>
				<Card.Footer>
					<p>Card Footer</p>
				</Card.Footer>
			</Card.Root>

			<Card.Root>
				<Card.Header>
					<Card.Title>Desglose de resultados</Card.Title>
					<Card.Description>Card Description</Card.Description>
				</Card.Header>
				<Card.Content>
					<p>
						Revisar a detalle el desempeño de una entidad para una medición a nivel de componente,
						variable, indicador y pregunta.
					</p>
				</Card.Content>
				<Card.Footer>
					<p>Card Footer</p>
				</Card.Footer>
			</Card.Root>

			<Card.Root>
				<Card.Header>
					<Card.Title>Exploración de respuestas</Card.Title>
					<Card.Description>Card Description</Card.Description>
				</Card.Header>
				<Card.Content>
					<p>
						Revisar las respuestas de una o varias entidades a una pregunta específica. Al
						seleccionar una pregunta el aplicativo le mostrará las respuestas originales.
					</p>
				</Card.Content>
				<Card.Footer>
					<p>Card Footer</p>
				</Card.Footer>
			</Card.Root>
		</div>
	</div>
</div>
