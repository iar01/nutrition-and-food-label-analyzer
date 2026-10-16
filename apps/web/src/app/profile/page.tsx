import { ProfileForm } from '@/components/profile-form';

export const metadata = { title: 'My profile | LabelLens' };

export default function ProfilePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">My profile</h1>
      <ProfileForm />
    </div>
  );
}
