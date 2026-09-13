exports.up = pgm => {
    pgm.createTable('debts', {
        id: { type: 'uuid', primaryKey: true, default: pgm.func('gen_random_uuid()') },
        groupId: { type: 'uuid', references: 'groups', onDelete: 'CASCADE', notNull: true, comment: 'Группа' },
        fromUserId: { type: 'uuid', references: 'users', onDelete: 'CASCADE', notNull: true, comment: 'Должник' },
        toUserId: { type: 'uuid', references: 'users', onDelete: 'CASCADE', notNull: true, comment: 'Кредитор' },
        amount: { type: 'decimal(10,2)', notNull: true, comment: 'Сумма долга' },
        status: { type: 'varchar(20)', notNull: true, defaultValue: 'active', comment: 'Статус: active, paid' },
        createDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') },
        updateDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') }
    }, { ifNotExists: true, comment: 'Долги' });

    pgm.createIndex('debts', 'groupId', { name: 'idx_debts_group_id' });
    pgm.createIndex('debts', 'fromUserId', { name: 'idx_debts_from_user' });
    pgm.createIndex('debts', 'toUserId', { name: 'idx_debts_to_user' });
};

exports.down = pgm => {
    pgm.dropTable('debts', { ifExists: true });
};