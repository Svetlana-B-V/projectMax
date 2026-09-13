const { runner } = require('node-pg-migrate');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const direction = process.argv[2] === 'down' ? 'down' : 'up';

const databaseUrl = process.env.DATABASE_URL || `postgresql://${process.env.DB_USER}:${process.env.DB_PASSWORD}@${process.env.DB_HOST}:${process.env.DB_PORT}/${process.env.DB_DATABASE}`;

console.log('Используемая строка подключения:', databaseUrl);

runner({
    databaseUrl: databaseUrl,
    dir: path.join(__dirname, 'migrations'),
    direction: direction,
    migrationsTable: 'pgmigrations',
}).then(() => {
    console.log('✅ Миграции выполнены успешно');
}).catch((err) => {
    console.error('❌ Ошибка миграции:', err);
});