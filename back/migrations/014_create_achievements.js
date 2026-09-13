const CATALOG = [
  {
    code: 'first_expense',
    name: 'Первый шаг',
    description: 'Добавь первый расход',
    icon: '🧾',
  },
  {
    code: 'three_expenses',
    name: 'Бухгалтер',
    description: 'Добавь 3 расхода',
    icon: '📊',
  },
  {
    code: 'first_payment',
    name: 'Честный должник',
    description: 'Верни долг хотя бы раз',
    icon: '🤝',
  },
  {
    code: 'first_contribute',
    name: 'Белочка',
    description: 'Положи деньги в копилку',
    icon: '🐿️',
  },
  {
    code: 'first_group',
    name: 'Хозяин',
    description: 'Создай группу',
    icon: '🏠',
  },
];

exports.up = pgm => {
  pgm.createTable('achievements', {
    code: { type: 'varchar(50)', primaryKey: true, comment: 'Стабильный код' },
    name: { type: 'varchar(100)', notNull: true },
    description: { type: 'text', notNull: true },
    icon: { type: 'varchar(20)' },
  }, { ifNotExists: true, comment: 'Каталог достижений' });

  pgm.createTable('user_achievements', {
    userId: {
      type: 'uuid',
      notNull: true,
      references: 'users',
      onDelete: 'CASCADE',
    },
    achievementCode: {
      type: 'varchar(50)',
      notNull: true,
      references: 'achievements',
      onDelete: 'CASCADE',
    },
    earnedAt: {
      type: 'timestamp with time zone',
      notNull: true,
      default: pgm.func('now()'),
    },
  }, { ifNotExists: true, comment: 'Полученные достижения' });

  pgm.addConstraint('user_achievements', 'user_achievements_unique', {
    unique: ['userId', 'achievementCode'],
  });

  for (const row of CATALOG) {
    pgm.sql(
      `INSERT INTO achievements (code, name, description, icon) VALUES ('${row.code}', '${row.name}', '${row.description}', '${row.icon}') ON CONFLICT (code) DO NOTHING`
    );
  }
};

exports.down = pgm => {
  pgm.dropTable('user_achievements', { ifExists: true });
  pgm.dropTable('achievements', { ifExists: true });
};
