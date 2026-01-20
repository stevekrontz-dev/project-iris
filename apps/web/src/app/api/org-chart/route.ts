import { NextResponse } from 'next/server';

const DATA_PATH = 'C:/dev/research/project-iris/apps/scraper/output/ksu_full_directory.json';

export async function GET() {
  try {
    const fs = await import('fs/promises');
    const data = await fs.readFile(DATA_PATH, 'utf-8');
    const parsed = JSON.parse(data);
    
    // Transform for frontend compatibility
    return NextResponse.json({
      generated: parsed.generated,
      total_leaders: parsed.total_people,
      by_category: parsed.categories || {},
      all_leaders: parsed.all_people || [],
      colleges: parsed.colleges || {},
      stats: {
        by_category: parsed.by_category,
        by_college: parsed.by_college,
      }
    });
  } catch (error: any) {
    return NextResponse.json({
      generated: 'Not yet generated',
      total_leaders: 0,
      by_category: {},
      all_leaders: [],
      error: 'Run cc4_org_chart.py to generate data'
    });
  }
}
