exports.up = pgm => {
    pgm.addColumn('expenses', {
        createdById: { type: 'uuid', references: 'users', onDelete: 'SET NULL', comment: 'Автор расхода' }
    }, { ifNotExists: true });
};

exports.down = pgm => {
    pgm.dropColumn('expenses', 'createdById', { ifExists: true });
};