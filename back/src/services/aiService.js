export const recognizeReceipt = async (imageBuffer) => {
  // Заглушка: в реальном проекте здесь будет вызов ИИ
  return {
    amount: 1234.56,
    date: new Date().toISOString(),
    category: 'Продукты',
    description: 'Магазин',
  };
};

export const getBudgetPrediction = async (monthlyExpenses) => {
  const totalSpent = monthlyExpenses.reduce((sum, e) => sum + parseFloat(e.amount), 0);
  const daysPassed = new Date().getDate();
  const daysInMonth = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate();
  return (totalSpent / daysPassed) * daysInMonth;
};