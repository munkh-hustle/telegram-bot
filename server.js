const express = require('express');
const axios = require('axios');
const path = require('path');

const app = express();
const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;

// Handle Telegram auth callback
app.get('/auth', (req, res) => {
  // Verify auth data here
  res.redirect('/'); // Return to main page after auth
});

// Handle video sending
app.post('/send-video', express.json(), async (req, res) => {
  try {
      await axios.post(`https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendVideo`, {
          chat_id: req.body.user.id,
          video: 'YOUR_FILE_ID',
          caption: 'Here is your video!'
      });
      res.json({ success: true });
  } catch (error) {
      res.status(500).json({ 
          error: error.response?.data?.description || 'Failed to send video' 
      });
  }
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));