from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import json
import hashlib
import secrets
from datetime import datetime
import re
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# File-system locations for persistent storage
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
DATASETS_FILE = os.path.join(DATA_DIR, "datasets.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)


def _save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file_handle:
        json.dump(data, file_handle, ensure_ascii=False, indent=2)


def _load_json(file_path, default):
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
    except Exception:
        return default


def _hash_password(password, salt):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _ensure_default_user():
    users = _load_json(USERS_FILE, {})
    if not users:
        # Create a default admin user on first run
        salt = secrets.token_hex(8)
        users["admin"] = {
            "salt": salt,
            "password_hash": _hash_password("admin123", salt),
            "created_at": datetime.now().isoformat(),
            "role": "admin"
        }
        _save_json(USERS_FILE, users)


def _get_default_dataset():
    # Organized exactly as requested by the user
    return {
        "Crimes Against the Person (Bodily & Life Offenses)": [
            {"Crime": "Murder", "IPC Section": "302", "Punishment Severity": "Extremely Severe", "Concrete Numbers": "Death penalty or life imprisonment (with or without fine)."},
            {"Crime": "Culpable Homicide Not Amounting to Murder", "IPC Section": "304", "Punishment Severity": "Severe", "Concrete Numbers": "Imprisonment up to 10 years or life imprisonment and fine."},
            {"Crime": "Rape", "IPC Section": "376", "Punishment Severity": "Severe", "Concrete Numbers": "Rigorous imprisonment for minimum 7 years to life and fine."},
            {"Crime": "Attempt to Murder", "IPC Section": "307", "Punishment Severity": "Severe", "Concrete Numbers": "Imprisonment up to 10 years, potentially life imprisonment."},
            {"Crime": "Voluntarily Causing Grievous Hurt by Dangerous Weapon", "IPC Section": "322", "Punishment Severity": "High", "Concrete Numbers": "Imprisonment up to 10 years and fine."},
            {"Crime": "Kidnapping", "IPC Section": "363", "Punishment Severity": "Moderate to High", "Concrete Numbers": "Imprisonment up to 7 years with fine."},
            {"Crime": "Assault", "IPC Section": "351", "Punishment Severity": "Low", "Concrete Numbers": "Imprisonment up to 3 months or fine up to 500 rupees or both."},
            {"Crime": "Voluntarily Causing Hurt", "IPC Section": "321", "Punishment Severity": "Low", "Concrete Numbers": "Imprisonment up to 1 year or fine or both."}
        ],
        "Crimes Against Property": [
            {"Crime": "Robbery", "IPC Section": "392", "Punishment Severity": "High", "Concrete Numbers": "Imprisonment up to 10 years and fine."},
            {"Crime": "Cheating & Dishonestly Inducing Delivery of Property (e.g., severe cheating)", "IPC Section": "420", "Punishment Severity": "High", "Concrete Numbers": "Imprisonment up to 7 years and fine."},
            {"Crime": "Theft", "IPC Section": "379", "Punishment Severity": "Moderate", "Concrete Numbers": "Imprisonment up to 3 years or fine or both."},
            {"Crime": "Extortion", "IPC Section": "384", "Punishment Severity": "Moderate", "Concrete Numbers": "Imprisonment up to 3 years and fine."},
            {"Crime": "Mischief (Damage over 50 rupees)", "IPC Section": "427", "Punishment Severity": "Low to Moderate", "Concrete Numbers": "Imprisonment up to 2 years, or fine, or both."}
        ],
        "Crimes Related to Forgery and Counterfeiting": [
            {"Crime": "Forgery of Valuable Security", "IPC Section": "467", "Specific Act": "IPC", "Punishment Severity": "High", "Concrete Numbers": "Imprisonment up to 7 years and fine."},
            {"Crime": "Counterfeiting Currency/Selling Forged Currency", "IPC Section": "489A", "Specific Act": "IPC", "Punishment Severity": "High", "Concrete Numbers": "Imprisonment up to 7 years and fine."},
            {"Crime": "Forgery (General)", "IPC Section": "463, 465", "Specific Act": "IPC", "Punishment Severity": "Low to Moderate", "Concrete Numbers": "Imprisonment up to 2 years or fine or both."},
            {"Crime": "Counterfeiting Government Seal/Stamps", "IPC Section": "489C, 489B", "Specific Act": "IPC", "Punishment Severity": "Moderate", "Concrete Numbers": "Imprisonment up to 3 years and fine."}
        ],
        "Crimes Against Women": [
            {"Crime": "Rape", "IPC Section": "376", "Punishment Severity": "Severe", "Concrete Numbers": "Rigorous imprisonment for minimum 7 years to life and fine."},
            {"Crime": "Dowry Death", "IPC Section": "304B", "Punishment Severity": "Severe", "Concrete Numbers": "Minimum imprisonment 7 years to life."},
            {"Crime": "Cruelty by Husband or Relatives (Domestic Violence)", "IPC Section": "498A", "Punishment Severity": "Moderate", "Concrete Numbers": "Imprisonment up to 3 years and fine."},
            {"Crime": "Outraging Modesty/Assault on Woman", "IPC Section": "354", "Punishment Severity": "Moderate", "Concrete Numbers": "Imprisonment up to 2 years and fine."},
            {"Crime": "Stalking", "IPC Section": "354D", "Punishment Severity": "Moderate", "Concrete Numbers": "Imprisonment up to 3 years and fine."},
            {"Crime": "Harassment of Women at Workplace (Word/Gesture)", "IPC Section": "509", "Punishment Severity": "Moderate", "Concrete Numbers": "Imprisonment up to 3 years and fine."}
        ],
        "Public Order and Security Offenses": [
            {"Crime": "Promotion of Enmity Between Groups", "IPC Section": "153A", "Punishment Severity": "Moderate", "Concrete Numbers": "Imprisonment up to 3 years or fine or both."},
            {"Crime": "Rioting Armed with Deadly Weapon", "IPC Section": "148", "Punishment Severity": "Moderate", "Concrete Numbers": "Imprisonment up to 3 years or fine or both."},
            {"Crime": "Defiling Place of Worship", "IPC Section": "295", "Punishment Severity": "Low to Moderate", "Concrete Numbers": "Imprisonment up to 2 years or fine or both."},
            {"Crime": "Unlawful Assembly", "IPC Section": "141, 143", "Punishment Severity": "Low", "Concrete Numbers": "Imprisonment up to 6 months or fine or both."},
            {"Crime": "Disobedience to Public Servant's Order", "IPC Section": "188", "Punishment Severity": "Low", "Concrete Numbers": "Imprisonment up to 6 months or fine or both."}
        ]
    }


def _ensure_default_dataset():
    existing = _load_json(DATASETS_FILE, None)
    if existing is None:
        _save_json(DATASETS_FILE, _get_default_dataset())


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapper


# Initialize persistent data on startup
_ensure_default_user()
_ensure_default_dataset()

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
    dataset = _load_json(DATASETS_FILE, _get_default_dataset())
    return render_template("index.html", dataset=dataset, theme=session.get("theme", "light"), user=session.get("user"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        users = _load_json(USERS_FILE, {})
        user = users.get(username)
        if user:
            salt = user.get("salt", "")
            if _hash_password(password, salt) == user.get("password_hash"):
                session["user"] = {"username": username, "role": user.get("role", "user")}
                return redirect(request.args.get("next") or url_for("index"))
        flash("Invalid username or password", "error")
    return render_template("login.html", theme=session.get("theme", "light"), user=session.get("user"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@app.route("/chat", methods=["POST"])
@login_required
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
@login_required
def generate_document():
    try:
        data = request.get_json()
        document_type = data.get("type", "complaint")
        user_details = data.get("details", {})
        referenced_crime = data.get("crime")  # optional, to sync with dataset
        referenced_category = data.get("category")

        # Pull referenced dataset info if provided
        dataset = _load_json(DATASETS_FILE, _get_default_dataset())
        referenced_info = None
        if referenced_crime:
            # Search across categories
            for category_name, rows in dataset.items():
                for row in rows:
                    if row.get("Crime", "").lower() == str(referenced_crime).lower():
                        referenced_info = row
                        referenced_category = category_name
                        break
                if referenced_info:
                    break
        
        annex = ""
        if referenced_info:
            annex = (
                "\n\nANNEXURE: Referenced Crime Details\n"
                f"Category: {referenced_category}\n"
                f"Crime: {referenced_info.get('Crime', '')}\n"
                f"IPC Section: {referenced_info.get('IPC Section', '')}\n"
                f"Punishment Severity: {referenced_info.get('Punishment Severity', referenced_info.get('Specific Act', ''))}\n"
                f"Details: {referenced_info.get('Concrete Numbers', '')}"
            )

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
{annex}
        """
        
        return jsonify({
            "status": "success",
            "document": document.strip()
        })
    
    except Exception as e:
        return jsonify({"error": "Error generating document"}), 500

@app.route("/history")
@login_required
def get_history():
    return jsonify(session.get("conversation", []))

@app.route("/clear")
@login_required
def clear_history():
    session.pop("conversation", None)
    return jsonify({"status": "success"})


@app.route("/datasets", methods=["GET", "POST"])
@login_required
def datasets():
    if request.method == "GET":
        return jsonify(_load_json(DATASETS_FILE, _get_default_dataset()))

    # POST: append or replace dataset entries
    payload = request.get_json(silent=True) or {}
    mode = str(payload.get("mode", "append")).lower()
    incoming = payload.get("data")
    if not isinstance(incoming, dict):
        return jsonify({"error": "Invalid payload. Expecting { 'data': {<Category>: [rows...]}, 'mode': 'append|replace' }"}), 400

    current = _load_json(DATASETS_FILE, _get_default_dataset())
    if mode == "replace":
        _save_json(DATASETS_FILE, incoming)
    else:
        # Append by category
        for category_name, rows in incoming.items():
            current.setdefault(category_name, [])
            if isinstance(rows, list):
                current[category_name].extend(rows)
        _save_json(DATASETS_FILE, current)
    return jsonify({"status": "success"})


@app.route("/theme", methods=["POST"])
def set_theme():
    data = request.get_json(silent=True) or {}
    theme = data.get("theme", "light")
    session["theme"] = theme if theme in ("light", "dark") else "light"
    return jsonify({"status": "ok", "theme": session["theme"]})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
