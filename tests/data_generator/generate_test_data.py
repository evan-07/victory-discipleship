# Purpose: Generate complex, relationally linked test cases for the Member Data Form.
# Usage: python3 tests/data_generator/generate_test_data.py
# Version: 1.1
# Last Modified: 2026-02-15

import json
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

# Configuration
NUM_LEADERS = 20   # "X count of victory group leaders"
NUM_MEMBERS = 60  # Pool of members to assign to leaders and use as interns

# Constants based on Frontend HTML
INDUSTRIES = [
    "Accounting / Finance", "Agriculture", "Arts / Entertainment", "BPO / IT Services",
    "Construction / Engineering", "Education", "Food & Beverage", "Government",
    "Health / Medical", "Hotel / Tourism", "Manufacturing", "Media", "Real Estate",
    "Retail / Sales", "Services", "Transportation", "Utilities"
]

VG_TYPES = ["Students", "Single Men", "Single Women", "Couples", "Husbands", "Wives", "Seniors"]
MINISTRIES = ["Kids Church", "Multimedia", "Prayer", "Safety", "Stage Mgmt", "Technical", "Ushering", "Worship"]
DISCIPLESHIP_STAGES = ["One2One", "Victory Weekend", "Discipleship Class / Leader's Lab", "Leadership L113", "Spiritual Foundations"]

def generate_base_profile(overrides=None):
    """Generates the common fields for any user, with optional overrides."""
    if overrides is None:
        overrides = {}

    gender = overrides.get("gender", random.choice(["Male", "Female"]))
    first_name = overrides.get("firstName", fake.first_name_male() if gender == "Male" else fake.first_name_female())
    last_name = overrides.get("lastName", fake.last_name())
    
    # Logic for Marital Status
    marital_status = overrides.get("maritalStatus", random.choice(["Single", "Married", "Solo Parent", "Widow/Widower"]))
    anniversary = ""
    if marital_status == "Married":
        ann_date = fake.date_between(start_date='-30y', end_date='-1y')
        anniversary = ann_date.strftime("%m/%d/%Y")

    # Logic for Occupation
    occ_type = overrides.get("occupationType", random.choice(["Student", "Professional", "Business Owner", "N/A"]))
    
    # Email Logic: firstname.lastname@example.com (simplified)
    # Removing spaces and special chars for email
    safe_first = first_name.lower().replace(" ", "")
    safe_last = last_name.lower().replace(" ", "")
    email_address = f"{safe_first}.{safe_last}@{fake.free_email_domain()}"

    profile = {
        "firstName": first_name,
        "middleName": fake.first_name(),
        "lastName": last_name,
        "suffix": random.choice(["", "", "", "Jr.", "Sr.", "III"]),
        "email": email_address,
        "fbName": f"{first_name} {last_name}",
        "primaryMobile": "09" + str(fake.random_number(digits=9, fix_len=True)), 
        "secondaryMobile": "09" + str(fake.random_number(digits=9, fix_len=True)) if random.choice([True, False]) else "",
        "gender": gender,
        "birthday": fake.date_of_birth(minimum_age=15, maximum_age=70).strftime("%m/%d/%Y"),
        "maritalStatus": marital_status,
        "anniversary": anniversary,
        "occupationType": occ_type,
        
        # Education (if Student)
        "educationLevel": random.choice(["K-12", "College"]) if occ_type == "Student" else "",
        "school": fake.company() + " University" if occ_type == "Student" else "",
        "yearLevel": str(random.randint(1, 4)) if occ_type == "Student" else "",
        "course": fake.job() if occ_type == "Student" else "",
        
        # Professional (if Professional)
        "jobTitle": fake.job() if occ_type == "Professional" else "",
        "company": fake.company() if occ_type == "Professional" else "",
        "employerIndustry": "",
        "employerIndustryOther": "",
        
        # Business (if Business Owner)
        "businessName": fake.company() if occ_type == "Business Owner" else "",
        "businessNature": "",
        "businessNatureOther": "",
        "businessAddress": fake.address() if occ_type == "Business Owner" else "",

        # Discipleship (Progressive Logic)
        "discipleship": generate_discipleship_string(),
        
        # Ministry
        "isMinistryMember": overrides.get("isMinistryMember", "No"),
        "ministry": overrides.get("ministry", "None"),
        "wantMinistry": overrides.get("wantMinistry", "")
    }

    # Handle Professional Industry
    if occ_type == "Professional":
        # Override takes precedence if provided, otherwise random
        ind = overrides.get("employerIndustry", random.choice(INDUSTRIES + ["Other"]))
        profile["employerIndustry"] = ind
        if ind == "Other":
             profile["employerIndustryOther"] = fake.bs()

    # Handle Business Nature
    if occ_type == "Business Owner":
        nat = overrides.get("businessNature", random.choice(INDUSTRIES + ["Other"]))
        profile["businessNature"] = nat
        if nat == "Other":
            profile["businessNatureOther"] = fake.bs()
    
    # Handle Ministry Logic (if not overridden)
    # If overrides handled isMinistryMember, we assume ministry/wantMinistry are also set or don't matter,
    # but the base function logic below is 'random if not set'.
    # To respect overrides fully, we only randomize if 'isMinistryMember' wasn't passed in overrides.
    if "isMinistryMember" not in overrides:
        if random.choice([True, False]):
            profile["isMinistryMember"] = "Yes"
            m_list = random.sample(MINISTRIES, k=random.randint(1, 2))
            profile["ministry"] = ", ".join(m_list)
            profile["wantMinistry"] = ""
        else:
            profile["isMinistryMember"] = "No"
            profile["ministry"] = "None"
            if random.choice([True, False]):
                m_list = random.sample(MINISTRIES, k=random.randint(1, 2))
                profile["wantMinistry"] = ", ".join(m_list)
            else:
                profile["wantMinistry"] = "None, I'll pray for it"

    # Apply any other direct overrides that might match keys (like wantVg, isLeader, etc.)
    for k, v in overrides.items():
        if k in ["firstName", "lastName", "gender", "maritalStatus", "occupationType", "isMinistryMember", "ministry", "wantMinistry", "employerIndustry", "businessNature"]:
            continue # Already handled or special logic
        profile[k] = v

    return profile

def generate_discipleship_string():
    """Generates a valid discipleship string respecting prerequisites."""
    count = random.randint(0, 5)
    if count == 0: return ""
    
    valid_path = ["One2One"]
    if count > 1: valid_path.append("Victory Weekend")
    if count > 2: valid_path.append("Spiritual Foundations")
    if count > 3: valid_path.append("Discipleship Class / Leader's Lab")
    if count > 4: valid_path.append("Leadership L113")
    
    return ", ".join(valid_path)

def main():
    test_cases = []
    
    # ---------------------------------------------------------
    # STEP 0: Seed Personas (Edge Cases)
    # ---------------------------------------------------------
    personas = []
    
    # Persona 1 (The Student Observer)
    personas.append(generate_base_profile({
        "occupationType": "Student",
        "maritalStatus": "Single",
        "isMember": "No",
        "wantVg": "Yes",
        "isMinistryMember": "No",
        "wantMinistry": "Kids Church"
    }))

    # Persona 2 (The Professional Leader)
    personas.append(generate_base_profile({
        "occupationType": "Professional",
        "employerIndustry": "Other",
        "maritalStatus": "Married",
        "isLeader": "Yes",
        "hasIntern": "No",
        "isMinistryMember": "Yes",
        "ministry": "Worship"
    }))

    # Persona 3 (The Business Owner Leader)
    personas.append(generate_base_profile({
        "occupationType": "Business Owner",
        "businessNature": "Other",
        "maritalStatus": "Solo Parent",
        "isLeader": "Yes",
        "hasIntern": "Yes", # Will need intern name logic later
        "isMinistryMember": "No",
        "wantMinistry": "None, I'll pray for it"
    }))

    # Persona 4 (The Retired Member)
    personas.append(generate_base_profile({
        "occupationType": "N/A",
        "maritalStatus": "Widow/Widower",
        "isMember": "Yes",
        "isMinistryMember": "No",
        "wantMinistry": "Prayer"
    }))

    # Persona 5 (The Skeptic)
    personas.append(generate_base_profile({
        "occupationType": "Professional",
        "maritalStatus": "Single",
        "isMember": "No",
        "wantVg": "No",
        "isMinistryMember": "No",
        "wantMinistry": "None, I'll pray for it"
    }))
    
    # Separation into Leaders and Members pool from Personas + Randoms
    leaders_pool = []
    members_pool = []

    # Process Personas first
    for p in personas:
        # Defaults if not set in persona
        if "isLeader" not in p: p["isLeader"] = "No"
        if "isMember" not in p: p["isMember"] = "Yes" # Default to yes unless specified No
        if "leaderName" not in p: p["leaderName"] = "" 
        if "vgDetails" not in p: p["vgDetails"] = ""
        if "groupCount" not in p: p["groupCount"] = ""

        if p["isLeader"] == "Yes":
           # Ensure leader fields
           if not p["vgDetails"]:
                p["groupCount"] = str(random.randint(1, 3))
                groups = []
                for _ in range(int(p["groupCount"])):
                    g_type = random.choice(VG_TYPES)
                    g_count = random.randint(3, 12)
                    groups.append(f"{g_type} ({g_count})")
                p["vgDetails"] = ", ".join(groups)
           p["leaderName"] = "Pastor " + fake.last_name()
           leaders_pool.append(p)
        else:
           members_pool.append(p)
           if p["isMember"] == "No": 
               p["leaderName"] = "" # No leader if not member
           # If member, leader will be assigned in Step 2 logic but let's just add to pool for now

    # ---------------------------------------------------------
    # STEP 1: Fill remaining Leaders
    # ---------------------------------------------------------
    needed_leaders = NUM_LEADERS - len(leaders_pool)
    for _ in range(needed_leaders):
        p = generate_base_profile()
        p["isLeader"] = "Yes"
        p["groupCount"] = str(random.randint(1, 3))
        
        groups = []
        for _ in range(int(p["groupCount"])):
             g_type = random.choice(VG_TYPES)
             g_count = random.randint(3, 12)
             groups.append(f"{g_type} ({g_count})")
        p["vgDetails"] = ", ".join(groups)
        p["hasIntern"] = "No" 
        p["internNames"] = ""
        p["isMember"] = "Yes"
        p["leaderName"] = "Pastor " + fake.last_name()
        
        leaders_pool.append(p)

    # ---------------------------------------------------------
    # STEP 2: Fill remaining Members
    # ---------------------------------------------------------
    needed_members = NUM_MEMBERS - len(members_pool)
    for _ in range(needed_members):
        p = generate_base_profile()
        p["isLeader"] = "No"
        p["vgDetails"] = ""
        p["hasIntern"] = "No"
        p["internNames"] = ""
        p["isMember"] = "Yes"
        p["leaderName"] = ""
        # Leader assigned below
        members_pool.append(p)

    # Assign Leaders to Members (who are members)
    for p in members_pool:
        if p["isMember"] == "Yes" and not p["leaderName"]:
             assigned_leader = random.choice(leaders_pool)
             p["leaderName"] = f"{assigned_leader['firstName']} {assigned_leader['lastName']}"
             p["wantVg"] = ""
        elif p["isMember"] == "No":
             p["leaderName"] = ""
             # wantVg already set in persona or defaults to null/random in base?
             # Base doesn't set wantVg if isMember is No logic explicitly, let's fix
             if "wantVg" not in p or not p["wantVg"]:
                  p["wantVg"] = random.choice(["Yes", "No"])


    # ---------------------------------------------------------
    # STEP 3: Assign Interns to Leaders (from Member pool)
    # ---------------------------------------------------------
    # Only for leaders who don't already have interns set (or update them)
    # Persona 3 has hasIntern=Yes but no names yet.
    
    # Filter members valid for internship (usually those who are members)
    valid_interns = [m for m in members_pool if m["isMember"] == "Yes"]

    for leader in leaders_pool:
        should_have_intern = leader.get("hasIntern") == "Yes"
        
        # If randomly decided or enforced by persona
        if should_have_intern or (leader.get("hasIntern") != "No" and random.choice([True, False])):
            leader["hasIntern"] = "Yes"
            if not leader.get("internNames") and valid_interns:
                 num_interns = random.randint(1, 2)
                 # Sample with replacement if pool is small, or just min
                 k = min(num_interns, len(valid_interns))
                 interns = random.sample(valid_interns, k=k)
                 intern_names_list = [f"{i['firstName']} {i['lastName']}" for i in interns]
                 leader["internNames"] = ", ".join(intern_names_list)
        else:
            leader["hasIntern"] = "No"
            leader["internNames"] = ""

    # Combine all
    all_profiles = []
    all_profiles.extend(leaders_pool)
    all_profiles.extend(members_pool)

    # Convert to Raw Schema format
    raw_records = []
    for profile in all_profiles:
        record = {
            "ingestion_timestamp": datetime.utcnow().isoformat(),
            "payload": profile,
            "metadata": {
                "ip_address": fake.ipv4(),
                "user_agent": fake.user_agent(),
                "origin": "http://localhost:test",
                "referer": "http://localhost:test/form"
            }
        }
        raw_records.append(record)

    with open('test_cases.json', 'w') as f:
        json.dump(raw_records, f, indent=2)

    print(f"Successfully generated {len(raw_records)} raw records in 'test_cases.json'.")
    print(f"- Leaders: {len(leaders_pool)}")
    print(f"- Members: {len(members_pool)}")
    print(f"- Personas included: {len(personas)}")

if __name__ == "__main__":
    main()
