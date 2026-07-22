const TelegramBot = require('node-telegram-bot-api');

// Токен и настройки берутся из переменных окружения Railway,
// никогда не хардкодим их в коде
const TOKEN = process.env.BOT_TOKEN;
const ENV_NAME = process.env.ENVIRONMENT_NAME || 'unknown';

if (!TOKEN) {
  console.error('Ошибка: переменная BOT_TOKEN не задана!');
  process.exit(1);
}

// polling: true — бот сам постоянно спрашивает у Telegram новые сообщения
const bot = new TelegramBot(TOKEN, { polling: true });

console.log(`Бот запущен в окружении: ${ENV_NAME}`);

bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  bot.sendMessage(chatId, `Привет! Я тестовый бот.\nОкружение: ${ENV_NAME}`);
});

bot.onText(/\/ping/, (msg) => {
  const chatId = msg.chat.id;
  bot.sendMessage(chatId, 'pong 🏓');
});

bot.on('message', (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text;

  // Игнорируем команды, чтобы не дублировать ответ
  if (text && !text.startsWith('/')) {
    bot.sendMessage(chatId, `Вы написали: ${text}`);
  }
});

bot.on('polling_error', (error) => {
  console.error('Polling error:', error.message);
});

process.on('SIGTERM', () => {
  console.log('Получен SIGTERM, останавливаю бота...');
  bot.stopPolling();
  process.exit(0);
});