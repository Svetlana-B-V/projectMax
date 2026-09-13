import app from './app.js';
import { env } from './config/env.js';

app.listen(env.port, () => {
  console.log(`Сервер запущен на http://localhost:${env.port}`);
  console.log(`Swagger документация: http://localhost:${env.port}/api-docs`);
});