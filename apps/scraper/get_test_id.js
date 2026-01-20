
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function main() {
    try {
        const researcher = await prisma.researcher.findFirst({
            where: { openalexId: { not: null } }
        });
        if (researcher) {
            console.log('TEST_ID:' + researcher.id);
        } else {
            console.log('NO_RESEARCHER_FOUND');
        }
    } catch (e) {
        console.error(e);
    } finally {
        await prisma.$disconnect();
    }
}

main();
