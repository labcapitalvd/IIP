<script lang="ts">
  export let data: {
    success: boolean;
    access_token?: string;
    error?: string;
  };
</script>

<h1>Test Login</h1>

{#if data.success}
  <p>Login succeeded! Token: {data.access_token}</p>
{:else}
  <p style="color: red;">Login failed: {data.error}</p>
{/if}
