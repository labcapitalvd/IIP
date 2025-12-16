<script lang="ts">
	import * as Avatar from '$lib/components/ui/avatar/index.ts';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.ts';
	import { goto } from '$app/navigation';
</script>

<div>
	<DropdownMenu.Root>
		<DropdownMenu.Trigger>
			<Avatar.Root class="cursor-pointer">
				<Avatar.Image src="https://github.com/shadcn.png" alt="@shadcn" />
				<Avatar.Fallback>CN</Avatar.Fallback>
			</Avatar.Root>
		</DropdownMenu.Trigger>
		<DropdownMenu.Content class="w-56" align="end">
			<DropdownMenu.Label>My Account</DropdownMenu.Label>
			<DropdownMenu.Group>
				<DropdownMenu.Item
					onclick={() => {
						goto('/profile');
					}}
				>
					Profile
					<DropdownMenu.Shortcut>⇧⌘P</DropdownMenu.Shortcut>
				</DropdownMenu.Item>
				<DropdownMenu.Item
					onclick={() => {
						goto('/billing');
					}}
				>
					Billing
					<DropdownMenu.Shortcut>⌘B</DropdownMenu.Shortcut>
				</DropdownMenu.Item>
				<DropdownMenu.Item
					onclick={() => {
						goto('/');
					}}
				>
					Settings
					<DropdownMenu.Shortcut>⌘S</DropdownMenu.Shortcut>
				</DropdownMenu.Item>
			</DropdownMenu.Group>

			<DropdownMenu.Separator />
			<DropdownMenu.Item
				onclick={() => {
					goto('/');
				}}
			>
				Log out
				<DropdownMenu.Shortcut>⇧⌘Q</DropdownMenu.Shortcut>
			</DropdownMenu.Item>
		</DropdownMenu.Content>
	</DropdownMenu.Root>
</div>
