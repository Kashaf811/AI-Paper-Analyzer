// AI Research Paper Analyzer - Frontend JavaScript

// Global variables
let currentUser = null;
let authToken = null;
let selectedFile = null;
let currentPaperId = null;

// DOM elements
const paperInput = document.getElementById('paperInput');
const uploadArea = document.getElementById('uploadArea');
const paperPreview = document.getElementById('paperPreview');
const analyzeBtn = document.getElementById('analyzeBtn');
const loading = document.getElementById('loading');
const resultSection = document.getElementById('resultSection');
const alertContainer = document.getElementById('alertContainer');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    checkAuthStatus();
    // Google Sign-In button event
    const googleBtn = document.getElementById('googleSignInBtn');
    if (googleBtn) {
        googleBtn.addEventListener('click', function() {
            window.location.href = '/auth/google';
        });
    }
});

function initializeApp() {
    // Check for stored auth token
    authToken = localStorage.getItem('authToken');
    if (authToken) {
        fetchUserProfile();
    }
    
    // Load initial data
    loadTopics();
}

function setupEventListeners() {
    // File upload
    uploadArea.addEventListener('click', () => paperInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('drop', handleDrop);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    paperInput.addEventListener('change', handleFileSelect);
    
    // Analyze button
    analyzeBtn.addEventListener('click', analyzePaper);
    
    // Navigation
    document.getElementById('analyzeAnotherBtn')?.addEventListener('click', resetForm);
    
    // Auth forms
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('signupForm').addEventListener('submit', handleSignup);
    
    // Paper modal
    document.getElementById('deletePaperBtn')?.addEventListener('click', deletePaper);
}

// File handling
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    // Validate file type
    const allowedTypes = ['.pdf', '.docx', '.txt', '.doc'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExt)) {
        showAlert('Please select a PDF, DOCX, or TXT file.', 'danger');
        return;
    }
    
    // Validate file size (50MB limit)
    if (file.size > 50 * 1024 * 1024) {
        showAlert('File size must be less than 50MB.', 'danger');
        return;
    }
    
    selectedFile = file;
    displayFilePreview(file);
    analyzeBtn.disabled = false;
}

function displayFilePreview(file) {
    document.getElementById('paperFileName').textContent = file.name;
    document.getElementById('paperFileSize').textContent = formatFileSize(file.size);
    paperPreview.style.display = 'block';
    paperPreview.classList.add('fade-in');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Paper analysis
async function analyzePaper() {
    if (!selectedFile) {
        showAlert('Please select a file first.', 'danger');
        return;
    }
    
    if (!authToken) {
        showAlert('Please login to analyze papers.', 'warning');
        document.querySelector('[data-bs-target="#loginModal"]').click();
        return;
    }
    
    const formData = new FormData();
    formData.append('paper', selectedFile);
    
    const title = document.getElementById('paperTitle').value.trim();
    const authors = document.getElementById('paperAuthors').value.trim();
    
    if (title) formData.append('title', title);
    if (authors) formData.append('authors', authors);
    
    try {
        // Show loading
        loading.style.display = 'block';
        analyzeBtn.disabled = true;
        
        const response = await fetch('/api/papers/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            currentPaperId = result.paperId;
            showAlert('Paper uploaded successfully! Analysis in progress...', 'success');
            
            // Poll for analysis completion
            pollAnalysisStatus(result.paperId);
        } else {
            throw new Error(result.error || 'Upload failed');
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        showAlert('Error analyzing paper: ' + error.message, 'danger');
        loading.style.display = 'none';
        analyzeBtn.disabled = false;
    }
}

async function pollAnalysisStatus(paperId) {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;
    
    const poll = async () => {
        try {
            const response = await fetch(`/api/papers/${paperId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            
            const paper = await response.json();
            
            if (paper.status === 'analyzed') {
                // Analysis complete, fetch results
                await displayAnalysisResults(paperId);
                loading.style.display = 'none';
                analyzeBtn.disabled = false;
            } else if (paper.status === 'failed') {
                throw new Error('Analysis failed');
            } else if (attempts < maxAttempts) {
                // Continue polling
                attempts++;
                setTimeout(poll, 5000); // Poll every 5 seconds
            } else {
                throw new Error('Analysis timeout');
            }
            
        } catch (error) {
            console.error('Polling error:', error);
            showAlert('Error checking analysis status: ' + error.message, 'danger');
            loading.style.display = 'none';
            analyzeBtn.disabled = false;
        }
    };
    
    poll();
}

async function displayAnalysisResults(paperId) {
    try {
        const response = await fetch(`/api/papers/${paperId}/analysis`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const analysis = await response.json();
        
        if (response.ok) {
            // Display summary
            document.getElementById('paperSummary').textContent = analysis.summary || 'No summary available.';
            
            // Display extracted topics
            displayTopics(analysis.extractedTopics || [], 'extractedTopics', 'extracted');
            
            // Display suggested topics
            displaySuggestedTopics(analysis.suggestedTopics || [], 'suggestedTopics');
            
            // Display research areas if available
            if (analysis.suggestedAreas && analysis.suggestedAreas.length > 0) {
                displayResearchAreas(analysis.suggestedAreas, 'researchAreas');
                document.getElementById('researchAreasSection').style.display = 'block';
            }
            
            // Show results section
            resultSection.style.display = 'block';
            resultSection.classList.add('slide-up');
            
            // Scroll to results
            resultSection.scrollIntoView({ behavior: 'smooth' });
            
            // Refresh papers list
            loadUserPapers();
            
        } else {
            throw new Error(analysis.error || 'Failed to load analysis results');
        }
        
    } catch (error) {
        console.error('Error displaying results:', error);
        showAlert('Error loading analysis results: ' + error.message, 'danger');
    }
}

function displayTopics(topics, containerId, className = '') {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    if (topics.length === 0) {
        container.innerHTML = '<p class="text-muted">No topics found.</p>';
        return;
    }
    
    topics.forEach(topic => {
        const topicElement = document.createElement('div');
        topicElement.className = `topic-tag ${className}`;
        
        const score = topic.relevanceScore || topic.suggestionScore || 0;
        const scoreText = (score * 100).toFixed(0) + '%';
        
        topicElement.innerHTML = `
            <span>${topic.topic || topic.topicName}</span>
            <span class="relevance-score">${scoreText}</span>
        `;
        
        container.appendChild(topicElement);
    });
}

function displaySuggestedTopics(topics, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    if (topics.length === 0) {
        container.innerHTML = '<p class="text-muted">No topic suggestions available.</p>';
        return;
    }
    
    topics.forEach(topic => {
        const topicElement = document.createElement('div');
        topicElement.className = 'topic-tag suggested';
        
        const score = (topic.suggestionScore * 100).toFixed(0) + '%';
        
        topicElement.innerHTML = `
            <span>${topic.topicName}</span>
            <span class="relevance-score">${score}</span>
        `;
        
        container.appendChild(topicElement);
    });
}

function displayResearchAreas(areas, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    areas.forEach(area => {
        const areaElement = document.createElement('div');
        areaElement.className = 'research-area';
        areaElement.innerHTML = `
            <h6>${area.area}</h6>
            <p>${area.reasoning}</p>
        `;
        container.appendChild(areaElement);
    });
}

// User management
async function handleLogin(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const loginData = {
        email: formData.get('email'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(loginData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            authToken = result.token;
            currentUser = result.user;
            localStorage.setItem('authToken', authToken);
            
            updateAuthUI();
            bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
            showAlert('Login successful!', 'success');
            
            // Load user data
            loadUserPapers();
            loadPersonalizedTopics();
            
        } else {
            throw new Error(result.error || 'Login failed');
        }
        
    } catch (error) {
        showAlert('Login error: ' + error.message, 'danger');
    }
}

async function handleSignup(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const signupData = {
        name: formData.get('name'),
        email: formData.get('email'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(signupData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            authToken = result.token;
            currentUser = result.user;
            localStorage.setItem('authToken', authToken);
            
            updateAuthUI();
            bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
            showAlert('Account created successfully!', 'success');
            
        } else {
            throw new Error(result.error || 'Signup failed');
        }
        
    } catch (error) {
        showAlert('Signup error: ' + error.message, 'danger');
    }
}

async function fetchUserProfile() {
    try {
        const response = await fetch('/api/profile', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            currentUser = result.user;
            updateAuthUI();
            loadUserPapers();
            loadPersonalizedTopics();
        } else {
            // Token invalid, clear it
            logout();
        }
        
    } catch (error) {
        console.error('Error fetching profile:', error);
        logout();
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    updateAuthUI();
    // Clear user-specific data
    document.getElementById('papersGrid').innerHTML = '';
    document.getElementById('personalizedTopics').innerHTML = '';
    // Also log out from Google session (optional, triggers backend logout)
    fetch('/auth/logout').then(() => {
        showAlert('Logged out successfully.', 'info');
    });
}

function updateAuthUI() {
    const authNav = document.getElementById('authNav');
    const userNav = document.getElementById('userNav');
    const userName = document.getElementById('userName');
    
    if (currentUser) {
        authNav.style.display = 'none';
        userNav.style.display = 'block';
        userName.textContent = currentUser.name;
    } else {
        authNav.style.display = 'block';
        userNav.style.display = 'none';
    }
}

function checkAuthStatus() {
    updateAuthUI();
}

// Data loading
async function loadUserPapers() {
    if (!authToken) return;
    
    try {
        const response = await fetch('/api/papers', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const papers = await response.json();
        
        if (response.ok) {
            displayPapers(papers);
        } else {
            console.error('Error loading papers:', papers.error);
        }
        
    } catch (error) {
        console.error('Error loading papers:', error);
    }
}

function displayPapers(papers) {
    const container = document.getElementById('papersGrid');
    const noMessage = document.getElementById('noPapersMessage');
    
    if (papers.length === 0) {
        container.innerHTML = '';
        noMessage.style.display = 'block';
        return;
    }
    
    noMessage.style.display = 'none';
    container.innerHTML = '';
    
    papers.forEach(paper => {
        const paperCard = document.createElement('div');
        paperCard.className = 'paper-card';
        paperCard.onclick = () => showPaperDetails(paper);
        
        const statusClass = `status-${paper.status}`;
        const uploadDate = new Date(paper.uploadDate).toLocaleDateString();
        
        paperCard.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-2">
                <h6 class="mb-0">${paper.title}</h6>
                <span class="paper-status ${statusClass}">${paper.status}</span>
            </div>
            <p class="text-muted mb-2">${paper.authors.join(', ') || 'No authors specified'}</p>
            <small class="text-secondary">Uploaded: ${uploadDate}</small>
        `;
        
        container.appendChild(paperCard);
    });
}

async function loadTopics() {
    try {
        const response = await fetch('/api/topics');
        const topics = await response.json();
        
        if (response.ok) {
            displayAllTopics(topics);
        } else {
            console.error('Error loading topics:', topics.error);
        }
        
    } catch (error) {
        console.error('Error loading topics:', error);
    }
}

function displayAllTopics(topics) {
    const container = document.getElementById('allTopics');
    container.innerHTML = '';
    
    topics.forEach(topic => {
        const topicItem = document.createElement('div');
        topicItem.className = 'topic-item';
        topicItem.innerHTML = `
            <h6>${topic.name}</h6>
            <p>${topic.description || 'No description available'}</p>
        `;
        container.appendChild(topicItem);
    });
}

async function loadPersonalizedTopics() {
    if (!authToken) return;
    
    try {
        const response = await fetch('/api/topics/suggest', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const suggestions = await response.json();
        
        if (response.ok) {
            displayPersonalizedTopics(suggestions);
        } else {
            console.error('Error loading personalized topics:', suggestions.error);
        }
        
    } catch (error) {
        console.error('Error loading personalized topics:', error);
    }
}

function displayPersonalizedTopics(suggestions) {
    const container = document.getElementById('personalizedTopics');
    
    if (suggestions.length === 0) {
        container.innerHTML = '<p class="text-muted">Upload and analyze papers to get personalized topic suggestions.</p>';
        return;
    }
    
    container.innerHTML = '';
    
    suggestions.forEach(suggestion => {
        const topicItem = document.createElement('div');
        topicItem.className = 'topic-item';
        
        const score = (suggestion.averageScore * 100).toFixed(0);
        
        topicItem.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <h6>${suggestion.topicName}</h6>
                <small class="text-primary">${score}% match</small>
            </div>
            <p class="mb-0">Based on ${suggestion.paperCount} paper(s)</p>
        `;
        container.appendChild(topicItem);
    });
}

// Paper details modal
function showPaperDetails(paper) {
    const modal = new bootstrap.Modal(document.getElementById('paperModal'));
    const detailsContainer = document.getElementById('paperDetails');
    const deleteBtn = document.getElementById('deletePaperBtn');
    
    // Store current paper ID for deletion
    deleteBtn.dataset.paperId = paper._id;
    
    const uploadDate = new Date(paper.uploadDate).toLocaleDateString();
    const statusClass = `status-${paper.status}`;
    
    let analysisHtml = '';
    if (paper.analysisResultId) {
        const analysis = paper.analysisResultId;
        analysisHtml = `
            <div class="mt-3">
                <h6>Analysis Summary:</h6>
                <p class="text-muted">${analysis.summary || 'No summary available'}</p>
                
                <h6>Extracted Topics:</h6>
                <div class="d-flex flex-wrap gap-2 mb-2">
                    ${analysis.extractedTopics.map(topic => 
                        `<span class="badge bg-info">${topic.topic}</span>`
                    ).join('')}
                </div>
                
                <h6>Suggested Topics:</h6>
                <div class="d-flex flex-wrap gap-2">
                    ${analysis.suggestedTopics.map(topic => 
                        `<span class="badge bg-warning">${topic.topicName}</span>`
                    ).join('')}
                </div>
            </div>
        `;
    }
    
    detailsContainer.innerHTML = `
        <div class="paper-details">
            <div class="d-flex justify-content-between align-items-start mb-3">
                <h5>${paper.title}</h5>
                <span class="paper-status ${statusClass}">${paper.status}</span>
            </div>
            
            <div class="row mb-3">
                <div class="col-sm-4"><strong>Authors:</strong></div>
                <div class="col-sm-8">${paper.authors.join(', ') || 'Not specified'}</div>
            </div>
            
            <div class="row mb-3">
                <div class="col-sm-4"><strong>Upload Date:</strong></div>
                <div class="col-sm-8">${uploadDate}</div>
            </div>
            
            <div class="row mb-3">
                <div class="col-sm-4"><strong>File:</strong></div>
                <div class="col-sm-8">${paper.filename}</div>
            </div>
            
            ${analysisHtml}
        </div>
    `;
    
    modal.show();
}

async function deletePaper() {
    const paperId = document.getElementById('deletePaperBtn').dataset.paperId;
    
    if (!confirm('Are you sure you want to delete this paper? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/papers/${paperId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('Paper deleted successfully.', 'success');
            bootstrap.Modal.getInstance(document.getElementById('paperModal')).hide();
            loadUserPapers();
        } else {
            throw new Error(result.error || 'Delete failed');
        }
        
    } catch (error) {
        showAlert('Error deleting paper: ' + error.message, 'danger');
    }
}

// Utility functions
function resetForm() {
    selectedFile = null;
    currentPaperId = null;
    paperInput.value = '';
    paperPreview.style.display = 'none';
    resultSection.style.display = 'none';
    analyzeBtn.disabled = true;
    
    document.getElementById('paperTitle').value = '';
    document.getElementById('paperAuthors').value = '';
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

