import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const OLLAMA_URL = 'http://localhost:11434/api/embeddings';
const EMBEDDING_MODEL = 'nomic-embed-text';
const BATCH_SIZE = 10;

interface Researcher {
  id: string;
  firstName: string;
  lastName: string;
  title: string | null;
  bio: string | null;
  position: string | null;
}

async function getEmbedding(text: string): Promise<number[]> {
  const response = await fetch(OLLAMA_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: EMBEDDING_MODEL,
      prompt: text
    })
  });

  if (!response.ok) {
    throw new Error(`Ollama error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.embedding;
}

function buildResearcherText(researcher: Researcher): string {
  const parts = [
    `${researcher.firstName} ${researcher.lastName}`,
    researcher.title,
    researcher.position,
    researcher.bio
  ].filter(Boolean);

  return parts.join(' ').substring(0, 4000); // Limit text length
}

async function generateEmbeddings() {
  console.log('Starting embedding generation...');
  console.log(`Model: ${EMBEDDING_MODEL}`);

  // First, ensure the vector extension and column exist
  console.log('Setting up pgvector...');
  await prisma.$executeRawUnsafe(`CREATE EXTENSION IF NOT EXISTS vector;`);

  // Check if embedding column exists, if not add it (768 dims for nomic-embed-text)
  try {
    await prisma.$executeRawUnsafe(`
      ALTER TABLE researchers
      ADD COLUMN IF NOT EXISTS embedding vector(768);
    `);
    await prisma.$executeRawUnsafe(`
      ALTER TABLE researchers
      ADD COLUMN IF NOT EXISTS "embeddingUpdatedAt" TIMESTAMP;
    `);
  } catch (e) {
    // Column might already exist with different type
    console.log('Embedding column exists or alter failed, continuing...');
  }

  // Get all researchers without embeddings or all of them
  const researchers = await prisma.researcher.findMany({
    select: {
      id: true,
      firstName: true,
      lastName: true,
      title: true,
      bio: true,
      position: true
    }
  }) as Researcher[];

  console.log(`Found ${researchers.length} researchers to process`);

  let processed = 0;
  let errors = 0;

  for (let i = 0; i < researchers.length; i += BATCH_SIZE) {
    const batch = researchers.slice(i, i + BATCH_SIZE);

    for (const researcher of batch) {
      try {
        const text = buildResearcherText(researcher);
        if (text.length < 10) {
          console.log(`Skipping ${researcher.firstName} ${researcher.lastName} - no content`);
          continue;
        }

        const embedding = await getEmbedding(text);

        // Store embedding using raw SQL
        const vectorStr = `[${embedding.join(',')}]`;
        await prisma.$executeRawUnsafe(`
          UPDATE researchers
          SET embedding = $1::vector,
              "embeddingUpdatedAt" = NOW()
          WHERE id = $2
        `, vectorStr, researcher.id);

        processed++;
        if (processed % 50 === 0) {
          console.log(`Processed ${processed}/${researchers.length} researchers...`);
        }

      } catch (err) {
        errors++;
        console.error(`Error for ${researcher.firstName} ${researcher.lastName}: ${err}`);
      }
    }

    // Small delay between batches
    await new Promise(r => setTimeout(r, 100));
  }

  console.log('\n--- Embedding Generation Complete ---');
  console.log(`Processed: ${processed}`);
  console.log(`Errors: ${errors}`);
}

generateEmbeddings()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
