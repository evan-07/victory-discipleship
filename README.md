# Victory Discipleship Member Management System

> [!IMPORTANT]  
> **🤖 AI Agent Instructions**: This file contains human-readable business logic. For system design, data architecture, allowed tools, and mandatory governance rules, you MUST read **[ARCHITECTURE.md](ARCHITECTURE.md)** and **[AGENTS.md](AGENTS.md)**.

## 1. System Purpose
The Victory Discipleship Member Management System is a comprehensive platform designed to manage church member data, track discipleship progress, and handle event registrations. It is built to seamlessly support the pastoral team by providing accurate, real-time insights into the spiritual journey of every person.

---

## 2. The Discipleship Journey (Person Lifecycle)
The system tracks an individual's growth through four distinct, admin-managed stages. A person's stage is never auto-computed; it relies on pastoral judgment and confirmed milestones.

### Stage 1: Contact
* **Who they are:** Someone participating in the church but not yet an official member (e.g., a first-time guest or event registrant).
* **Requirements:** Basic contact info (Name, Address, Mobile, Birthday).
* **Next Step:** Complete One2One to become a Member.

### Stage 2: Member
* **Who they are:** Someone who has completed **One2One** and is actively part of a Victory Group.
* **Requirements:** All Contact info + Employment Details + Name of their Victory Group Leader.
* **Next Step:** Begin training as an intern while taking Equipping Classes.

### Stage 3: VG Intern
* **Who they are:** A member actively being discipled to lead their own group.
* **Requirements:** Same as Member, but they are formally linked in the system to a supervising VG Leader.
* **Next Step:** Launch and lead their own group.

### Stage 4: VG Leader
* **Who they are:** An individual actively leading one or more Victory Groups.
* **Requirements:** All previous info + specific data on the groups they lead (Group Type, Member Roster).
* **Ongoing:** Tracked in the system as the primary spiritual mentor for their group members.

---

## 3. The Equipping Pathway
The system tracks the classes and training a member undergoes. The completion logic handles both the historical ("Old") pathway and the current ("New") pathway natively, ensuring no one is left behind.

* **New Pathway (2025 - Present):**
  1. `One2One` 
  2. `Spiritual Foundations`
  3. `Leadership 113`
* **Old Pathway (Legacy):**
  1. `One2One` 
  2. `Victory Weekend`
  3. `Discipleship Class` (or Leader's Lab)
  4. `Leadership 113`

> [!TIP]
> The system automatically grants a "Fully Equipped" status when either pathway is completed. Leaders on the old pathway are gently encouraged by the system to take *Spiritual Foundations*.

---

## 4. Event Management & Registration
Events are strictly categorized into four types to ensure data cleanliness and prevent registration errors.

### 🎓 Equipping Classes
* **Examples:** Spiritual Foundations, Leadership 113.
* **Workflow:** Admin-managed rosters only. There is no public registration page for these. Administrators enroll members, and completion directly impacts the person's Equipping Pathway progress.

### 🎉 Church Events
* **Examples:** Date Talk, Convergence, Family Day.
* **Workflow:** Public self-registration via a dedicated landing page (`/e/[slug]`). The system strictly checks for duplicates to prevent double-booking. If a brand new person registers, they are entered into the system as a **Contact**.

### ⛪ Pastoral Events (Self-Register)
* **Examples:** Weddings, Child Dedications.
* **Workflow:** Families register via a pastoral form. The system automatically creates new profiles for the individuals involved if they do not exist, flagging them for pastoral follow-up.

### 🕊️ Pastoral Events (Admin-Only)
* **Examples:** Funerals.
* **Workflow:** Highly sensitive. Handled entirely by administrators. These records are hidden from standard executive reports to maintain privacy.

---

## 5. Development & Administration Quick Links

### System Access
* **Public Pages:** `/` (Member Registration) and `/e/[slug]` (Event Registration).
* **Admin Portal:** `/admin.html` (Protected via Cloudflare Access).
* **Leader Dashboard:** `/dashboard.html` (Google Sign-In required; verified against `vg_leader` role).
* **Executive Reports:** `/reports.html` (Looker Studio Dashboards).

### Developer Resources
If you are an engineer or an authorized AI agent working on this repository, please refer strictly to the following guides:
1. **[ARCHITECTURE.md](ARCHITECTURE.md)**: Master architecture plan, schema references, and hard boundaries.
2. **[AGENTS.md](AGENTS.md)**: Agent orchestration, tool authorizations, and workflows.
3. **Infrastructure**: `terraform/` (No local applies allowed; standard PR flow required).
4. **Dataform**: `data/definitions/` (Medallion architecture: Bronze -> Silver -> Gold).