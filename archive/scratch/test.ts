import { trackComplaint } from './FRONTEND/src/actions/db.ts';

async function test() {
    const res = await trackComplaint("ABC-123");
    console.log(res);
}

test();
