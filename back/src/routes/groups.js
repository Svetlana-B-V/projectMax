import { Router } from 'express';
import { createGroup, getMyGroups, joinGroup, getGroupMembers } from '../controllers/groupController.js';
import { validate } from '../middlewares/validate.js';
import { createGroupSchema, joinGroupSchema } from '../schemas/groupSchema.js';

const router = Router();

router.post('/', validate(createGroupSchema), createGroup);
router.get('/my', getMyGroups);
router.post('/join', validate(joinGroupSchema), joinGroup);
router.get('/:groupId/members', getGroupMembers);

export default router;