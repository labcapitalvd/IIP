<script>
  import { Button } from "$lib/components/ui/button/index.ts";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.ts";
</script>

<Button id="dd-btn">Dropdown button</Button>
 
<DropdownMenu.Root>
 <DropdownMenu.Trigger>Open</DropdownMenu.Trigger>
 <DropdownMenu.Content>
  <DropdownMenu.Group>
   <DropdownMenu.Label>My Account</DropdownMenu.Label>
   <DropdownMenu.Separator />
   <DropdownMenu.Item>Profile</DropdownMenu.Item>
   <DropdownMenu.Item>Billing</DropdownMenu.Item>
   <DropdownMenu.Item>Team</DropdownMenu.Item>
   <DropdownMenu.Item>Subscription</DropdownMenu.Item>
  </DropdownMenu.Group>
 </DropdownMenu.Content>
</DropdownMenu.Root>

<h1>Page 3</h1>
<p>Página 3</p>
