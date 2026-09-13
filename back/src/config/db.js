import { Sequelize } from 'sequelize';
import { env } from './env.js';

const sequelize = new Sequelize(env.db.database, env.db.user, env.db.password, {
  host: env.db.host,
  port: env.db.port,
  dialect: 'postgres',
  logging: false,
  define: {
    freezeTableName: true,
    timestamps: true,
    createdAt: 'createDate',
    updatedAt: 'updateDate',
  },
});

export { sequelize };