import { useSyncExternalStore } from 'react';
import type { Profile } from '@/lib/api/types';

export const DIETS = [
  { id: 'vegan', label: 'Vegan' },
  { id: 'vegetarian', label: 'Vegetarian' },
  { id: 'gluten_free', label: 'Gluten-free' },
  { id: 'lactose_free', label: 'Lactose-free' },
  { id: 'palm_oil_free', label: 'Palm-oil-free' },
  { id: 'nut_free', label: 'Nut-free' },
] as const;

export const ALLERGENS = [
  { id: 'milk', label: 'Milk' },
  { id: 'eggs', label: 'Eggs' },
  { id: 'peanuts', label: 'Peanuts' },
  { id: 'nuts', label: 'Tree nuts' },
  { id: 'soy', label: 'Soy' },
  { id: 'gluten', label: 'Gluten (wheat, rye, barley)' },
  { id: 'fish', label: 'Fish' },
  { id: 'crustaceans', label: 'Crustaceans' },
  { id: 'molluscs', label: 'Molluscs' },
  { id: 'sesame', label: 'Sesame' },
  { id: 'celery', label: 'Celery' },
  { id: 'mustard', label: 'Mustard' },
  { id: 'lupin', label: 'Lupin' },
  { id: 'sulphites', label: 'Sulphites' },
] as const;

export const GOALS = [
  { id: 'low_sugar', label: 'Low sugar' },
  { id: 'low_salt', label: 'Low salt' },
  { id: 'low_sat_fat', label: 'Low saturated fat' },
] as const;

// Compile-time drift guard: if the API's allowed values change, these lines stop compiling.
const _diets: Profile['diets'] = [] as (typeof DIETS)[number]['id'][];
const _allergens: Profile['allergens'] = [] as (typeof ALLERGENS)[number]['id'][];
const _goals: Profile['goals'] = [] as (typeof GOALS)[number]['id'][];
void [_diets, _allergens, _goals];

const KEY = 'labellens.profile.v1';
const EMPTY: Profile = { diets: [], allergens: [], goals: [] };

function onlyKnown<T extends string>(value: unknown, allowed: readonly T[]): T[] {
  if (!Array.isArray(value)) return [];
  return allowed.filter((id) => value.includes(id)); // also keeps a stable order
}

function normalise(raw: unknown): Profile {
  const obj = (raw ?? {}) as Record<string, unknown>;
  return {
    diets: onlyKnown(obj.diets, DIETS.map((d) => d.id)),
    allergens: onlyKnown(obj.allergens, ALLERGENS.map((a) => a.id)),
    goals: onlyKnown(obj.goals, GOALS.map((g) => g.id)),
  };
}

/** A stable string for a profile: used as a cache key and as an effect dependency. */
export function profileKey(profile: Profile): string {
  return JSON.stringify(normalise(profile));
}

// ---- the store -----------------------------------------------------------------
let cache: Profile | null = null;
const listeners = new Set<() => void>();

function read(): Profile {
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? normalise(JSON.parse(raw)) : EMPTY;
  } catch {
    return EMPTY; // private mode, blocked storage or corrupt JSON
  }
}

function getSnapshot(): Profile {
  if (cache === null) cache = read();
  return cache; // must be the SAME object until the data really changes
}

function emit(): void {
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  const onStorage = (event: StorageEvent): void => {
    if (event.key === KEY) {
      cache = null; // another tab changed it
      emit();
    }
  };
  window.addEventListener('storage', onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener('storage', onStorage);
  };
}

export function setProfile(next: Profile): void {
  cache = normalise(next);
  try {
    window.localStorage.setItem(KEY, JSON.stringify(cache));
  } catch {
    // Storage is blocked: the profile still works for this page view.
  }
  emit();
}

export function useProfile(): Profile {
  return useSyncExternalStore(subscribe, getSnapshot, () => EMPTY);
}
