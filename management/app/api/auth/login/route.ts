import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { supabase } from '@/lib/supabase';
import CryptoJS from 'crypto-js';

export async function POST(request: Request) {
  try {
    const { name, surname, password } = await request.json();

    console.log('Login attempt:', { name, surname });

    if (!name || !surname || !password) {
      return NextResponse.json(
        { error: 'All fields are required' },
        { status: 400 }
      );
    }

    // Hash the password using MD5 (same as the Python backend)
    const hashedPassword = CryptoJS.SHA256(password).toString();
    console.log('Hashed password:', hashedPassword.substring(0, 10) + '...');

    // Query Supabase for the user
    const { data: users, error } = await supabase
      .from('users')
      .select('*')
      .eq('name', name)
      .eq('surname', surname)
      .eq('password', hashedPassword);

    console.log('Supabase response:', { userCount: users?.length, error });

    if (error) {
      console.error('Supabase error:', error);
      return NextResponse.json(
        { error: `Database error: ${error.message}` },
        { status: 500 }
      );
    }

    if (!users || users.length === 0) {
      return NextResponse.json(
        { error: 'Invalid credentials' },
        { status: 401 }
      );
    }

    const user = users[0];

    if (user.role !== 'project_manager') {
      return NextResponse.json(
        { error: 'Access denied. Project managers only.' },
        { status: 403 }
      );
    }

    // Create session
    // Generate project_key from surname_name if not set in database
    const projectKey = user.project_key || `${user.surname}_${user.name}`;

    const session = {
      name: user.name,
      surname: user.surname,
      role: user.role,
      projectKey,
      dbType: user.db_type || 'supabase',
      dbConnection: null
    };

    console.log('Login successful for:', session.name, session.surname, 'Project:', projectKey);

    const cookieStore = await cookies();
    cookieStore.set('pm_session', JSON.stringify(session), {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 7 // 7 days
    });

    return NextResponse.json({ success: true, role: user.role });
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { error: 'Authentication failed' },
      { status: 500 }
    );
  }
}
