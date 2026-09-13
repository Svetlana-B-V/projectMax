exports.up = pgm => {
    pgm.createTable('group_members', {
        id: { type: 'uuid', primaryKey: true, default: pgm.func('gen_random_uuid()') },
        groupId: { type: 'uuid', references: 'groups', onDelete: 'CASCADE', notNull: true, comment: 'Группа' },
        userId: { type: 'uuid', references: 'users', onDelete: 'CASCADE', notNull: true, comment: 'Пользователь' },
        role: { type: 'varchar(20)', notNull: true, defaultValue: 'member', comment: 'Роль: owner, admin, member' },
        joinedAt: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') }
    }, { ifNotExists: true, comment: 'Участники групп' });

    // Уникальность: один пользователь может быть только один раз в группе
    pgm.addConstraint('group_members', 'unique_group_user', {
        unique: ['groupId', 'userId']
    });
};

exports.down = pgm => {
    pgm.dropTable('group_members', { ifExists: true });
};