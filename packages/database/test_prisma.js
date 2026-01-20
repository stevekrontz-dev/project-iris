const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function main() {
  console.log('Connecting to database...');
  const count = await prisma.researcher.count();
  console.log('Total researchers:', count);
  
  const sample = await prisma.researcher.findMany({ take: 3 });
  sample.forEach(r => console.log(`- ${r.firstName} ${r.lastName}`));
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
