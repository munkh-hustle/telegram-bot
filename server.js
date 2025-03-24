require('dotenv').config();
const express = require('express');
const axios = require('axios');
const crypto = require('crypto');

const app = express();
const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;

app.use(express.static('public'));
app.use(express.json());

// Authentication endpoint
app.post('/auth', (req, res) => {
    const authData = req.body;
    
    // Verify the data (important for security)
    const checkString = Object.keys(authData)
        .filter(key => key !== 'hash')
        .map(key => `${key}=${authData[key]}`)
        .join('\n');
    
    const secretKey = crypto.createHash('sha256')
        .update(TELEGRAM_TOKEN)
        .digest();
    
    const hash = crypto.createHmac('sha256', secretKey)
        .update(checkString)
        .digest('hex');
    
    if (hash !== authData.hash) {
        return res.status(403).send('Invalid authentication');
    }

    // Return user data to store in frontend
    res.json({
        id: authData.id,
        first_name: authData.first_name
    });
});

app.post('/send-video', async (req, res) => {
    try {
        const user = req.body;
        
        await axios.post(`https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendVideo`, {
            chat_id: user.id,
            video: 'BAACAgUAAxkBAAMNZ-BVwwuQGbrw7tAlSwZxNTF0XNkAAtoTAAIbd_FWoxDx_THJMrA2BA',
            caption: 'Pluto 2024 Бүлэг-1 Анги-2 орлоо😊',
            supports_streaming: true // Allows streaming
        });

        res.json({ message: 'Video sent to your Telegram!' });
    } catch (error) {
        console.error('Error details:', {
            status: error.response?.status,
            data: error.response?.data,
            message: error.message
        });
        res.status(500).json({ 
            message: 'Failed to send video',
            error: error.response?.data || error.message
        });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));