'use client';

import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { ALLERGENS, DIETS, GOALS, setProfile, useProfile } from '@/lib/profile';
import type { Profile } from '@/lib/api/types';

type Group = 'diets' | 'allergens' | 'goals';

function toggle(profile: Profile, group: Group, id: string, on: boolean): Profile {
  const current = (profile[group] as string[] | undefined) ?? [];
  const next = on ? [...current, id] : current.filter((value) => value !== id);
  return { ...profile, [group]: next } as Profile;
}

function Section({
  title,
  group,
  options,
}: {
  title: string;
  group: Group;
  options: readonly { id: string; label: string }[];
}) {
  const profile = useProfile();
  return (
    <fieldset className="space-y-3">
      <legend className="text-lg font-semibold">{title}</legend>
      <div className="grid gap-3 sm:grid-cols-2">
        {options.map((option) => {
          const inputId = `${group}-${option.id}`;
          const checked = ((profile[group] as string[] | undefined) ?? []).includes(option.id);
          return (
            <div key={option.id} className="flex items-center gap-3 rounded-md border p-3">
              <Checkbox
                id={inputId}
                checked={checked}
                onCheckedChange={(value) => setProfile(toggle(profile, group, option.id, value === true))}
              />
              <Label htmlFor={inputId} className="flex-1 cursor-pointer">
                {option.label}
              </Label>
            </div>
          );
        })}
      </div>
    </fieldset>
  );
}

export function ProfileForm() {
  return (
    <div className="space-y-8">
      <p className="rounded-md border bg-muted/40 p-3 text-sm">
        Your choices are saved <strong>only in this browser</strong>. They are sent with each check so the answer fits
        you, and are not stored in an account.
      </p>
      <Section title="Allergens to avoid" group="allergens" options={ALLERGENS} />
      <Section title="Diets" group="diets" options={DIETS} />
      <Section title="Nutrition goals" group="goals" options={GOALS} />
      <Button variant="outline" onClick={() => setProfile({ diets: [], allergens: [], goals: [] })}>
        Clear everything
      </Button>
    </div>
  );
}
