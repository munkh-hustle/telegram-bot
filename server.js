const express = require('express');
const axios = require('axios');
const app = express();

const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;

app.use(express.json());

// Webhook verification
app.post('/webhook', (req, res) => {
  const chatId = req.body.message?.chat.id;
  if (chatId) {
    axios.post(`https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendVideo`, {
      chat_id: chatId,
      video: 'BAACAgUAAxkBAAMNZ-BVwwuQGbrw7tAlSwZxNTF0XNkAAtoTAAIbd_FWoxDx_THJMrA2BA',
      caption: 'Your requested video!'
    });
  }
  res.sendStatus(200);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Running on ${PORT}`));