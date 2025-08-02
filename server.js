const express = require('express');
const mongoose = require('mongoose');
const multer = require('multer');
const path = require('path');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { spawn } = require('child_process');
const fs = require('fs');
const session = require('express-session');
const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(cors());
app.use('/uploads', express.static('uploads'));
app.use('/processed', express.static('processed'));
app.use(express.static('public'));

// Session middleware (required for Passport)
app.use(session({
    secret: 'your-session-secret',
    resave: false,
    saveUninitialized: false
}));

// Initialize Passport
app.use(passport.initialize());
app.use(passport.session());

// MongoDB connection
mongoose.connect('mongodb://localhost:27017/ai_research_analyzer', {
    useNewUrlParser: true,
    useUnifiedTopology: true
});

// User Schema
const userSchema = new mongoose.Schema({
    name: { type: String, required: true },
    email: { type: String, required: true, unique: true },
    password: { type: String },
    googleId: { type: String },
    createdAt: { type: Date, default: Date.now }
});
// Passport Google OAuth Strategy
passport.use(new GoogleStrategy({
    clientID: '513727892633-klv86vhh73cj022bi8dd1jcv6i4spp9c.apps.googleusercontent.com',
    clientSecret: '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',
    callbackURL: '/auth/google/callback',
}, async (accessToken, refreshToken, profile, done) => {
    try {
        let user = await User.findOne({ googleId: profile.id });
        if (!user) {
            // If user with this Google ID doesn't exist, create one
            user = new User({
                name: profile.displayName,
                email: profile.emails[0].value,
                googleId: profile.id
            });
            await user.save();
        }
        return done(null, user);
    } catch (err) {
        return done(err, null);
    }
}));

passport.serializeUser((user, done) => {
    done(null, user.id);
});

passport.deserializeUser(async (id, done) => {
    try {
        const user = await User.findById(id);
        done(null, user);
    } catch (err) {
        done(err, null);
    }
});

// Google OAuth Routes
app.get('/auth/google', passport.authenticate('google', { scope: ['profile', 'email'] }));

app.get('/auth/google/callback', passport.authenticate('google', {
    failureRedirect: '/?error=google_auth_failed',
    session: true
}), (req, res) => {
    // Successful authentication, redirect to frontend or send token
    res.redirect('/?google_auth=success');
});

// Logout route
app.get('/auth/logout', (req, res) => {
    req.logout(() => {
        res.redirect('/');
    });
});

// Paper Schema
const paperSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    title: { type: String, required: true },
    authors: [{ type: String }],
    abstract: { type: String },
    filePath: { type: String, required: true },
    extractedTextPath: { type: String },
    uploadDate: { type: Date, default: Date.now },
    status: { type: String, enum: ['uploaded', 'processing', 'analyzed', 'failed'], default: 'uploaded' },
    analysisResultId: { type: mongoose.Schema.Types.ObjectId, ref: 'AnalysisResult' },
    associatedTopics: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Topic' }],
    filename: { type: String, required: true }
});

// Topic Schema
const topicSchema = new mongoose.Schema({
    name: { type: String, required: true, unique: true },
    description: { type: String },
    paperCount: { type: Number, default: 0 }
});

// Analysis Result Schema
const analysisResultSchema = new mongoose.Schema({
    paperId: { type: mongoose.Schema.Types.ObjectId, ref: 'Paper', required: true },
    summary: { type: String },
    extractedTopics: [{
        topic: { type: String },
        relevanceScore: { type: Number },
        keywords: [{ type: String }]
    }],
    suggestedTopics: [{
        topicId: { type: mongoose.Schema.Types.ObjectId, ref: 'Topic' },
        topicName: { type: String },
        suggestionScore: { type: Number }
    }],
    suggestedAreas: [{
        area: { type: String },
        reasoning: { type: String }
    }],
    analysisDate: { type: Date, default: Date.now },
    analyzedWith: { type: String, default: 'Local' }
});

const User = mongoose.model('User', userSchema);
const Paper = mongoose.model('Paper', paperSchema);
const Topic = mongoose.model('Topic', topicSchema);
const AnalysisResult = mongoose.model('AnalysisResult', analysisResultSchema);

// Create directories if they don't exist
const createDirectories = () => {
    const dirs = ['uploads', 'processed', 'public', 'extracted_texts', 'analysis_results'];
    dirs.forEach(dir => {
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
    });
};
createDirectories();

// Initialize default topics
const initializeDefaultTopics = async () => {
    try {
        const topicCount = await Topic.countDocuments();
        if (topicCount === 0) {
            const defaultTopics = [
                { name: 'Machine Learning', description: 'Algorithms and models that learn from data' },
                { name: 'Natural Language Processing', description: 'Processing and understanding human language' },
                { name: 'Computer Vision', description: 'Enabling computers to interpret visual information' },
                { name: 'Deep Learning', description: 'Neural networks with multiple layers' },
                { name: 'Artificial Intelligence', description: 'Creating intelligent machines and systems' },
                { name: 'Data Mining', description: 'Extracting patterns from large datasets' },
                { name: 'Robotics', description: 'Design and operation of robots' },
                { name: 'Human-Computer Interaction', description: 'Study of interaction between humans and computers' },
                { name: 'Cybersecurity', description: 'Protection of digital systems and data' },
                { name: 'Software Engineering', description: 'Systematic approach to software development' },
                { name: 'Database Systems', description: 'Storage, retrieval, and management of data' },
                { name: 'Distributed Systems', description: 'Systems with components on networked computers' },
                { name: 'Algorithms', description: 'Step-by-step procedures for calculations and data processing' },
                { name: 'Bioinformatics', description: 'Application of computational methods to biological data' },
                { name: 'Quantum Computing', description: 'Computing using quantum-mechanical phenomena' }
            ];
            
            await Topic.insertMany(defaultTopics);
            console.log('Default topics initialized');
        }
    } catch (error) {
        console.error('Error initializing default topics:', error);
    }
};

// Initialize topics on startup
initializeDefaultTopics();

// Multer configuration for file uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, 'uploads/');
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, uniqueSuffix + path.extname(file.originalname));
    }
});

const upload = multer({ 
    storage: storage,
    limits: { fileSize: 50 * 1024 * 1024 }, // 50MB limit for documents
    fileFilter: (req, file, cb) => {
        const allowedTypes = ['.pdf', '.docx', '.txt', '.doc'];
        const fileExt = path.extname(file.originalname).toLowerCase();
        
        if (allowedTypes.includes(fileExt)) {
            cb(null, true);
        } else {
            cb(new Error('Only PDF, DOCX, and TXT files are allowed!'), false);
        }
    }
});

// JWT middleware
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({ error: 'Access token required' });
    }
    
    jwt.verify(token, 'your-secret-key', (err, user) => {
        if (err) {
            return res.status(403).json({ error: 'Invalid token' });
        }
        req.user = user;
        next();
    });
};

// Routes

// User Registration
app.post('/api/register', async (req, res) => {
    try {
        const { name, email, password } = req.body;
        
        const existingUser = await User.findOne({ email });
        if (existingUser) {
            return res.status(400).json({ error: 'User already exists' });
        }
        
        const hashedPassword = await bcrypt.hash(password, 10);
        
        const user = new User({
            name,
            email,
            password: hashedPassword
        });
        
        await user.save();
        
        const token = jwt.sign(
            { userId: user._id, email: user.email },
            'your-secret-key',
            { expiresIn: '7d' }
        );
        
        res.status(201).json({
            message: 'User created successfully',
            token,
            user: { id: user._id, name: user.name, email: user.email }
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// User Login
app.post('/api/login', async (req, res) => {
    try {
        const { email, password } = req.body;
        
        const user = await User.findOne({ email });
        if (!user) {
            return res.status(400).json({ error: 'Invalid credentials' });
        }
        
        const isValidPassword = await bcrypt.compare(password, user.password);
        if (!isValidPassword) {
            return res.status(400).json({ error: 'Invalid credentials' });
        }
        
        const token = jwt.sign(
            { userId: user._id, email: user.email },
            'your-secret-key',
            { expiresIn: '7d' }
        );
        
        res.json({
            message: 'Login successful',
            token,
            user: { id: user._id, name: user.name, email: user.email }
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Upload and process research paper
app.post('/api/papers/upload', authenticateToken, upload.single('paper'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No paper file provided' });
        }
        
        const { title, authors } = req.body;
        const filePath = req.file.path;
        const filename = req.file.filename;
        
        // Create paper record
        const paperRecord = new Paper({
            userId: req.user.userId,
            title: title || req.file.originalname,
            authors: authors ? authors.split(',').map(a => a.trim()) : [],
            filePath,
            filename,
            status: 'uploaded'
        });
        
        await paperRecord.save();
        
        // Start text extraction and analysis
        const extractedTextPath = `extracted_texts/${filename}.txt`;
        const analysisResultPath = `analysis_results/${filename}.json`;
        
        // Update paper with paths
        paperRecord.extractedTextPath = extractedTextPath;
        paperRecord.status = 'processing';
        await paperRecord.save();
        
        // Extract text from document
        const extractProcess = spawn('python3', [
            'ai_processing/text_extractor.py',
            filePath,
            extractedTextPath
        ]);
        
        let extractOutput = '';
        let extractError = '';
        
        extractProcess.stdout.on('data', (data) => {
            extractOutput += data.toString();
        });
        
        extractProcess.stderr.on('data', (data) => {
            extractError += data.toString();
        });
        
        extractProcess.on('close', async (code) => {
            if (code === 0) {
                console.log('Text extraction successful');
                
                // Get predefined topics for analysis
                const topics = await Topic.find({});
                const topicsPath = `analysis_results/topics_${Date.now()}.json`;
                fs.writeFileSync(topicsPath, JSON.stringify(topics, null, 2));
                
                // Analyze the extracted text
                const analyzeProcess = spawn('python3', [
                    'ai_processing/openai_analyzer.py',
                    extractedTextPath,
                    analysisResultPath,
                    topicsPath
                ]);
                
                let analyzeOutput = '';
                let analyzeError = '';
                
                analyzeProcess.stdout.on('data', (data) => {
                    analyzeOutput += data.toString();
                });
                
                analyzeProcess.stderr.on('data', (data) => {
                    analyzeError += data.toString();
                });
                
                analyzeProcess.on('close', async (analyzeCode) => {
                    try {
                        if (analyzeCode === 0 && fs.existsSync(analysisResultPath)) {
                            // Read analysis results
                            const analysisData = JSON.parse(fs.readFileSync(analysisResultPath, 'utf8'));
                            
                            // Create analysis result record
                            const analysisResult = new AnalysisResult({
                                paperId: paperRecord._id,
                                summary: analysisData.summary,
                                extractedTopics: analysisData.extractedTopics,
                                suggestedTopics: analysisData.suggestedTopics,
                                suggestedAreas: analysisData.suggestedAreas || [],
                                analyzedWith: analysisData.analyzedWith || 'Local'
                            });
                            
                            await analysisResult.save();
                            
                            // Update paper status
                            paperRecord.status = 'analyzed';
                            paperRecord.analysisResultId = analysisResult._id;
                            await paperRecord.save();
                            
                            console.log('Analysis completed successfully');
                        } else {
                            console.error('Analysis failed:', analyzeError);
                            paperRecord.status = 'failed';
                            await paperRecord.save();
                        }
                        
                        // Clean up temporary files
                        try {
                            if (fs.existsSync(topicsPath)) {
                                fs.unlinkSync(topicsPath);
                            }
                        } catch (cleanupError) {
                            console.error('Cleanup error:', cleanupError);
                        }
                        
                    } catch (error) {
                        console.error('Error processing analysis results:', error);
                        paperRecord.status = 'failed';
                        await paperRecord.save();
                    }
                });
                
            } else {
                console.error('Text extraction failed:', extractError);
                paperRecord.status = 'failed';
                await paperRecord.save();
            }
        });
        
        res.json({
            message: 'Paper uploaded successfully and processing started',
            paperId: paperRecord._id,
            status: 'processing'
        });
        
    } catch (error) {
        console.error('Upload error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Get user's papers
app.get('/api/papers', authenticateToken, async (req, res) => {
    try {
        const papers = await Paper.find({ userId: req.user.userId })
            .populate('analysisResultId')
            .sort({ uploadDate: -1 });
        
        res.json(papers);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get specific paper details
app.get('/api/papers/:id', authenticateToken, async (req, res) => {
    try {
        const paper = await Paper.findOne({ 
            _id: req.params.id, 
            userId: req.user.userId 
        }).populate('analysisResultId');
        
        if (!paper) {
            return res.status(404).json({ error: 'Paper not found' });
        }
        
        res.json(paper);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get paper analysis results
app.get('/api/papers/:id/analysis', authenticateToken, async (req, res) => {
    try {
        const paper = await Paper.findOne({ 
            _id: req.params.id, 
            userId: req.user.userId 
        });
        
        if (!paper) {
            return res.status(404).json({ error: 'Paper not found' });
        }
        
        const analysisResult = await AnalysisResult.findOne({ paperId: paper._id });
        
        if (!analysisResult) {
            return res.status(404).json({ error: 'Analysis not found' });
        }
        
        res.json(analysisResult);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get all topics
app.get('/api/topics', async (req, res) => {
    try {
        const topics = await Topic.find({}).sort({ paperCount: -1, name: 1 });
        res.json(topics);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get topic suggestions for a user
app.get('/api/topics/suggest', authenticateToken, async (req, res) => {
    try {
        // Get user's analyzed papers
        const papers = await Paper.find({ 
            userId: req.user.userId, 
            status: 'analyzed' 
        }).populate('analysisResultId');
        
        if (papers.length === 0) {
            return res.json([]);
        }
        
        // Collect all suggested topics from user's papers
        const allSuggestions = [];
        
        papers.forEach(paper => {
            if (paper.analysisResultId && paper.analysisResultId.suggestedTopics) {
                allSuggestions.push(...paper.analysisResultId.suggestedTopics);
            }
        });
        
        // Aggregate suggestions by topic
        const topicScores = {};
        allSuggestions.forEach(suggestion => {
            const topicName = suggestion.topicName;
            if (!topicScores[topicName]) {
                topicScores[topicName] = {
                    topicName,
                    totalScore: 0,
                    count: 0
                };
            }
            topicScores[topicName].totalScore += suggestion.suggestionScore;
            topicScores[topicName].count += 1;
        });
        
        // Calculate average scores and sort
        const suggestions = Object.values(topicScores)
            .map(topic => ({
                topicName: topic.topicName,
                averageScore: topic.totalScore / topic.count,
                paperCount: topic.count
            }))
            .sort((a, b) => b.averageScore - a.averageScore)
            .slice(0, 10);
        
        res.json(suggestions);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Delete paper
app.delete('/api/papers/:id', authenticateToken, async (req, res) => {
    try {
        const paper = await Paper.findOne({ 
            _id: req.params.id, 
            userId: req.user.userId 
        });
        
        if (!paper) {
            return res.status(404).json({ error: 'Paper not found' });
        }
        
        // Delete associated files
        try {
            if (fs.existsSync(paper.filePath)) {
                fs.unlinkSync(paper.filePath);
            }
            if (paper.extractedTextPath && fs.existsSync(paper.extractedTextPath)) {
                fs.unlinkSync(paper.extractedTextPath);
            }
        } catch (fileError) {
            console.error('Error deleting files:', fileError);
        }
        
        // Delete analysis result
        if (paper.analysisResultId) {
            await AnalysisResult.findByIdAndDelete(paper.analysisResultId);
        }
        
        // Delete paper record
        await Paper.findByIdAndDelete(req.params.id);
        
        res.json({ message: 'Paper deleted successfully' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get user profile
app.get('/api/profile', authenticateToken, async (req, res) => {
    try {
        const user = await User.findById(req.user.userId).select('name email');
        if (!user) return res.status(404).json({ error: 'User not found' });
        res.json({ user: { id: user._id, name: user.name, email: user.email } });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Serve the main page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`AI Research Paper Analyzer running on http://localhost:${PORT}`);
    console.log('Make sure MongoDB is running on localhost:27017');
    console.log('Make sure Python dependencies are installed');
});

