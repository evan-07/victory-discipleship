# Looker Studio Reporting Guide

This guide outlines how to visualize the data from the **Gold Layer** tables in Looker Studio. Use these recommended chart types, dimensions, and metrics to build insightful dashboards.

---

## 1. Executive Overview (Source: `rept_executive_kpis` or `rept_daily_trends`)

**Goal:** High-level snapshot of church health. 

| Chart Type | Dimension | Metric | Insight |
| :--- | :--- | :--- | :--- |
| **Scorecard** | None | `MAX(total_members_to_date)` | Total Membership Count |
| **Scorecard** | None | `MAX(total_vg_members_to_date)` | Total Active in Small Groups |
| **Scorecard** | None | `MAX(total_leaders_to_date)` | Total Leadership Strength |
| **Time Series** | `report_date` | `new_signups` | Weekly/Monthly Growth Trend |

---

## 2. Demographic Analysis (Source: `rept_unified_member_profile`)

**Goal:** Understand who your members are.

| Chart Type | Dimension | Metric | Insight |
| :--- | :--- | :--- | :--- |
| **Donut Chart** | `gender` | `COUNT(email)` | Gender Ratio (Aim for varying targets) |
| **Bar Chart** | `age_group` | `COUNT(email)` | Age Distribution (Youth vs Adult vs Senior) |
| **Bar Chart** | `marital_status` | `COUNT(email)` | Family Life Stage Breakdown |
| **Tree Map** | `School_Normalized` | `COUNT(email)` | Top Campuses (Filter: `occupation_type` = Student) |
| **Tree Map** | `Industry` | `COUNT(email)` | Top Industries (Filter: `occupation_type` = Professional) |

---

## 3. Discipleship Pipeline (Source: `rept_discipleship_funnel`)

**Goal:** Identify bottlenecks in the discipleship process.

| Chart Type | Dimension | Metric | Insight |
| :--- | :--- | :--- | :--- |
| **Funnel Chart** | `stage` | `SUM(count)` | Conversion rates between steps. *Sort by `step_order`* |
| **Bar Chart** | `stage` | `SUM(count)` | Absolute numbers at each stage. |

**Key Metric Calculation in Looker:**
- **Conversion Rate**: `(Finished Victory Weekend / Total Members) * 100`

---

## 4. Small Group Health (Source: `rept_unified_member_profile`)

**Goal:** Analyze Victory Group participation and leadership capacity.

| Chart Type | Dimension | Metric | Insight |
| :--- | :--- | :--- | :--- |
| **Pie Chart** | `vg_status` | `COUNT(email)` | % Active vs % Interested vs % None |
| **Bar Chart** | `leader_group_type` | `COUNT(email)` | Types of groups available (e.g., Singles, Couples) |
| **Scatter Plot** | `leader_group_type` | X: `leader_group_size`, Y: `COUNT(Leader)` | Avg size of each group type |
| **Table** | `vg_leader_name` | `COUNT(email)` | List of Leaders and their current member count |

---

## 5. Engagement Segmentation (Source: `rept_engagement_score`)

**Goal:** Identify core leaders vs. the crowd.

| Chart Type | Dimension | Metric | Insight |
| :--- | :--- | :--- | :--- |
| **Pie Chart** | `engagement_level` | `COUNT(email)` | **Core** (High impact) vs **Crowd** (Potential growth) |
| **Table** | `first_name`, `last_name` | `engagement_score` | identify top potential leaders (High score but not yet leader) |

---

## Tips for Looker Studio:
1.  **Cross-Filtering**: Enable "Cross-filtering" on all charts. This allows you to click "Youth" on one chart and see the Discipleship Funnel update for *just* the Youth.
2.  **Date Range Control**: Add a date range control at the top right to filter all Time Series charts.
3.  **Calculated Fields**: Create a field `Is_Student` (`CASE WHEN occupation_type = 'Student' THEN 'Yes' ELSE 'No' END`) for easy toggling.
