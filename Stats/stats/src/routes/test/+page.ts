import type { PageLoad } from './$types';
import { Fetcher } from '$lib/api/Fetcher';

export const load: PageLoad = async (event) => {
  try {
    const body = new URLSearchParams({
      grant_type: 'password',
      username: 'root',
      password: 'averysafepassword'
    });

    // Assign response to variable
    const response = await Fetcher<{ access_token: string }>({
      url: '/auth/login',
      method: 'POST',
      data: body,
      svelteEvent: event
    });

    return {
      success: true,
      access_token: response.access_token
    };
  } catch (err) {
    console.error('Login failed', err);
    return {
      success: false,
      error: err instanceof Error ? err.message : String(err)
    };
  }
};
