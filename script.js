// Enhanced Personal Advocate AI - JavaScript Functionality
document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const chatMessages = document.getElementById('chatMessages');
    const clearChatButton = document.getElementById('clearChat');
    const generateDocButton = document.getElementById('generateDoc');
    const documentModal = document.getElementById('documentModal');
    const documentForm = document.getElementById('documentForm');
    const closeModal = document.querySelector('.close');

    // Quick question function
    window.askQuestion = function(question) {
        messageInput.value = question;
        sendMessage();
    };

    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        addMessageToChat(message, 'user');
        messageInput.value = '';

        const loadingMessage = addMessageToChat('', 'ai', true);
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            loadingMessage.remove();
            addAIResponseToChat(data);
            
        } catch (error) {
            loadingMessage.remove();
            addMessageToChat('Sorry, I encountered an error. Please try again.', 'ai');
        }
    }

    function addMessageToChat(message, sender, isLoading = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ' + sender + '-message';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'user' ? '<i class=\"fas fa-user\"></i>' : '<i class=\"fas fa-robot\"></i>';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        if (isLoading) {
            content.innerHTML = '<div class=\"loading\"></div> Processing your request...';
        } else {
            content.innerHTML = '<p>' + message + '</p>';
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageDiv;
    }

    function addAIResponseToChat(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i class=\"fas fa-robot\"></i>';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        let responseHTML = '';
        
        if (data.status === 'unclear') {
            responseHTML = '<p>' + data.message + '</p>';
            responseHTML += '<div class=\"recommendations\">';
            responseHTML += '<h4><i class=\"fas fa-lightbulb\"></i> Suggestions:</h4>';
            responseHTML += '<ul>';
            data.suggestions.forEach(function(suggestion) {
                responseHTML += '<li>' + suggestion + '</li>';
            });
            responseHTML += '</ul></div>';
        } else if (data.status === 'success') {
            responseHTML = '<p><strong> Legal Analysis Complete!</strong></p>';
            responseHTML += '<p>I have identified the following legal issues in your query:</p>';
            responseHTML += '<p><strong>Issues:</strong> ' + data.issues_identified.join(', ') + '</p>';
            
            if (data.legal_sections && data.legal_sections.length > 0) {
                responseHTML += '<h4><i class=\"fas fa-book\"></i> Relevant Legal Sections:</h4>';
                data.legal_sections.forEach(function(section) {
                    responseHTML += '<div class=\"legal-section\">';
                    responseHTML += '<h4><i class=\"fas fa-gavel\"></i> ' + section.section + ' (' + section.category + ')</h4>';
                    responseHTML += '<p><strong>Description:</strong> ' + section.description + '</p>';
                    responseHTML += '<p><strong>Punishment:</strong> ' + section.punishment + '</p>';
                    responseHTML += '</div>';
                });
            }
            
            if (data.precedents && data.precedents.length > 0) {
                responseHTML += '<h4><i class=\"fas fa-balance-scale\"></i> Relevant Case Precedents:</h4>';
                data.precedents.forEach(function(precedent) {
                    responseHTML += '<div class=\"precedent-case\">';
                    responseHTML += '<h4><i class=\"fas fa-file-alt\"></i> ' + precedent.case + ' (' + precedent.year + ')</h4>';
                    responseHTML += '<p>' + precedent.summary + '</p>';
                    responseHTML += '</div>';
                });
            }
            
            if (data.recommendations && data.recommendations.length > 0) {
                responseHTML += '<div class=\"recommendations\">';
                responseHTML += '<h4><i class=\"fas fa-check-circle\"></i> General Recommendations:</h4>';
                responseHTML += '<ul>';
                data.recommendations.forEach(function(rec) {
                    responseHTML += '<li>' + rec + '</li>';
                });
                responseHTML += '</ul></div>';
            }
            
            if (data.next_steps && data.next_steps.length > 0) {
                responseHTML += '<div class=\"recommendations\">';
                responseHTML += '<h4><i class=\"fas fa-route\"></i> Immediate Next Steps:</h4>';
                responseHTML += '<ul>';
                data.next_steps.forEach(function(step) {
                    responseHTML += '<li>' + step + '</li>';
                });
                responseHTML += '</ul></div>';
            }
            
            responseHTML += '<div class=\"recommendations\">';
            responseHTML += '<h4><i class=\"fas fa-exclamation-triangle\"></i> Important Disclaimer:</h4>';
            responseHTML += '<p>This information is for educational purposes only and should not be considered as professional legal advice. Please consult with a qualified lawyer for specific legal guidance.</p>';
            responseHTML += '</div>';
        } else {
            responseHTML = '<p>I apologize, but I could not process your request. Please try again.</p>';
        }
        
        content.innerHTML = responseHTML;
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function clearChat() {
        try {
            await fetch('/clear', { method: 'GET' });
            chatMessages.innerHTML = '<div class=\"message ai-message\"><div class=\"message-avatar\"><i class=\"fas fa-robot\"></i></div><div class=\"message-content\"><p> Welcome to your Personal Advocate AI! I am here to help you understand legal matters in simple terms. Whether you are dealing with property disputes, workplace issues, family matters, or any legal concern, just describe your situation in plain English and I will guide you through the relevant laws and your rights.</p></div></div>';
        } catch (error) {
            console.error('Error clearing chat:', error);
        }
    }

    async function generateDocument(formData) {
        try {
            const response = await fetch('/document', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                const newWindow = window.open('', '_blank');
                newWindow.document.write('<html><head><title>Generated Legal Document</title><style>body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; background: #f8f9fa; } .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); } pre { white-space: pre-wrap; background: #f5f5f5; padding: 20px; border-radius: 5px; border-left: 4px solid #667eea; } .header { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #e9ecef; } .disclaimer { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin-top: 20px; }</style></head><body><div class=\"container\"><div class=\"header\"><h1> Generated Legal Document</h1><p>Generated on ' + new Date().toLocaleDateString() + '</p></div><pre>' + data.document + '</pre><div class=\"disclaimer\"><strong> Disclaimer:</strong> This document has been generated by Personal Advocate AI for informational purposes only. Please consult with a qualified lawyer before filing any legal documents.</div><div style=\"margin-top: 30px; text-align: center;\"><button onclick=\"window.print()\" style=\"padding: 15px 30px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold;\"> Print Document</button></div></div></body></html>');
                newWindow.document.close();
                documentModal.style.display = 'none';
                documentForm.reset();
            } else {
                alert('Error generating document. Please try again.');
            }
        } catch (error) {
            console.error('Error generating document:', error);
            alert('Error generating document. Please try again.');
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    clearChatButton.addEventListener('click', clearChat);
    
    generateDocButton.addEventListener('click', function() {
        documentModal.style.display = 'block';
    });
    
    closeModal.addEventListener('click', function() {
        documentModal.style.display = 'none';
    });
    
    window.addEventListener('click', function(event) {
        if (event.target === documentModal) {
            documentModal.style.display = 'none';
        }
    });
    
    documentForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = {
            type: document.getElementById('docType').value,
            details: {
                name: document.getElementById('userName').value,
                address: document.getElementById('userAddress').value,
                description: document.getElementById('description').value
            }
        };
        
        generateDocument(formData);
    });

    async function loadHistory() {
        try {
            const response = await fetch('/history');
            const history = await response.json();
            
            if (history && history.length > 0) {
                chatMessages.innerHTML = '';
                history.forEach(function(entry) {
                    addMessageToChat(entry.user, 'user');
                    addAIResponseToChat(entry.ai);
                });
            }
        } catch (error) {
            console.error('Error loading history:', error);
        }
    }

    // Add some interactive animations
    function addInteractiveEffects() {
        // Add hover effects to question cards
        const questionCards = document.querySelectorAll('.question-card');
        questionCards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-8px) scale(1.03)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });
        
        // Add typing effect to welcome message
        const welcomeMessage = document.querySelector('.message-content p');
        if (welcomeMessage && welcomeMessage.textContent.includes('Welcome')) {
            const text = welcomeMessage.textContent;
            welcomeMessage.textContent = '';
            let i = 0;
            const typeWriter = setInterval(() => {
                if (i < text.length) {
                    welcomeMessage.textContent += text.charAt(i);
                    i++;
                } else {
                    clearInterval(typeWriter);
                }
            }, 50);
        }
    }

    // Initialize everything
    loadHistory();
    addInteractiveEffects();
});
