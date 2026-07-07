# 🛍️ THRIFT AI - Smart Clothing Price Checker

THRIFT AI is an intelligent web application that helps you determine if you're getting a good deal on clothing items. It uses machine learning to predict fair prices and compares them against your find to tell you if it's a great deal!

## ✨ Features

- 🤖 **AI Price Prediction**: ML-powered price estimation based on brand, item type, and size
- 🔍 **Market Data Integration**: Fetches real-time data from multiple marketplaces (Amazon, Craigslist, Kijiji)
- 💡 **Deal Assessment**: Tells you if you're getting an excellent deal, fair price, or if it's overpriced
- 🎨 **Clean Interface**: User-friendly web interface with responsive design
- 🔒 **Input Validation**: Secure input handling to prevent malicious data

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Installation

1. **Clone or download this repository**
   ```bash
   cd THRIFT_AI
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys**
   ```bash
   cp apikeys.env.example apikeys.env
   ```
   Edit `apikeys.env` and add your RapidAPI key:
   ```
   API_KEY=your_rapidapi_key_here
   ```

4. **Run the application**
   ```bash
   python Main.py
   ```

5. **Open your browser**
   Visit `http://localhost:5000`

## 📊 How It Works

1. **Enter Item Details**: Input brand, item type, size, color, material, and condition
2. **Add Your Price**: Enter the price you found to get a deal assessment
3. **Get AI Analysis**: Our ML model predicts a fair price based on training data
4. **Market Comparison**: We fetch real-time data from multiple sources
5. **Deal Assessment**: Get clear feedback on whether it's a good deal

### Deal Categories
- 🎉 **Excellent Deal**: 30%+ below predicted price
- 👍 **Good Deal**: 15-30% below predicted price  
- ✅ **Fair Price**: Within 15% of predicted price
- ⚠️ **Slightly High**: 15-30% above predicted price
- 🚨 **Overpriced**: 30%+ above predicted price

## 🔧 Development

### Project Structure
```
THRIFT_AI/
├── Main.py                 # Flask web application
├── train_model.py         # ML model training script
├── utils.py               # Input validation utilities
├── amazon_api.py          # Amazon data integration
├── craigslist_api.py      # Craigslist data integration
├── kijiji_api.py          # Kijiji data integration
├── ai_scraper_api.py      # AI web scraper integration
├── templates/             # HTML templates
│   ├── input.html         # Search form
│   └── results.html       # Results page
├── *.pkl                  # Trained ML models
├── requirements.txt       # Python dependencies
├── apikeys.env.example    # API key template
└── DEPLOYMENT_CHECKLIST.md # Deployment guide
```

### Retraining the Model
If you want to retrain the ML model with new data:
```bash
python train_model.py
```

### API Integration
The app integrates with several APIs:
- **RapidAPI**: For Amazon, Craigslist, and Kijiji data
- **AI Web Scraper**: For general web scraping

## 🚢 Deployment

See `DEPLOYMENT_CHECKLIST.md` for a comprehensive deployment guide.

### Quick Deploy Options
- **Heroku**: `git push heroku main`
- **Railway**: Connect GitHub repository
- **Render**: Connect GitHub repository

### Environment Variables for Production
```bash
API_KEY=your_rapidapi_key
FLASK_SECRET_KEY=your_secret_key
FLASK_ENV=production
```

## 🔒 Security Features

- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Secure API key handling
- Rate limiting ready

## 📝 License

This project is for educational and personal use. Please ensure you comply with all API terms of service when using external data sources.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check `DEPLOYMENT_CHECKLIST.md` for common problems
- Review the Flask logs for error details
- Ensure all API keys are properly configured

---

Made with ❤️ for smart thrift shopping!