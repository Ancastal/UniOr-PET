import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'UniOr-PET Management',
  description: 'Project Manager Dashboard for UniOr-PET Translation System',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
