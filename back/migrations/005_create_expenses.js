exports.up = pgm => {
    pgm.createTable('expenses', {
        id: { type: 'uuid', primaryKey: true, default: pgm.func('gen_random_uuid()') },
        groupId: { type: 'uuid', references: 'groups', onDelete: 'CASCADE', notNull: true, comment: 'Группа' },
        payerId: { type: 'uuid', references: 'users', notNull: true, comment: 'Кто заплатил' },
        categoryId: { type: 'uuid', references: 'categories', comment: 'Категория' },
        amount: { type: 'decimal(10,2)', notNull: true, comment: 'Сумма' },
        description: { type: 'text', comment: 'Описание' },
        date: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()'), comment: 'Дата траты' },
        receiptPhotoUrl: { type: 'text', comment: 'Фото чека' },
        createDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') },
        updateDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') }
    }, { ifNotExists: true, comment: 'Расходы' });

    // Индексы для быстрых запросов
    pgm.createIndex('expenses', 'groupId', { name: 'idx_expenses_group_id' });
    pgm.createIndex('expenses', 'date', { name: 'idx_expenses_date' });
    pgm.createIndex('expenses', 'payerId', { name: 'idx_expenses_payer_id' });
};

exports.down = pgm => {
    pgm.dropTable('expenses', { ifExists: true });
};