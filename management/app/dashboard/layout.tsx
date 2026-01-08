import { redirect } from 'next/navigation';
import { getAuthenticatedPM } from '@/lib/auth';
import DashboardLayoutClient from './DashboardLayoutClient';

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pm = await getAuthenticatedPM();

  if (!pm) {
    redirect('/');
  }

  return <DashboardLayoutClient pm={pm}>{children}</DashboardLayoutClient>;
}
