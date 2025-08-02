# AI Research Paper Analyzer

An intelligent research paper analysis system that uses advanced AI to extract topics, generate summaries, and suggest related research areas from uploaded academic papers.

## Features

### 🤖 AI-Powered Analysis
- **Text Extraction**: Supports PDF, DOCX, and TXT files
- **Topic Extraction**: Uses NLP to identify key topics and themes
- **Smart Summarization**: Generates concise summaries of research papers
- **Topic Suggestions**: AI-powered recommendations for related research areas
- **Relevance Scoring**: Quantifies topic relevance with percentage scores

### 👤 User Management
- **User Authentication**: Secure login and registration system
- **Paper Management**: Track and organize uploaded research papers
- **Personalized Suggestions**: Topic recommendations based on user's research history
- **Analysis History**: View past analysis results and summaries

### 🎨 Modern Interface
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Drag & Drop Upload**: Intuitive file upload with visual feedback
- **Real-time Analysis**: Live progress tracking during paper processing
- **Interactive Results**: Clickable topic tags with relevance scores
- **Clean UI**: Modern, professional interface design

## Technology Stack

### Backend
- **Node.js**: Server runtime environment
- **Express.js**: Web application framework
- **MongoDB**: Document database for data storage
- **Mongoose**: MongoDB object modeling
- **Multer**: File upload handling
- **JWT**: JSON Web Token authentication
- **bcryptjs**: Password hashing

### AI & NLP
- **Python**: AI processing backend
- **NLTK**: Natural Language Toolkit for text processing
- **scikit-learn**: Machine learning algorithms
- **PyPDF2**: PDF text extraction
- **python-docx**: DOCX document processing
- **OpenAI API**: Advanced language model integration

### Frontend
- **HTML5**: Modern markup
- **CSS3**: Advanced styling with animations
- **JavaScript (ES6+)**: Interactive functionality
- **Bootstrap 5**: Responsive UI framework
- **Font Awesome**: Icon library

## Installation & Setup

### Prerequisites
- Node.js (v14 or higher)
- Python 3.8+
- MongoDB (v4.4 or higher)
- npm or yarn package manager

### 1. Clone and Setup
```bash
# Navigate to project directory
cd ai-research-analyzer

# Install Node.js dependencies
npm install

# Install Python dependencies
pip3 install -r requirements.txt
```

### 2. Database Setup
```bash
# Start MongoDB service
sudo systemctl start mongod

# Enable MongoDB to start on boot
sudo systemctl enable mongod

# Verify MongoDB is running
sudo systemctl status mongod
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
# Server Configuration
PORT=3000
NODE_ENV=development

# Database Configuration
MONGODB_URI=mongodb://localhost:27017/research_analyzer

# JWT Configuration
JWT_SECRET=your_jwt_secret_key_here
JWT_EXPIRES_IN=7d

# OpenAI Configuration (Optional - for enhanced AI features)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
```

### 4. Start the Application
```bash
# Start the server
npm start

# Or for development with auto-restart
npm run dev
```

The application will be available at `http://localhost:3000`

## Usage Guide

### 1. User Registration/Login
- Navigate to the application homepage
- Click "Login" to access the authentication modal
- Register a new account or login with existing credentials
- User sessions are maintained with JWT tokens

### 2. Upload Research Papers
- Click on the upload area or drag & drop files
- Supported formats: PDF, DOCX, TXT
- Optionally add paper title and authors
- Click "Analyze Paper" to start processing

### 3. View Analysis Results
- **Summary**: AI-generated abstract of the paper
- **Extracted Topics**: Key topics found in the paper with relevance scores
- **Suggested Topics**: Related research areas recommended by AI
- **Research Areas**: Potential research directions with explanations

### 4. Manage Papers
- View all uploaded papers in "My Papers" section
- Click on any paper to view detailed analysis
- Delete papers when no longer needed
- Track analysis status (uploaded, processing, analyzed, failed)

### 5. Explore Topics
- Browse available research topics in the "Topics" section
- View personalized topic suggestions based on your papers
- Discover new research areas related to your interests

## API Documentation

### Authentication Endpoints
```
POST /api/register - User registration
POST /api/login - User login
GET /api/profile - Get user profile
```

### Paper Management Endpoints
```
POST /api/papers/upload - Upload and analyze paper
GET /api/papers - Get user's papers
GET /api/papers/:id - Get specific paper
GET /api/papers/:id/analysis - Get paper analysis
DELETE /api/papers/:id - Delete paper
```

### Topic Endpoints
```
GET /api/topics - Get all available topics
GET /api/topics/suggest - Get personalized topic suggestions
```

## AI Processing Pipeline

### 1. Text Extraction
- **PDF Processing**: Uses PyPDF2 to extract text from PDF files
- **DOCX Processing**: Uses python-docx for Word document text extraction
- **TXT Processing**: Direct text file reading
- **Preprocessing**: Text cleaning and normalization

### 2. Topic Extraction
- **Tokenization**: Breaking text into meaningful units
- **Stop Word Removal**: Filtering common words
- **TF-IDF Analysis**: Term frequency-inverse document frequency scoring
- **Keyword Extraction**: Identifying significant terms and phrases
- **Topic Clustering**: Grouping related terms into topics

### 3. Summarization
- **Sentence Scoring**: Ranking sentences by importance
- **Key Sentence Extraction**: Selecting most representative sentences
- **Summary Generation**: Creating concise paper abstracts
- **Length Optimization**: Ensuring appropriate summary length

### 4. Topic Suggestion
- **Similarity Analysis**: Comparing papers to topic database
- **Machine Learning Models**: Using trained models for recommendations
- **Relevance Scoring**: Calculating topic match percentages
- **Personalization**: Tailoring suggestions to user's research history

## File Structure

```
ai-research-analyzer/
├── ai_processing/           # Python AI scripts
│   ├── text_extractor.py   # Text extraction from documents
│   ├── topic_analyzer.py   # Topic extraction and analysis
│   └── openai_analyzer.py  # OpenAI integration for enhanced analysis
├── public/                 # Frontend files
│   ├── index.html          # Main HTML file
│   ├── style.css           # CSS styles
│   └── script.js           # JavaScript functionality
├── uploads/                # Temporary file storage
├── server.js               # Main server file
├── package.json            # Node.js dependencies
├── requirements.txt        # Python dependencies
├── README.md               # This documentation
└── .env                    # Environment variables (create this)
```

## Troubleshooting

### Common Issues

#### MongoDB Connection Error
```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Start MongoDB if not running
sudo systemctl start mongod

# Check MongoDB logs
sudo journalctl -u mongod
```

#### Python Dependencies Error
```bash
# Install missing packages
pip3 install PyPDF2 python-docx nltk scikit-learn

# Download NLTK data
python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

#### File Upload Issues
- Ensure the `uploads/` directory exists and is writable
- Check file size limits (default: 50MB)
- Verify supported file formats (PDF, DOCX, TXT)

#### Port Already in Use
```bash
# Find process using port 3000
sudo lsof -i :3000

# Kill the process
sudo kill -9 <PID>
```

## Development

### Adding New Features
1. **Backend**: Add routes in `server.js`
2. **AI Processing**: Create new Python scripts in `ai_processing/`
3. **Frontend**: Update HTML, CSS, and JavaScript files
4. **Database**: Define new schemas using Mongoose

### Testing
```bash
# Run basic functionality tests
npm test

# Test AI processing scripts
python3 ai_processing/test_analyzer.py
```

### Deployment
For production deployment:
1. Set `NODE_ENV=production` in environment
2. Use a process manager like PM2
3. Configure reverse proxy (nginx)
4. Set up SSL certificates
5. Use MongoDB Atlas for cloud database

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review the API documentation
- Create an issue in the repository

## Changelog

### Version 1.0.0
- Initial release with core AI analysis features
- User authentication and paper management
- Topic extraction and suggestion system
- Modern responsive web interface
- Support for PDF, DOCX, and TXT files

