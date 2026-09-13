exports.up = pgm => {
    pgm.createTable('groups', {
        id: { type: 'uuid', primaryKey: true, default: pgm.func('gen_random_uuid()') },
        name: { type: 'varchar(100)', notNull: true, comment: 'Название группы' },
        currency: { type: 'varchar(10)', notNull: true, defaultValue: 'RUB', comment: 'Валюта группы' },
        inviteCode: { type: 'varchar(10)', unique: true, notNull: true, comment: 'Код приглашения' },
        ownerId: { type: 'uuid', references: 'users', onDelete: 'CASCADE', comment: 'Создатель группы' },
        createDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') },
        updateDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') }
    }, { ifNotExists: true, comment: 'Группы' });
};

exports.down = pgm => {
    pgm.dropTable('groups', { ifExists: true });
};