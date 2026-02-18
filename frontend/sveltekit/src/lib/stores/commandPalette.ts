import { writable } from 'svelte/store';

export const paletteOpen = writable(false);

export function openPalette() {
  paletteOpen.set(true);
}

export function closePalette() {
  paletteOpen.set(false);
}
