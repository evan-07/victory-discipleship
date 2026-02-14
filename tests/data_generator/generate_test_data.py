# Purpose: Generate complex, relationally linked test cases for the Member Data Form.
# Usage: python3 tests/data_generator/generate_test_data.py
# Version: 1.0
# Last Modified: 2026-02-13

import json
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

# Configuration
NUM_LEADERS = 5   # "X count of victory group leaders"
NUM_MEMBERS = 15  # Pool of members to assign to leaders and use as interns

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

def generate_base_profile():
    """Generates the common fields for any user."""
    gender = random.choice(["Male", "Female"])
    first_name = fake.first_name_male() if gender == "Male" else fake.first_name_female()
    last_name = fake.last_name()
    
    # Logic for Marital Status
    marital_status = random.choice(["Single", "Married", "Solo Parent", "Widow/Widower"])
    anniversary = ""
    if marital_status == "Married":
        ann_date = fake.date_between(start_date='-30y', end_date='-1y')
        anniversary = ann_date.strftime("%m/%d/%Y")

    # Logic for Occupation
    occ_type = random.choice(["Student", "Professional", "Business Owner", "N/A"])
    
    profile = {
        "firstName": first_name,
        "middleName": fake.first_name(), # Simple random middle name
        "lastName": last_name,
        "suffix": random.choice(["", "", "", "Jr.", "Sr.", "III"]),
        "email": fake.email(),
        "fbName": f"{first_name} {last_name}",
        # Frontend adds '09', input is 9 digits. We simulate the final API payload here
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
        "employerIndustry": random.choice(INDUSTRIES) if occ_type == "Professional" else "",
        
        # Business (if Business Owner)
        "businessName": fake.company() if occ_type == "Business Owner" else "",
        "businessNature": random.choice(INDUSTRIES) if occ_type == "Business Owner" else "",
        "businessAddress": fake.address() if occ_type == "Business Owner" else "",

        # Discipleship (Progressive Logic)
        "discipleship": generate_discipleship_string(),
        
        # Ministry
        "isMinistryMember": "No", # Default, updated later
        "ministry": "None",
        "wantMinistry": ""
    }
    
    # Handle Ministry Logic
    if random.choice([True, False]):
        profile["isMinistryMember"] = "Yes"
        # Pick 1 or 2 ministries
        m_list = random.sample(MINISTRIES, k=random.randint(1, 2))
        profile["ministry"] = ", ".join(m_list)
    else:
        # Want ministry?
        if random.choice([True, False]):
            m_list = random.sample(MINISTRIES, k=random.randint(1, 2))
            profile["wantMinistry"] = ", ".join(m_list)
        else:
            profile["wantMinistry"] = "None, I'll pray for it"

    return profile

def generate_discipleship_string():
    """Generates a valid discipleship string respecting prerequisites."""
    # Logic: 0 classes, just 1, 1+2, etc.
    count = random.randint(0, 5)
    if count == 0: return ""
    
    # Based on evaluateDiscipleship in JS
    valid_path = ["One2One"]
    if count > 1: valid_path.append("Victory Weekend")
    if count > 2: valid_path.append("Spiritual Foundations") # Available after VW
    if count > 3: valid_path.append("Discipleship Class / Leader's Lab") # Available after VW
    if count > 4: valid_path.append("Leadership L113") # Available after DC/LL
    
    return ", ".join(valid_path)

def main():
    test_cases = []
    
    # ---------------------------------------------------------
    # STEP 1: Seed X count of Victory Group Leaders
    # ---------------------------------------------------------
    leaders_pool = []
    for _ in range(NUM_LEADERS):
        p = generate_base_profile()
        
        # Leader Specifics
        p["isLeader"] = "Yes"
        p["groupCount"] = str(random.randint(1, 3))
        
        # Generate Group Details string
        groups = []
        for _ in range(int(p["groupCount"])):
            g_type = random.choice(VG_TYPES)
            g_count = random.randint(3, 12)
            groups.append(f"{g_type} ({g_count})")
        p["vgDetails"] = ", ".join(groups)
        
        # Initialize Intern fields (populated in Step 3)
        p["hasIntern"] = "No" 
        p["internNames"] = ""
        
        # Leaders are usually members too (Reporting to a higher leader), 
        # but for this logic, we keep their "Member" status optional or self-contained.
        # Let's assume Leaders report to a generic "Pastor" for simplicity unless specified.
        p["isMember"] = "Yes"
        p["leaderName"] = "Pastor " + fake.last_name()
        
        leaders_pool.append(p)

    # ---------------------------------------------------------
    # STEP 2: Seed Members linked to Leaders
    # ---------------------------------------------------------
    members_pool = []
    for _ in range(NUM_MEMBERS):
        p = generate_base_profile()
        
        p["isLeader"] = "No"
        p["vgDetails"] = ""
        p["hasIntern"] = "No"
        p["internNames"] = ""
        
        # CONSTRAINT: Seeded leaders in Step 1 should be their Leader
        p["isMember"] = "Yes"
        assigned_leader = random.choice(leaders_pool)
        
        # Map leader name as requested
        p["leaderName"] = f"{assigned_leader['firstName']} {assigned_leader['lastName']}"
        p["wantVg"] = "" # N/A since isMember is Yes

        members_pool.append(p)

    # ---------------------------------------------------------
    # STEP 3: Assign Interns to Leaders (from Member pool)
    # ---------------------------------------------------------
    for leader in leaders_pool:
        # Randomly decide if leader has intern
        if random.choice([True, False]):
            leader["hasIntern"] = "Yes"
            
            # CONSTRAINT: Interns names should be from the 2nd stem (members_pool)
            # Pick 1 or 2 unique members to be interns
            num_interns = random.randint(1, 2)
            interns = random.sample(members_pool, k=num_interns)
            
            # Create comma-separated string of names
            intern_names_list = [f"{i['firstName']} {i['lastName']}" for i in interns]
            leader["internNames"] = ", ".join(intern_names_list)
        else:
            leader["hasIntern"] = "No"
            leader["internNames"] = ""

    # Combine all for final processing
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

    # Write to file
    with open('test_cases.json', 'w') as f:
        json.dump(raw_records, f, indent=2)

    print(f"Successfully generated {len(raw_records)} raw records in 'test_cases.json'.")
    print(f"- Leaders: {len(leaders_pool)}")
    print(f"- Members: {len(members_pool)}")

if __name__ == "__main__":
    main()
