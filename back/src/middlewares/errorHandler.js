export const errorHandler = (err, req, res, next) => {
  // Безопасное логирование
  if (err) {
    console.error('Error message:', err.message || 'Unknown error');
    if (err.stack) {
      console.error('Stack:', err.stack);
    }
  }

  if (err.name === 'ZodError') {
    return res.status(400).json({ message: 'Ошибка валидации', errors: err.errors });
  }

  res.status(err.status || 500).json({ message: err.message || 'Внутренняя ошибка сервера' });
};