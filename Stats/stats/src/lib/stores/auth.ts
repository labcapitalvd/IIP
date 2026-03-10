// src/lib/stores/auth.ts
import { writable } from 'svelte/store';
import { browser } from '$app/environment';

// Create a custom store that persists to localStorage
function createPersistedStore<T>(key: string, initialValue: T) {
	// Get initial value from localStorage if in browser
	const storedValue = browser ? localStorage.getItem(key) : null;
	const initial = storedValue ? JSON.parse(storedValue) : initialValue;

	const { subscribe, set, update } = writable<T>(initial);

	return {
		subscribe,
		set: (value: T) => {
			if (browser) {
				localStorage.setItem(key, JSON.stringify(value));
			}
			set(value);
		},
		update: (updater: (value: T) => T) => {
			update((current) => {
				const newValue = updater(current);
				if (browser) {
					localStorage.setItem(key, JSON.stringify(newValue));
				}
				return newValue;
			});
		},
		clear: () => {
			if (browser) {
				localStorage.removeItem(key);
			}
			set(initialValue);
		}
	};
}

export const accessToken = createPersistedStore<string | null>('accessToken', null);
export const isLoggedIn = writable(false);

// Auto-update isLoggedIn based on accessToken
accessToken.subscribe((token) => {
	isLoggedIn.set(!!token);
});
