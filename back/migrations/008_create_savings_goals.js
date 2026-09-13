exports.up = pgm => {
    pgm.createTable('savings_goals', {
        id: { type: 'uuid', primaryKey: true, default: pgm.func('gen_random_uuid()') },
        groupId: { type: 'uuid', references: 'groups', onDelete: 'CASCADE', notNull: true, comment: 'Группа' },
        name: { type: 'varchar(100)', notNull: true, comment: 'Название копилки' },
        type: { type: 'varchar(20)', notNull: true, defaultValue: 'group', comment: 'Тип: group, personal' },
        targetAmount: { type: 'decimal(10,2)', notNull: true, comment: 'Целевая сумма' },
        currentAmount: { type: 'decimal(10,2)', notNull: true, defaultValue: 0, comment: 'Текущая сумма' },
        createdBy: { type: 'uuid', references: 'users', comment: 'Создатель' },
        deadline: { type: 'timestamp with time zone', comment: 'Дедлайн' },
        status: { type: 'varchar(20)', notNull: true, defaultValue: 'active', comment: 'Статус: active, completed, cancelled' },
        createDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') },
        updateDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') }
    }, { ifNotExists: true, comment: 'Копилки' });

    pgm.createIndex('savings_goals', 'groupId', { name: 'idx_savings_group_id' });
};

exports.down = pgm => {
    pgm.dropTable('savings_goals', { ifExists: true });
};