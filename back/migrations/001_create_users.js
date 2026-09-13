exports.up = pgm => {
    pgm.createTable('users', {
        id: { type: 'uuid', primaryKey: true, default: pgm.func('gen_random_uuid()') },
        telegramId: { type: 'bigint', unique: true, comment: 'Telegram ID пользователя' },
        email: { type: 'varchar(255)', unique: true, comment: 'Email пользователя' },
        name: { type: 'varchar(100)', notNull: true, comment: 'Имя пользователя' },
        avatarUrl: { type: 'text', comment: 'Ссылка на аватар' },
        createDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') },
        updateDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') }
    }, { ifNotExists: true, comment: 'Пользователи' });
};

exports.down = pgm => {
    pgm.dropTable('users', { ifExists: true });
};