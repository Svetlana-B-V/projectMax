exports.up = pgm => {
    pgm.createTable('contributions', {
        id: { type: 'uuid', primaryKey: true, default: pgm.func('gen_random_uuid()') },
        savingsGoalId: { type: 'uuid', references: 'savings_goals', onDelete: 'CASCADE', notNull: true, comment: 'Копилка' },
        userId: { type: 'uuid', references: 'users', onDelete: 'CASCADE', notNull: true, comment: 'Кто внёс' },
        amount: { type: 'decimal(10,2)', notNull: true, comment: 'Сумма взноса' },
        note: { type: 'text', comment: 'Заметка' },
        createDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') }
    }, { ifNotExists: true, comment: 'Взносы в копилки' });

    pgm.createIndex('contributions', 'savingsGoalId', { name: 'idx_contributions_goal_id' });
    pgm.createIndex('contributions', 'userId', { name: 'idx_contributions_user_id' });
};

exports.down = pgm => {
    pgm.dropTable('contributions', { ifExists: true });
};