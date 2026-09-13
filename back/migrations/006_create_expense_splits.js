exports.up = pgm => {
    pgm.createTable('expense_splits', {
        id: { type: 'uuid', primaryKey: true, default: pgm.func('gen_random_uuid()') },
        expenseId: { type: 'uuid', references: 'expenses', onDelete: 'CASCADE', notNull: true, comment: 'Расход' },
        userId: { type: 'uuid', references: 'users', onDelete: 'CASCADE', notNull: true, comment: 'Участник' },
        amountOwed: { type: 'decimal(10,2)', notNull: true, comment: 'Сколько должен' },
        isPaid: { type: 'boolean', notNull: true, defaultValue: false, comment: 'Оплачено ли' },
        createDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') }
    }, { ifNotExists: true, comment: 'Разделение расходов' });

    pgm.createIndex('expense_splits', 'expenseId', { name: 'idx_splits_expense_id' });
    pgm.createIndex('expense_splits', 'userId', { name: 'idx_splits_user_id' });
};

exports.down = pgm => {
    pgm.dropTable('expense_splits', { ifExists: true });
};