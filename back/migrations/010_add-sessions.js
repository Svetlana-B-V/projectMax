exports.up = pgm => {
    pgm.createTable('sessions', {
        id: { type: 'uuid', primaryKey: true, default: pgm.func('gen_random_uuid()') },
        userId: { type: 'uuid', references: 'users', onDelete: 'CASCADE', notNull: true, comment: 'Пользователь' },
        token: { type: 'text', notNull: true, unique: true, comment: 'JWT токен' },
        expiresAt: { type: 'timestamp with time zone', comment: 'Срок действия (может быть null для бессрочных)' },
        createDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') }
    }, { ifNotExists: true, comment: 'Сессии пользователей' });
};

exports.down = pgm => {
    pgm.dropTable('sessions', { ifExists: true });
};