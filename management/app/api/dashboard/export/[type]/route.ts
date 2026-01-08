import { NextResponse } from 'next/server';
import { getAuthenticatedPM } from '@/lib/auth';
import { supabase } from '@/lib/supabase';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ type: string }> }
) {
  const pm = await getAuthenticatedPM();
  const { type } = await params;

  if (!pm) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  try {
    let csvContent = '';

    switch (type) {
      case 'translations': {
        csvContent = 'Segment ID,Source Text,Translation,Translator,Edit Time,Insertions,Deletions\n';

        const { data: translators } = await supabase
          .from('users')
          .select('*')
          .eq('project_key', pm.projectKey)
          .eq('role', 'translator');

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
              metricsArray.forEach((m: any) => {
                const row = [
                  m.segment_id || 'N/A',
                  `"${(m.source || m.original || '').replace(/"/g, '""')}"`,
                  `"${(m.edited || '').replace(/"/g, '""')}"`,
                  `"${translator.name} ${translator.surname}"`,
                  m.edit_time || 0,
                  m.insertions || 0,
                  m.deletions || 0
                ].join(',');
                csvContent += row + '\n';
              });
            }
          }
        }
        break;
      }

      case 'metrics': {
        csvContent = 'Translator,Segments Completed,Total Edit Time,Total Insertions,Total Deletions,Avg Edit Time\n';

        const { data: translators } = await supabase
          .from('users')
          .select('*')
          .eq('project_key', pm.projectKey)
          .eq('role', 'translator');

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
              const avgEditTime = totalEditTime / segmentsCompleted;

              const row = [
                `"${translator.name} ${translator.surname}"`,
                segmentsCompleted,
                totalEditTime.toFixed(2),
                insertions,
                deletions,
                avgEditTime.toFixed(2)
              ].join(',');
              csvContent += row + '\n';
            }
          }
        }
        break;
      }

      case 'activity': {
        csvContent = 'Translator,Segment ID,Edit Time,Insertions,Deletions\n';

        const { data: translators } = await supabase
          .from('users')
          .select('*')
          .eq('project_key', pm.projectKey)
          .eq('role', 'translator');

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
              metricsArray.forEach((m: any) => {
                const row = [
                  `"${translator.name} ${translator.surname}"`,
                  m.segment_id || 'N/A',
                  m.edit_time || 0,
                  m.insertions || 0,
                  m.deletions || 0
                ].join(',');
                csvContent += row + '\n';
              });
            }
          }
        }
        break;
      }

      case 'summary': {
        const { data: projectFiles } = await supabase
          .from('project_files')
          .select('line_count')
          .eq('project_key', pm.projectKey)
          .single();

        const { data: translators } = await supabase
          .from('users')
          .select('*')
          .eq('project_key', pm.projectKey)
          .eq('role', 'translator');

        const totalSegments = projectFiles?.line_count || 0;
        let completedSegments = 0;
        let totalEditTime = 0;

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
              totalEditTime += metricsArray.reduce((sum: number, m: any) => sum + (m.edit_time || 0), 0);
            }
          }
        }

        csvContent = 'Metric,Value\n';
        csvContent += `Project Key,"${pm.projectKey}"\n`;
        csvContent += `Total Translators,${translators?.length || 0}\n`;
        csvContent += `Total Segments,${totalSegments}\n`;
        csvContent += `Completed Segments,${completedSegments}\n`;
        csvContent += `Progress,"${totalSegments > 0 ? ((completedSegments / totalSegments) * 100).toFixed(1) : 0}%"\n`;
        csvContent += `Total Edit Time,"${totalEditTime.toFixed(2)}s"\n`;
        csvContent += `Average Edit Time,"${completedSegments > 0 ? (totalEditTime / completedSegments).toFixed(2) : 0}s"\n`;
        break;
      }

      default:
        return NextResponse.json(
          { error: 'Invalid export type' },
          { status: 400 }
        );
    }

    return new NextResponse(csvContent, {
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': `attachment; filename="${type}-export-${new Date().toISOString().split('T')[0]}.csv"`
      }
    });
  } catch (error) {
    console.error('Export error:', error);
    return NextResponse.json(
      { error: 'Failed to export data' },
      { status: 500 }
    );
  }
}
