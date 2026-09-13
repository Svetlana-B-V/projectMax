exports.up = pgm => {
    pgm.createTable('categories', {
        id: { type: 'uuid', primaryKey: true, default: pgm.func('gen_random_uuid()') },
        name: { type: 'varchar(100)', notNull: true, comment: 'Название категории' },
        icon: { type: 'varchar(50)', comment: 'Иконка (emoji)' },
        color: { type: 'varchar(20)', comment: 'Цвет в HEX' },
        isDefault: { type: 'boolean', notNull: true, defaultValue: false, comment: 'Общая категория' },
        groupId: { type: 'uuid', references: 'groups', onDelete: 'CASCADE', comment: 'Группа (null = общая)' },
        createDate: { type: 'timestamp with time zone', notNull: true, default: pgm.func('now()') }
    }, { ifNotExists: true, comment: 'Категории трат' });
};

exports.down = pgm => {
    pgm.dropTable('categories', { ifExists: true });
};