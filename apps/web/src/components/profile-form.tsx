'use client';

import Link from 'next/link';
import { ShieldCheck, RotateCcw, AlertOctagon, UtensilsCrossed, HeartPulse, ArrowRight } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Button, buttonVariants } from '@/components/ui/button';
import { ALLERGENS, DIETS, GOALS, setProfile, useProfile } from '@/lib/profile';
import { cn } from '@/lib/utils';
import type { Profile } from '@/lib/api/types';

type Group = 'diets' | 'allergens' | 'goals';

function toggle(profile: Profile, group: Group, id: string, on: boolean): Profile {
  const current = (profile[group] as string[] | undefined) ?? [];
  const next = on ? [...current, id] : current.filter((value) => value !== id);
  return { ...profile, [group]: next } as Profile;
}

function Section({
  title,
  subtitle,
  group,
  options,
  accent,
}: {
  title: string;
  subtitle: string;
  group: Group;
  options: readonly { id: string; label: string }[];
  accent: 'red' | 'emerald' | 'blue';
}) {
  const profile = useProfile();
  const selectedCount = ((profile[group] as string[] | undefined) ?? []).length;

  return (
    <fieldset className="rounded-2xl border border-border/80 bg-card p-5 shadow-xs transition-all sm:p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
        <div>
          <div className="flex items-center gap-2">
            {group === 'allergens' ? (
              <AlertOctagon aria-hidden className="size-4.5 text-red-600" />
            ) : group === 'diets' ? (
              <UtensilsCrossed aria-hidden className="size-4.5 text-emerald-600" />
            ) : (
              <HeartPulse aria-hidden className="size-4.5 text-blue-600" />
            )}
            <legend className="text-lg font-bold tracking-tight text-foreground">{title}</legend>
          </div>
          <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>
        </div>
        {selectedCount > 0 ? (
          <span className="inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs font-semibold text-foreground">
            {selectedCount} selected
          </span>
        ) : null}
      </div>

      <div className="grid gap-2.5 sm:grid-cols-2">
        {options.map((option) => {
          const inputId = `${group}-${option.id}`;
          const checked = ((profile[group] as string[] | undefined) ?? []).includes(option.id);

          const activeStyle =
            accent === 'red'
              ? 'border-red-300/80 bg-red-50/60 text-red-950 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-200'
              : accent === 'emerald'
                ? 'border-emerald-300/80 bg-emerald-50/60 text-emerald-950 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-200'
                : 'border-blue-300/80 bg-blue-50/60 text-blue-950 dark:border-blue-900/60 dark:bg-blue-950/30 dark:text-blue-200';

          return (
            <div
              key={option.id}
              className={`flex items-center gap-3 rounded-xl border p-3 transition-all ${
                checked
                  ? activeStyle
                  : 'border-border/70 bg-card hover:border-border hover:bg-secondary/40'
              }`}
            >
              <Checkbox
                id={inputId}
                checked={checked}
                onCheckedChange={(value) => setProfile(toggle(profile, group, option.id, value === true))}
                className="size-4.5 rounded-sm"
              />
              <Label htmlFor={inputId} className="flex-1 cursor-pointer text-sm font-medium leading-none">
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
  const profile = useProfile();
  const totalCount =
    (profile.diets?.length ?? 0) + (profile.allergens?.length ?? 0) + (profile.goals?.length ?? 0);

  return (
    <div className="space-y-6">
      {/* Privacy Notice Banner */}
      <div className="flex items-start gap-3.5 rounded-xl border border-primary/20 bg-primary/5 p-4 text-sm text-foreground">
        <ShieldCheck aria-hidden className="mt-0.5 size-5 shrink-0 text-primary" />
        <div className="space-y-1">
          <p className="font-semibold text-foreground">
            Your choices are saved <strong>only in this browser</strong>.
          </p>
          <p className="text-xs text-muted-foreground">
            They are sent with each check so the analysis fits your health needs, and are not stored in any external account or database.
          </p>
        </div>
      </div>

      <Section
        title="Allergens to avoid"
        subtitle="Critical alerts if any ingredient or factory trace is detected"
        group="allergens"
        options={ALLERGENS}
        accent="red"
      />

      <Section
        title="Diets"
        subtitle="Filter formulations by lifestyle, faith, or dietary principles"
        group="diets"
        options={DIETS}
        accent="emerald"
      />

      <Section
        title="Nutrition goals"
        subtitle="Highlights products adhering to UK traffic-light guidance"
        group="goals"
        options={GOALS}
        accent="blue"
      />

      <div className="flex flex-col-reverse items-center justify-between gap-4 pt-2 sm:flex-row">
        <Button
          variant="outline"
          onClick={() => setProfile({ diets: [], allergens: [], goals: [] })}
          disabled={totalCount === 0}
          className="w-full text-xs text-muted-foreground hover:text-foreground sm:w-auto"
        >
          <RotateCcw aria-hidden className="size-3.5" />
          Clear everything
        </Button>

        <Link
          href="/"
          className={cn(
            buttonVariants({ variant: 'default' }),
            'w-full font-semibold shadow-xs sm:w-auto h-9 px-4',
          )}
        >
          Start scanning with this profile
          <ArrowRight aria-hidden className="size-4" />
        </Link>
      </div>
    </div>
  );
}
