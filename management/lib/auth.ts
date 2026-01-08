import { cookies } from 'next/headers';

export interface AuthenticatedUser {
  name: string;
  surname: string;
  role: string;
  projectKey: string;
  dbType: string;
  dbConnection: any;
}

export async function getAuthenticatedPM(): Promise<AuthenticatedUser | null> {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get('pm_session');

  if (!sessionCookie) {
    return null;
  }

  try {
    // Parse the session cookie
    const session = JSON.parse(sessionCookie.value);

    // Verify the session is valid and user is a project manager
    if (session.role !== 'project_manager') {
      return null;
    }

    return {
      name: session.name,
      surname: session.surname,
      role: session.role,
      projectKey: session.projectKey,
      dbType: session.dbType,
      dbConnection: session.dbConnection
    };
  } catch (error) {
    return null;
  }
}
