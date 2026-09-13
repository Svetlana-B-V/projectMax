exports.up = pgm => {
    pgm.createTable('debt_payments', {
        id: { type: 'uuid', primaryKey: true, default: pgm.func('gen_random_uuid()') },
        debtId: { type: 'uuid', references: 'debts', onDelete: 'CASCADE', notNull: true, comment: 'Долг' },
        amount: { type: 'decimal(10,2)', notNull: true, comment: 'Сумма возврата' },
        createDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') }
    }, { ifNotExists: true, comment: 'Платежи по долгам' });
};

exports.down = pgm => {
    pgm.dropTable('debt_payments', { ifExists: true });
};