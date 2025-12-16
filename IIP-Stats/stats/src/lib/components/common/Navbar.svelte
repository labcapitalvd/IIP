<script lang="ts">
	import * as NavigationMenu from '$lib/components/ui/navigation-menu/index.ts';
	import ProfileDropdown from '$lib/components/common/ProfileDropdown.svelte';

	import { goto } from '$app/navigation';
</script>

<div class="bg-blue-500 flex flex-row items-center justify-between p-2 md:p-3 gap-2 md:gap-3 max-h-12">
  <!-- Logo -->
  <div class="">
    <a href="/app" aria-label="Go to dashboard" onclick={() => goto('/app')}>
      <enhanced:img
        class="object-contain w-auto h-10"
        src="$lib/images/logo.png"
        alt="Go to dashboard"
      />
    </a>
  </div>

  <!-- Navigation -->
  <div class="h-full w-auto">
    <NavigationMenu.Root>
      <NavigationMenu.List>
        <NavigationMenu.Item>
          <NavigationMenu.Trigger>Item 2</NavigationMenu.Trigger>
          <NavigationMenu.Content>
            <ul class="grid w-[200px] gap-4 p-2">
              <li>
                <NavigationMenu.Link href="#">Components</NavigationMenu.Link>
                <NavigationMenu.Link href="#">Documentation</NavigationMenu.Link>
                <NavigationMenu.Link href="#">Blocks</NavigationMenu.Link>
              </li>
            </ul>
          </NavigationMenu.Content>
        </NavigationMenu.Item>

        <NavigationMenu.Item>
          <NavigationMenu.Link href="#">Link 4</NavigationMenu.Link>
        </NavigationMenu.Item>
      </NavigationMenu.List>
    </NavigationMenu.Root>
  </div>

  <!-- Profile Dropdown -->
  <div class="h-full:important w-auto">
    <ProfileDropdown />
  </div>
</div>

