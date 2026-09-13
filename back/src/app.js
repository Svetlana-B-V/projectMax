import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import swaggerJsdoc from 'swagger-jsdoc';
import swaggerUi from 'swagger-ui-express';
import path from 'path';
import { fileURLToPath } from 'url';

import { sequelize } from './config/db.js';
import './models/index.js';

import authRoutes from './routes/auth.js';
import groupRoutes from './routes/groups.js';
import expenseRoutes from './routes/expenses.js';
import debtRoutes from './routes/debts.js';
import savingsGoalRoutes from './routes/savingsGoals.js';
import analyticsRoutes from './routes/analytics.js';
import categoryRoutes from './routes/categories.js';
import reminderRoutes from './routes/reminders.js';
import achievementRoutes from './routes/achievements.js';

import { auth } from './middlewares/auth.js';
import { errorHandler } from './middlewares/errorHandler.js';
import { env } from './config/env.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

// Swagger
const swaggerOptions = {
  definition: {
    openapi: '3.0.0',
    info: { title: 'Общак API', version: '1.0.0', description: 'API для сервиса совместных финансов «Общак»' },
    servers: [{ url: `http://localhost:${env.port}` }],
  },
  apis: ['./src/routes/*.js'],
};
const swaggerSpec = swaggerJsdoc(swaggerOptions);
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(morgan('dev'));

// API
app.use('/api/auth', authRoutes);
app.use('/api/groups', auth, groupRoutes);
app.use('/api/expenses', auth, expenseRoutes);
app.use('/api/debts', auth, debtRoutes);
app.use('/api/savings-goals', auth, savingsGoalRoutes);
app.use('/api/analytics', auth, analyticsRoutes);
app.use('/api/categories', auth, categoryRoutes);
app.use('/api/reminders', auth, reminderRoutes);
app.use('/api/achievements', auth, achievementRoutes);

// Статические файлы фронтенда
const frontendPath = path.join(__dirname, '../../front');
app.use(express.static(frontendPath));

// Все не-API запросы отдают index.html
app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api')) {
    return next();
  }
  res.sendFile(path.join(frontendPath, 'index.html'));
});

app.use(errorHandler);

const init = async () => {
  await sequelize.authenticate();
  console.log('Подключение к PostgreSQL установлено');
};

init().catch(err => {
  console.error('Ошибка инициализации БД:', err);
  process.exit(1);
});

export default app;