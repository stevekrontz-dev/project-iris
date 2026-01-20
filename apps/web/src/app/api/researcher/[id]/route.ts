import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    const researcher = await prisma.researcher.findUnique({
      where: { id },
      include: {
        department: {
          include: {
            college: true
          }
        },
        user: {
          select: {
            email: true
          }
        },
        publications: {
          include: {
            publication: true
          },
          orderBy: {
            publication: {
              publishedDate: 'desc'
            }
          }
        }
      }
    });

    if (!researcher) {
      return NextResponse.json(
        { error: 'Researcher not found' },
        { status: 404 }
      );
    }

    const formatted = {
      id: researcher.id,
      net_id: researcher.id, // Legacy compat
      firstName: researcher.firstName,
      lastName: researcher.lastName,
      name: (researcher.firstName || '') + ' ' + (researcher.lastName || ''),
      title: researcher.title,
      position: researcher.position,
      bio: researcher.bio,
      photoUrl: researcher.photoUrl,
      department: researcher.department?.name || null,
      college: researcher.department?.college?.name || null,
      email: researcher.user?.email || null,

      // External IDs
      orcidId: researcher.orcidId,
      googleScholarId: researcher.googleScholarId,
      openalexId: researcher.openalexId,

      // Metrics
      h_index: researcher.hIndex || 0,
      citation_count: researcher.citationCount || 0,
      i10_index: 0, // Placeholder if not stored
      works_count: researcher.worksCount || 0,

      // Publications
      publications: researcher.publications.map(p => ({
        title: p.publication.title,
        year: p.publication.publishedDate ? new Date(p.publication.publishedDate).getFullYear() : null,
        journal: p.publication.journal,
        citations: p.publication.citationCount,
        doi: p.publication.doi,
        article_url: p.publication.doi ? `https://doi.org/${p.publication.doi}` : null
      }))
    };

    return NextResponse.json(formatted);

  } catch (error) {
    console.error('Error fetching researcher:', error);
    return NextResponse.json(
      { error: 'Failed to fetch researcher' },
      { status: 500 }
    );
  }
}
