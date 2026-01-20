import { PrismaClient } from '@prisma/client';
import * as fs from 'fs';
import * as path from 'path';

const prisma = new PrismaClient();

interface OpenAlexWork {
    title: string;
    year: number;
    citations: number;
    venue: string | null;
    doi: string | null;
    landing_page_url: string | null;
}

interface OpenAlexData {
    id: string;
    display_name: string;
    works_count: number;
    cited_by_count: number;
    h_index: number;
    i10_index: number;
    topics: string[];
}

interface EnrichedFaculty {
    email: string | null;
    name: string;
    openalex?: OpenAlexData;
    publications?: OpenAlexWork[];
}

async function importOpenAlex() {
    console.log('Starting OpenAlex data import...');

    // Read enriched data
    const dataPath = process.argv[2] || path.join(__dirname, 'output', 'faculty_openalex_50.json');
    if (!fs.existsSync(dataPath)) {
        console.error(`File not found: ${dataPath}`);
        return;
    }

    const rawData = fs.readFileSync(dataPath, 'utf-8');
    const facultyData: EnrichedFaculty[] = JSON.parse(rawData);

    console.log(`Loaded ${facultyData.length} profiles to process`);

    let updated = 0;
    let skipped = 0;
    let errors = 0;
    let pubsCreated = 0;

    for (const faculty of facultyData) {
        if (!faculty.email || !faculty.openalex) {
            skipped++;
            continue;
        }

        try {
            // Find researcher
            const user = await prisma.user.findUnique({
                where: { email: faculty.email },
                include: { researcher: true }
            });

            if (!user || !user.researcher) {
                console.log(`Researcher not found for email: ${faculty.email}`);
                skipped++;
                continue;
            }

            const researcherId = user.researcher.id;

            // Update Researcher Metrics
            await prisma.researcher.update({
                where: { id: researcherId },
                data: {
                    openalexId: faculty.openalex.id,
                    hIndex: faculty.openalex.h_index,
                    citationCount: faculty.openalex.cited_by_count,
                    worksCount: faculty.openalex.works_count,
                    lastActiveAt: new Date(),
                }
            });
            updated++;

            // Upsert Publications
            if (faculty.publications && faculty.publications.length > 0) {
                for (const pub of faculty.publications) {

                    // Try to find by DOI first
                    let publication = null;
                    if (pub.doi) {
                        publication = await prisma.publication.findUnique({
                            where: { doi: pub.doi }
                        });
                    }

                    // If not found by DOI, create it
                    if (!publication) {
                        // Basic create
                        publication = await prisma.publication.create({
                            data: {
                                title: pub.title || 'Untitled',
                                publicationType: 'JOURNAL_ARTICLE', // Defaulting
                                doi: pub.doi,
                                citationCount: pub.citations || 0,
                                publishedDate: pub.year ? new Date(pub.year, 0, 1) : undefined,
                                journal: pub.venue,
                            }
                        });
                        pubsCreated++;
                    }

                    // Link Researcher to Publication
                    // Check if already linked
                    const existingLink = await prisma.publicationAuthor.findFirst({
                        where: {
                            publicationId: publication.id,
                            researcherId: researcherId
                        }
                    });

                    if (!existingLink) {
                        // Determine order (simplified: add as first author if creating, or just append)
                        const highestOrder = await prisma.publicationAuthor.findFirst({
                            where: { publicationId: publication.id },
                            orderBy: { authorOrder: 'desc' }
                        });
                        const nextOrder = (highestOrder?.authorOrder ?? 0) + 1;

                        await prisma.publicationAuthor.create({
                            data: {
                                publicationId: publication.id,
                                researcherId: researcherId,
                                authorName: faculty.name, // Fallback name
                                authorOrder: nextOrder
                            }
                        });
                    }
                }
            }

            if (updated % 50 === 0) {
                console.log(`Updated ${updated} researchers, created ${pubsCreated} publications...`);
            }

        } catch (err) {
            errors++;
            console.error(`Error processing ${faculty.email}: ${err}`);
        }
    }

    console.log('\n--- Import Complete ---');
    console.log(`Researchers Updated: ${updated}`);
    console.log(`Publications Created: ${pubsCreated}`);
    console.log(`Skipped: ${skipped}`);
    console.log(`Errors: ${errors}`);
}

importOpenAlex()
    .catch(console.error)
    .finally(() => prisma.$disconnect());
