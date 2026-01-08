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

    const totalSegments = projectFiles?.line_count || 0;

    // Get translators for this project
    const { data: translators } = await supabase
      .from('users')
      .select('*')
      .eq('project_key', pm.projectKey)
      .eq('role', 'translator');

    const translatorMetrics = [];
    let completedSegments = 0;
    let totalEditTime = 0;
    const allEditTimes: number[] = [];

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
          completedSegments += metricsArray.length;

          const avgEditTime = metricsArray.reduce((sum: number, m: any) => sum + (m.edit_time || 0), 0) / metricsArray.length;
          const avgInsertions = metricsArray.reduce((sum: number, m: any) => sum + (m.insertions || 0), 0) / metricsArray.length;
          const avgDeletions = metricsArray.reduce((sum: number, m: any) => sum + (m.deletions || 0), 0) / metricsArray.length;

          // Calculate efficiency based on edit time and changes
          const efficiency = Math.min(100, Math.max(0, 100 - (avgEditTime / 100)));

          totalEditTime += metricsArray.reduce((sum: number, m: any) => sum + (m.edit_time || 0), 0);

          metricsArray.forEach((m: any) => {
            if (m.edit_time) allEditTimes.push(m.edit_time);
          });

          translatorMetrics.push({
            name: translator.name,
            surname: translator.surname,
            avgEditTime,
            avgInsertions,
            avgDeletions,
            efficiency
          });
        }
      }
    }

    // Calculate segment distribution
    const distribution = [
      { range: '0-30s', count: 0 },
      { range: '30-60s', count: 0 },
      { range: '60-90s', count: 0 },
      { range: '90s+', count: 0 }
    ];

    allEditTimes.forEach(time => {
      if (time < 30) distribution[0].count++;
      else if (time < 60) distribution[1].count++;
      else if (time < 90) distribution[2].count++;
      else distribution[3].count++;
    });

    const analytics = {
      overview: {
        totalSegments,
        completedSegments,
        avgEditTimePerSegment: completedSegments > 0 ? totalEditTime / completedSegments : 0,
        totalTranslators: translators?.length || 0
      },
      translatorMetrics,
      segmentDistribution: distribution
    };

    return NextResponse.json(analytics);
  } catch (error) {
    console.error('Analytics error:', error);
    return NextResponse.json(
      { error: 'Failed to load analytics' },
      { status: 500 }
    );
  }
}
