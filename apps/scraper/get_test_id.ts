
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

async function main() {
    const researcher = await prisma.researcher.findFirst({
        where: {
            openalexId: { not: null }
        }
    });
    console.log('TEST_ID:' + researcher?.id);
}

main()
    .catch(e => console.error(e))
    .finally(async () => {
        await prisma.$disconnect();
    });
