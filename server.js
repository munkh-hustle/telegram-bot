const express = require('express');
const axios = require('axios');
const path = require('path');

const app = express();
const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;

// Serve static files from public folder
app.use(express.static(path.join(__dirname, 'public')));

// API endpoint to send video
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

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));