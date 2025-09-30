from flask import Flask, render_template, request, jsonify, session
import json
import hashlib
import secrets
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Enhanced IPC sections database with more categories
IPC_SECTIONS = {
    # Property Related
    "theft": {
        "section": "Section 378",
        "description": "Theft is defined as dishonestly taking any movable property out of the possession of any person without that person's consent.",
        "punishment": "Imprisonment up to 3 years or fine or both",
        "category": "Property Crime"
    },
    "robbery": {
        "section": "Section 390",
        "description": "Robbery is theft or extortion committed in the presence of the person robbed, and by means of violence or fear.",
        "punishment": "Imprisonment up to 10 years and fine",
        "category": "Property Crime"
    },
    "criminal breach of trust": {
        "section": "Section 405",
        "description": "Whoever, being in any manner entrusted with property, dishonestly misappropriates or converts to his own use that property.",
        "punishment": "Imprisonment up to 3 years or fine or both",
        "category": "Property Crime"
    },
    
    # Violence Related
    "assault": {
        "section": "Section 351",
        "description": "Assault is making a gesture or preparation intending or knowing it to be likely that such gesture or preparation will cause any person present to apprehend that he who makes that gesture or preparation is about to use criminal force to him.",
        "punishment": "Imprisonment up to 3 months or fine up to Rs. 500 or both",
        "category": "Violence"
    },
    "criminal force": {
        "section": "Section 350",
        "description": "Whoever intentionally uses force to any person, without that person's consent, in order to commit an offence, or intending by the use of such force to cause, or knowing it to be likely that by the use of such force he will cause injury, fear or annoyance to the person to whom the force is used.",
        "punishment": "Imprisonment up to 3 months or fine up to Rs. 500 or both",
        "category": "Violence"
    },
    "domestic violence": {
        "section": "Section 498A",
        "description": "Husband or relative of husband of a woman subjecting her to cruelty.",
        "punishment": "Imprisonment up to 3 years and fine",
        "category": "Family Violence"
    },
    
    # Fraud and Cheating
    "fraud": {
        "section": "Section 420",
        "description": "Cheating and dishonestly inducing delivery of property.",
        "punishment": "Imprisonment up to 7 years and fine",
        "category": "Fraud"
    },
    "cheating": {
        "section": "Section 415",
        "description": "Whoever, by deceiving any person, fraudulently or dishonestly induces the person so deceived to deliver any property to any person, or to consent that any person shall retain any property.",
        "punishment": "Imprisonment up to 1 year or fine or both",
        "category": "Fraud"
    },
    
    # Cyber Crimes
    "cyber crime": {
        "section": "Section 66",
        "description": "Computer related offences under Information Technology Act.",
        "punishment": "Imprisonment up to 3 years or fine up to Rs. 5 lakh or both",
        "category": "Cyber Crime"
    },
    "online fraud": {
        "section": "Section 66C & 66D",
        "description": "Identity theft and cheating by personation using computer resource.",
        "punishment": "Imprisonment up to 3 years and fine up to Rs. 1 lakh",
        "category": "Cyber Crime"
    },
    
    # Workplace Issues
    "sexual harassment": {
        "section": "Section 354A",
        "description": "Sexual harassment and punishment for sexual harassment.",
        "punishment": "Imprisonment up to 3 years or fine or both",
        "category": "Workplace"
    },
    "wage theft": {
        "section": "Section 25F of Industrial Disputes Act",
        "description": "Non-payment of wages or salary without proper notice.",
        "punishment": "Fine up to Rs. 1000 or imprisonment up to 6 months or both",
        "category": "Workplace"
    },
    
    # Property Disputes
    "trespass": {
        "section": "Section 441",
        "description": "Whoever enters into or upon property in the possession of another with intent to commit an offence or to intimidate, insult or annoy any person in possession of such property.",
        "punishment": "Imprisonment up to 3 months or fine up to Rs. 500 or both",
        "category": "Property Dispute"
    },
    "nuisance": {
        "section": "Section 268",
        "description": "A person is guilty of a public nuisance who does any act or is guilty of an illegal omission which causes any common injury, danger or annoyance to the public.",
        "punishment": "Fine up to Rs. 200",
        "category": "Property Dispute"
    },
    
    # Road Accidents
    "rash driving": {
        "section": "Section 279",
        "description": "Whoever drives any vehicle, or rides, on any public way in a manner so rash or negligent as to endanger human life, or to be likely to cause hurt or injury to any other person.",
        "punishment": "Imprisonment up to 6 months or fine up to Rs. 1000 or both",
        "category": "Traffic"
    },
    "hit and run": {
        "section": "Section 304A",
        "description": "Whoever causes the death of any person by doing any rash or negligent act not amounting to culpable homicide.",
        "punishment": "Imprisonment up to 2 years or fine or both",
        "category": "Traffic"
    },
    
    # Defamation
    "defamation": {
        "section": "Section 499",
        "description": "Whoever, by words either spoken or intended to be read, or by signs or by visible representations, makes or publishes any imputation concerning any person intending to harm, or knowing or having reason to believe that such imputation will harm, the reputation of such person.",
        "punishment": "Imprisonment up to 2 years or fine or both",
        "category": "Defamation"
    }
}

# Enhanced precedent cases
PRECEDENT_CASES = {
    "theft": [
        {
            "case": "State of Maharashtra vs. Vishwanath",
            "year": "2019",
            "summary": "The court held that temporary deprivation of property constitutes theft even if the intention is to return it later."
        },
        {
            "case": "K.N. Mehra vs. State of Rajasthan",
            "year": "1957",
            "summary": "The Supreme Court clarified that taking property without consent, even temporarily, amounts to theft."
        }
    ],
    "assault": [
        {
            "case": "Ramesh Kumar vs. State of UP",
            "year": "2020",
            "summary": "The court clarified that mere words without any gesture or preparation do not amount to assault."
        }
    ],
    "domestic violence": [
        {
            "case": "Arnesh Kumar vs. State of Bihar",
            "year": "2014",
            "summary": "The Supreme Court laid down guidelines to prevent misuse of Section 498A and ensure fair investigation."
        }
    ],
    "fraud": [
        {
            "case": "Inder Singh vs. State of Punjab",
            "year": "2018",
            "summary": "The court held that online fraud and cheating through digital means are punishable under Section 420."
        }
    ],
    "cyber crime": [
        {
            "case": "Shreya Singhal vs. Union of India",
            "year": "2015",
            "summary": "The Supreme Court struck down Section 66A of IT Act as unconstitutional, protecting free speech online."
        }
    ]
}

class EnhancedLegalAI:
    def __init__(self):
        self.conversation_history = []
        self.keyword_mapping = {
            # Property related
            "stolen": ["theft", "robbery"],
            "stole": ["theft", "robbery"],
            "theft": ["theft"],
            "robbery": ["robbery"],
            "security deposit": ["criminal breach of trust", "fraud"],
            "landlord": ["criminal breach of trust", "fraud"],
            "property": ["theft", "trespass", "criminal breach of trust"],
            
            # Violence related
            "assault": ["assault", "criminal force"],
            "hit": ["assault", "criminal force"],
            "beat": ["assault", "criminal force"],
            "violence": ["assault", "criminal force", "domestic violence"],
            "domestic": ["domestic violence"],
            "spouse": ["domestic violence"],
            "husband": ["domestic violence"],
            "wife": ["domestic violence"],
            
            # Fraud related
            "cheated": ["fraud", "cheating"],
            "cheat": ["fraud", "cheating"],
            "fraud": ["fraud", "cheating"],
            "online": ["cyber crime", "online fraud"],
            "internet": ["cyber crime", "online fraud"],
            "social media": ["cyber crime", "defamation"],
            "rumors": ["defamation"],
            "false": ["defamation", "fraud"],
            
            # Workplace
            "salary": ["wage theft"],
            "employer": ["wage theft", "sexual harassment"],
            "workplace": ["sexual harassment", "wage theft"],
            "harassment": ["sexual harassment"],
            
            # Property disputes
            "neighbor": ["nuisance", "trespass"],
            "noise": ["nuisance"],
            "loud": ["nuisance"],
            "music": ["nuisance"],
            
            # Traffic
            "accident": ["rash driving", "hit and run"],
            "road": ["rash driving", "hit and run"],
            "car": ["rash driving", "hit and run"],
            "vehicle": ["rash driving", "hit and run"],
            
            # Defamation
            "defamation": ["defamation"],
            "reputation": ["defamation"],
            "photos": ["defamation", "cyber crime"],
            "images": ["defamation", "cyber crime"]
        }
    
    def process_query(self, user_input):
        user_input_lower = user_input.lower()
        legal_issues = []
        
        # Enhanced keyword matching with context
        for keyword, issues in self.keyword_mapping.items():
            if keyword in user_input_lower:
                legal_issues.extend(issues)
        
        # Remove duplicates while preserving order
        legal_issues = list(dict.fromkeys(legal_issues))
        
        # If no direct match, try fuzzy matching
        if not legal_issues:
            for issue in IPC_SECTIONS.keys():
                if any(word in user_input_lower for word in issue.split()):
                    legal_issues.append(issue)
        
        return legal_issues
    
    def get_legal_advice(self, user_input):
        legal_issues = self.process_query(user_input)
        
        if not legal_issues:
            return {
                "status": "unclear",
                "message": "I need more information to provide specific legal advice. Could you please describe your legal issue in more detail?",
                "suggestions": [
                    "Try rephrasing your question with more specific details",
                    "Include information about what happened, when, and where",
                    "Mention any relevant people or organizations involved",
                    "Describe the impact or consequences you're facing"
                ]
            }
        
        advice = {
            "status": "success",
            "issues_identified": legal_issues,
            "legal_sections": [],
            "precedents": [],
            "recommendations": [],
            "next_steps": []
        }
        
        for issue in legal_issues:
            if issue in IPC_SECTIONS:
                advice["legal_sections"].append(IPC_SECTIONS[issue])
            
            if issue in PRECEDENT_CASES:
                advice["precedents"].extend(PRECEDENT_CASES[issue])
        
        # Generate contextual recommendations
        advice["recommendations"] = [
            "Consult with a qualified lawyer for detailed legal advice",
            "Gather all relevant documents and evidence",
            "Document the incident with dates, times, and witnesses",
            "Consider alternative dispute resolution methods like mediation"
        ]
        
        # Generate next steps based on issue type
        if any("theft" in issue or "robbery" in issue for issue in legal_issues):
            advice["next_steps"] = [
                "File an FIR at the nearest police station immediately",
                "Preserve any evidence related to the incident",
                "Inform your insurance company if applicable",
                "Keep copies of all police reports and documents"
            ]
        elif any("domestic" in issue for issue in legal_issues):
            advice["next_steps"] = [
                "Contact local women's helpline or domestic violence support",
                "Document all incidents with dates and details",
                "Consider filing a complaint under Protection of Women from Domestic Violence Act",
                "Seek immediate help if in danger"
            ]
        elif any("cyber" in issue or "online" in issue for issue in legal_issues):
            advice["next_steps"] = [
                "Take screenshots of all relevant online content",
                "Report the incident to the cyber crime cell",
                "Change passwords and secure your accounts",
                "File a complaint with the platform where the incident occurred"
            ]
        else:
            advice["next_steps"] = [
                "Document all relevant facts and evidence",
                "Consider sending a legal notice if appropriate",
                "Explore mediation or negotiation options",
                "Prepare for potential legal proceedings"
            ]
        
        return advice

# Initialize enhanced AI system
legal_ai = EnhancedLegalAI()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        
        if not user_message:
            return jsonify({"error": "Please enter a message"}), 400
        
        advice = legal_ai.get_legal_advice(user_message)
        
        session["conversation"] = session.get("conversation", [])
        session["conversation"].append({
            "user": user_message,
            "ai": advice,
            "timestamp": datetime.now().isoformat()
        })
        
        return jsonify(advice)
    
    except Exception as e:
        return jsonify({"error": "An error occurred processing your request"}), 500

@app.route("/document", methods=["POST"])
def generate_document():
    try:
        data = request.get_json()
        document_type = data.get("type", "complaint")
        user_details = data.get("details", {})
        
        document = f"""
LEGAL DOCUMENT - {document_type.upper()}

Date: {datetime.now().strftime('%d/%m/%Y')}

To: The Honorable Court

Subject: {document_type.title()}

Dear Sir/Madam,

I, {user_details.get('name', '[Your Name]')}, residing at {user_details.get('address', '[Your Address]')}, 
hereby submit this {document_type} regarding the following matter:

{user_details.get('description', '[Description of the matter]')}

I request the court to take appropriate action in this matter.

Yours faithfully,
{user_details.get('name', '[Your Name]')}

---
This document has been generated by Personal Advocate AI for informational purposes only.
Please consult with a qualified lawyer before filing any legal documents.
        """
        
        return jsonify({
            "status": "success",
            "document": document.strip()
        })
    
    except Exception as e:
        return jsonify({"error": "Error generating document"}), 500

@app.route("/history")
def get_history():
    return jsonify(session.get("conversation", []))

@app.route("/clear")
def clear_history():
    session.pop("conversation", None)
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
