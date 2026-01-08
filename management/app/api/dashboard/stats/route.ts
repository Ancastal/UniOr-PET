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
    // Get project info
    const { data: project } = await supabase
      .from('projects')
      .select('*')
      .eq('project_key', pm.projectKey)
      .single();

    // Get project files info
    const { data: projectFiles } = await supabase
      .from('project_files')
      .select('*')
      .eq('project_key', pm.projectKey)
      .single();

    const totalSegments = projectFiles?.line_count || 0;

    // Get translators for this project
    const { data: translators } = await supabase
      .from('users')
      .select('*')
      .eq('project_key', pm.projectKey)
      .eq('role', 'translator');

    // Get all metrics for this project
    const activity = [];
    let completedSegments = 0;

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
          const totalEditTime = metricsArray.reduce((sum: number, m: any) => sum + (m.edit_time || 0), 0);
          const insertions = metricsArray.reduce((sum: number, m: any) => sum + (m.insertions || 0), 0);
          const deletions = metricsArray.reduce((sum: number, m: any) => sum + (m.deletions || 0), 0);

          activity.push({
            name: translator.name,
            surname: translator.surname,
            segmentsCompleted,
            totalEditTime,
            insertions,
            deletions,
            status: segmentsCompleted > 0 ? 'Active' : 'Idle'
          });

          completedSegments += segmentsCompleted;
        } else {
          activity.push({
            name: translator.name,
            surname: translator.surname,
            segmentsCompleted: 0,
            totalEditTime: 0,
            insertions: 0,
            deletions: 0,
            status: 'Idle'
          });
        }
      }
    }

    const stats = {
      stats: {
        totalTranslators: translators?.length || 0,
        totalSegments,
        completedSegments,
        projectCreated: project?.created_at ? new Date(project.created_at).toLocaleDateString() : 'N/A',
        sourceFile: projectFiles?.source_filename || 'N/A',
        translationFile: projectFiles?.translation_filename || 'N/A',
        dbType: 'Supabase'
      },
      activity
    };

    return NextResponse.json(stats);
  } catch (error) {
    console.error('Dashboard stats error:', error);
    return NextResponse.json(
      { error: 'Failed to load dashboard data' },
      { status: 500 }
    );
  }
}
