exports.up = pgm => {
    pgm.createTable('reminder_settings', {
        userId: {
            type: 'uuid',
            primaryKey: true,
            references: 'users',
            onDelete: 'CASCADE',
            notNull: true,
            comment: 'Пользователь',
        },
        style: {
            type: 'varchar(20)',
            notNull: true,
            default: 'neutral',
            comment: 'soft | neutral | playful',
        },
        enabled: {
            type: 'boolean',
            notNull: true,
            default: true,
            comment: 'Присылать напоминания о долгах',
        },
        lastRemindedAt: {
            type: 'timestamp with time zone',
            comment: 'Когда бот в последний раз напомнил',
        },
    }, { ifNotExists: true, comment: 'Настройки напоминаний о долгах' });
};

exports.down = pgm => {
    pgm.dropTable('reminder_settings', { ifExists: true });
};
