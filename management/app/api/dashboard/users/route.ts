import { NextResponse } from 'next/server';
import { getAuthenticatedPM } from '@/lib/auth';
import { supabase } from '@/lib/supabase';

export async function GET() {
  const pm = await getAuthenticatedPM();

  if (!pm) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  try {
    // Get project files info for total segments
    const { data: projectFiles } = await supabase
      .from('project_files')
      .select('line_count')
      .eq('project_key', pm.projectKey)
      .single();

    const totalSegments = projectFiles?.line_count || 100;

    // Get translators for this project
    const { data: translators } = await supabase
      .from('users')
      .select('*')
      .eq('project_key', pm.projectKey)
      .eq('role', 'translator');

    const translatorData = [];

    if (translators) {
      for (const translator of translators) {
        const { data: progressData } = await supabase
          .from('user_progress')
          .select('metrics')
          .eq('user_name', translator.name)
          .eq('user_surname', translator.surname)
          .single();

        const metrics = progressData?.metrics || [];
        const metricsArray = Array.isArray(metrics) ? metrics : [];

        if (metricsArray.length > 0) {
          const segmentsCompleted = metricsArray.length;
          const progress = Math.round((segmentsCompleted / totalSegments) * 100);
          const totalEditTime = metricsArray.reduce((sum: number, m: any) => sum + (m.edit_time || 0), 0);
          const insertions = metricsArray.reduce((sum: number, m: any) => sum + (m.insertions || 0), 0);
          const deletions = metricsArray.reduce((sum: number, m: any) => sum + (m.deletions || 0), 0);

          translatorData.push({
            name: translator.name,
            surname: translator.surname,
            segmentsCompleted,
            progress,
            totalEditTime,
            insertions,
            deletions,
            status: segmentsCompleted > 0 ? 'Active' : 'Idle'
          });
        } else {
          translatorData.push({
            name: translator.name,
            surname: translator.surname,
            segmentsCompleted: 0,
            progress: 0,
            totalEditTime: 0,
            insertions: 0,
            deletions: 0,
            status: 'Idle'
          });
        }
      }
    }

    return NextResponse.json({ translators: translatorData });
  } catch (error) {
    console.error('Users error:', error);
    return NextResponse.json(
      { error: 'Failed to load translators' },
      { status: 500 }
    );
  }
}
