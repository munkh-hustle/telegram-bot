// Add this before other routes
app.use(express.json());

// Webhook endpoint must return 200 immediately
app.post('/webhook', (req, res) => {
  res.sendStatus(200); // Critical for Telegram
  
  // Process update asynchronously
  const chatId = req.body.message?.chat.id;
  if (chatId) {
    axios.post(`https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendVideo`, {
      chat_id: chatId,
      video: 'BAACAgUAAxkBAAMNZ-BVwwuQGbrw7tAlSwZxNTF0XNkAAtoTAAIbd_FWoxDx_THJMrA2BA'
    }).catch(console.error);
  }
});
const express = require('express');
const path = require('path');
const axios = require('axios');

const app = express();
const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;

// Serve static files from public directory
app.use(express.static(path.join(__dirname, 'public')));

// Handle root route - serve index.html
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Telegram auth callback
app.get('/auth', (req, res) => {
    // Validate Telegram auth data here
    // For now, just redirect back to home
    res.redirect('/');
});

// Video sending endpoint
app.post('/send-video', express.json(), async (req, res) => {
    try {
        await axios.post(`https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendVideo`, {
            chat_id: req.body.user.id,
            video: 'BAACAgUAAxkBAAMNZ-BVwwuQGbrw7tAlSwZxNTF0XNkAAtoTAAIbd_FWoxDx_THJMrA2BA',
            caption: 'Here is your requested video!'
        });
        res.json({ success: true });
    } catch (error) {
        console.error('Error sending video:', error.response?.data || error.message);
        res.status(500).json({ 
            error: error.response?.data?.description || 'Failed to send video' 
        });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Access at: http://localhost:${PORT}`);
});