import { ProfileForm } from '@/components/profile-form';

export const metadata = {
  title: 'My Profile & Dietary Preferences | LabelLens',
  description: 'Configure allergens, dietary commitments, and nutrition goals stored privately in your browser.',
};

export default function ProfilePage() {
  return (
    <div className="space-y-6">
      <div className="space-y-1.5">
        <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
          My profile
        </h1>
        <p className="text-sm text-muted-foreground">
          Tailor ingredient checks to your body, allergies, and lifestyle.
        </p>
      </div>
      <ProfileForm />
    </div>
  );
}
