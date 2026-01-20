import { PrismaClient } from '@prisma/client';
import * as fs from 'fs';
import * as path from 'path';

const prisma = new PrismaClient();

interface FixedFaculty {
  net_id: string;
  name: string;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
}

async function updateNames() {
  console.log('Starting name update from fixed data...');

  // Read fixed data
  const dataPath = path.join(__dirname, 'output', 'faculty_fixed.json');
  const rawData = fs.readFileSync(dataPath, 'utf-8');
  const facultyData: FixedFaculty[] = JSON.parse(rawData);

  console.log(`Loaded ${facultyData.length} faculty profiles`);

  let updated = 0;
  let notFound = 0;
  let errors = 0;

  for (const faculty of facultyData) {
    if (!faculty.email) {
      continue;
    }

    // Skip if name is still bad
    if (!faculty.name || faculty.name === 'KSU' || faculty.name.length < 3) {
      continue;
    }

    try {
      // Find user by email
      const user = await prisma.user.findUnique({
        where: { email: faculty.email },
        include: { researcher: true }
      });

      if (!user || !user.researcher) {
        notFound++;
        continue;
      }

      // Update user and researcher names
      await prisma.user.update({
        where: { id: user.id },
        data: {
          name: faculty.name,
          researcher: {
            update: {
              firstName: faculty.first_name || faculty.name.split(' ')[0],
              lastName: faculty.last_name || faculty.name.split(' ').slice(-1)[0] || ''
            }
          }
        }
      });

      updated++;
      if (updated % 100 === 0) {
        console.log(`Updated ${updated} profiles...`);
      }

    } catch (err) {
      errors++;
      console.error(`Error updating ${faculty.email}: ${err}`);
    }
  }

  console.log('\n--- Update Complete ---');
  console.log(`Updated: ${updated}`);
  console.log(`Not found: ${notFound}`);
  console.log(`Errors: ${errors}`);
}

updateNames()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
