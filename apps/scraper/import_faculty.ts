import { PrismaClient } from '@prisma/client';
import * as fs from 'fs';
import * as path from 'path';

const prisma = new PrismaClient();

interface ScrapedFaculty {
  net_id: string;
  name: string;
  first_name: string | null;
  last_name: string | null;
  title: string | null;
  department: string | null;
  college: string | null;
  email: string | null;
  phone: string | null;
  office: string | null;
  photo_url: string | null;
  bio: string | null;
  research_interests: string[];
  education: string[];
  publications: string[];
  courses: string[];
  profile_url: string | null;
}

// Clean college name - remove extra text after newlines
function cleanCollegeName(college: string | null): string | null {
  if (!college) return null;
  // Take only the first line and clean it
  let clean = college.split('\n')[0].trim();
  // Remove common suffixes
  clean = clean.replace(/\s+(at|in|for)\s+.*$/i, '').trim();
  if (clean.length < 3 || clean.includes('Contact')) return null;
  return clean;
}

// Parse name into first/last
function parseName(name: string): { firstName: string; lastName: string } {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) {
    return { firstName: parts[0], lastName: '' };
  }
  const lastName = parts.pop() || '';
  const firstName = parts.join(' ');
  return { firstName, lastName };
}

async function importFaculty() {
  console.log('Starting faculty import...');

  // Read scraped data
  const dataPath = path.join(__dirname, 'output', 'faculty_fixed.json');
  const rawData = fs.readFileSync(dataPath, 'utf-8');
  const facultyData: ScrapedFaculty[] = JSON.parse(rawData);

  console.log(`Loaded ${facultyData.length} faculty profiles`);

  // Track created entities
  const collegeMap = new Map<string, string>(); // name -> id
  const departmentMap = new Map<string, string>(); // name -> id

  let imported = 0;
  let skipped = 0;
  let errors = 0;

  // Create data import record
  const dataImport = await prisma.dataImport.create({
    data: {
      source: 'ksu_facultyweb',
      status: 'RUNNING',
      recordsFound: facultyData.length,
      startedAt: new Date(),
    }
  });

  for (const faculty of facultyData) {
    try {
      // Skip if no email
      if (!faculty.email) {
        skipped++;
        continue;
      }

      // Parse name
      let firstName = faculty.first_name;
      let lastName = faculty.last_name;
      if (!firstName || firstName === 'null' || lastName === 'KSU') {
        const parsed = parseName(faculty.name);
        firstName = parsed.firstName;
        lastName = parsed.lastName;
      }

      // Skip if still no valid name
      if (!firstName || firstName.length < 2) {
        skipped++;
        continue;
      }

      // Get or create college
      let collegeId: string | null = null;
      const cleanCollege = cleanCollegeName(faculty.college);
      if (cleanCollege) {
        if (!collegeMap.has(cleanCollege)) {
          // Find existing or create new
          let college = await prisma.college.findFirst({
            where: { name: cleanCollege }
          });
          if (!college) {
            college = await prisma.college.create({
              data: { name: cleanCollege }
            });
          }
          collegeMap.set(cleanCollege, college.id);
        }
        collegeId = collegeMap.get(cleanCollege)!;
      }

      // Get or create department
      let departmentId: string | null = null;
      if (faculty.department) {
        const deptKey = `${faculty.department}|${collegeId || ''}`;
        if (!departmentMap.has(deptKey)) {
          const dept = await prisma.department.create({
            data: {
              name: faculty.department,
              collegeId: collegeId,
            }
          });
          departmentMap.set(deptKey, dept.id);
        }
        departmentId = departmentMap.get(deptKey)!;
      }

      // Check if user already exists
      const existingUser = await prisma.user.findUnique({
        where: { email: faculty.email }
      });

      if (existingUser) {
        skipped++;
        continue;
      }

      // Create user and researcher
      const user = await prisma.user.create({
        data: {
          email: faculty.email,
          name: `${firstName} ${lastName}`.trim(),
          role: 'RESEARCHER',
          researcher: {
            create: {
              firstName: firstName,
              lastName: lastName || '',
              title: faculty.title?.replace(/^(Dr\.|Prof\.)?\s*/i, '').trim() || null,
              position: faculty.title,
              bio: faculty.bio,
              photoUrl: faculty.photo_url,
              departmentId: departmentId,
              officeLocation: faculty.office,
              officePhone: faculty.phone,
              profileStatus: 'UNCLAIMED',
            }
          }
        }
      });

      imported++;
      if (imported % 100 === 0) {
        console.log(`Imported ${imported} profiles...`);
      }

    } catch (err) {
      errors++;
      console.error(`Error importing ${faculty.email}: ${err}`);
    }
  }

  // Update import record
  await prisma.dataImport.update({
    where: { id: dataImport.id },
    data: {
      status: errors > 0 ? 'COMPLETED' : 'COMPLETED',
      recordsImported: imported,
      recordsFailed: errors + skipped,
      completedAt: new Date(),
    }
  });

  console.log('\n--- Import Complete ---');
  console.log(`Imported: ${imported}`);
  console.log(`Skipped: ${skipped}`);
  console.log(`Errors: ${errors}`);
  console.log(`Colleges created: ${collegeMap.size}`);
  console.log(`Departments created: ${departmentMap.size}`);
}

importFaculty()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
