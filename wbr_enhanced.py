#!/usr/bin/env python3
"""
Enhanced WBR Reader - Reads all sheets and provides week-over-week comparison
"""

import gspread
from google.oauth2.service_account import Credentials
import os
import sys

SPREADSHEET_ID = "161qbyJ5nQsgDEaudZ5O1C4zldUIBbeDiYMYyCgldG40"
SERVICE_ACCOUNT_FILE = "service_account.json"

def get_wbr_data(week_offset=0):
    """
    Fetch WBR data from Google Sheets.
    
    Args:
        week_offset: 0 for current week, 1 for previous week, etc.
    
    Returns:
        Dictionary with WBR metrics from all sheets
    """
    try:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            return None
            
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SPREADSHEET_ID)
        
        # Helper function to find week in a sheet
        def find_week_row(sheet, week_name, header_rows=1):
            """Find the row number for a given week in a sheet"""
            all_values = sheet.get_all_values()
            for i in range(header_rows, len(all_values)):
                if all_values[i] and all_values[i][0] == week_name:
                    return i + 1  # Convert to 1-indexed
            return None
        
        # Find the last week with data in sheet 1 to determine current week
        sheet1 = sh.worksheet("WBR - created/auto/data #")
        all_values = sheet1.get_all_values()
        
        # Find all weeks in sheet 1
        weeks = []
        for i in range(1, len(all_values)):  # Skip header row 0
            if all_values[i] and all_values[i][0] and all_values[i][0].startswith('W'):
                weeks.append(all_values[i][0])
        
        if not weeks:
            return None
        
        # Get the target week based on offset
        if week_offset >= len(weeks):
            return None
        target_week = weeks[-(week_offset + 1)]  # Get from end of list
        
        result = {
            "week": target_week,
            "created_auto_data": {},
            "due_done": {},
            "new_kpis": {},
            "planning": {}
        }
        
        # Sheet 1: WBR - created/auto/data #
        try:
            row_num = find_week_row(sheet1, target_week, header_rows=1)
            if row_num:
                row_data = sheet1.row_values(row_num)
                if row_data:
                    result["created_auto_data"] = {
                        "total_tasks": row_data[1] if len(row_data) > 1 else "0",
                        "auto_tasks": row_data[2] if len(row_data) > 2 else "0",
                        "data_tasks": row_data[4] if len(row_data) > 4 else "0"
                    }
        except Exception as e:
            print(f"Error reading sheet 1: {e}", file=sys.stderr)
        
        # Sheet 2: WBR - due/done #
        sheet2 = sh.worksheet("WBR - due/done #")
        try:
            # Sheet 2 has empty row 1, headers in row 2, data starts at row 3
            row_num = find_week_row(sheet2, target_week, header_rows=2)
            if row_num:
                row_data = sheet2.row_values(row_num)
                if row_data:
                    result["due_done"] = {
                        "created": row_data[1] if len(row_data) > 1 else "0",
                        "auto": row_data[2] if len(row_data) > 2 else "0",
                        "data": row_data[3] if len(row_data) > 3 else "0",
                        "total_due": row_data[4] if len(row_data) > 4 else "0",
                        "total_done": row_data[5] if len(row_data) > 5 else "0"
                    }
        except Exception as e:
            print(f"Error reading sheet 2: {e}", file=sys.stderr)
        
        # Sheet 3: WBR - new kpis #
        sheet3 = sh.worksheet("WBR - new kpis #")
        try:
            row_num = find_week_row(sheet3, target_week, header_rows=1)
            if row_num:
                row_data = sheet3.row_values(row_num)
                if row_data:
                    result["new_kpis"] = {
                        "critical_over_sla": row_data[1] if len(row_data) > 1 else "0",
                        "returned": row_data[2] if len(row_data) > 2 else "0",
                        "repeating": row_data[3] if len(row_data) > 3 else "-",
                        "new_launches": row_data[4] if len(row_data) > 4 else "-"
                    }
        except Exception as e:
            print(f"Error reading sheet 3: {e}", file=sys.stderr)
        
        # Sheet 5: planning for week W - hrs
        sheet5 = sh.worksheet("planning for week W - hrs")
        try:
            row_num = find_week_row(sheet5, target_week, header_rows=2)
            if row_num:
                row_data = sheet5.row_values(row_num)
                if row_data:
                    result["planning"] = {
                        "created_est": row_data[1] if len(row_data) > 1 else "-",
                        "new_debt": row_data[2] if len(row_data) > 2 else "-",
                        "planned": row_data[3] if len(row_data) > 3 else "-",
                        "debt": row_data[4] if len(row_data) > 4 else "-"
                    }
        except Exception as e:
            print(f"Error reading sheet 5: {e}", file=sys.stderr)
        
        return result
        
    except Exception as e:
        print(f"Error fetching WBR data: {e}", file=sys.stderr)
        return None


def format_wbr_summary(data):
    """Format WBR data for Slack display"""
    if not data or not data.get("week"):
        return "❌ No WBR data available"
    
    week = data["week"]
    summary = f"📊 **Weekly Business Review - {week}**\n"
    summary += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Tasks Created/Auto/Data
    if data.get("created_auto_data"):
        cad = data["created_auto_data"]
        summary += f"📝 **Tasks Created**\n"
        summary += f"├─ Total: **{cad.get('total_tasks', '0')}**\n"
        summary += f"├─ Auto: {cad.get('auto_tasks', '0')}\n"
        summary += f"└─ Data: {cad.get('data_tasks', '0')}\n\n"
    
    # Due/Done
    if data.get("due_done"):
        dd = data["due_done"]
        summary += f"✅ **Due/Done Status**\n"
        summary += f"├─ Created: {dd.get('created', '0')}\n"
        summary += f"├─ Auto: {dd.get('auto', '0')}\n"
        summary += f"├─ Data: {dd.get('data', '0')}\n"
        summary += f"├─ Total Due: **{dd.get('total_due', '0')}** 📌\n"
        summary += f"└─ Total Done: **{dd.get('total_done', '0')}** ✓\n\n"
    
    # KPIs
    if data.get("new_kpis"):
        kpi = data["new_kpis"]
        summary += f"📈 **Key Performance Indicators**\n"
        summary += f"├─ Critical over SLA: {kpi.get('critical_over_sla', '0')} ⚠️\n"
        summary += f"└─ Returned: {kpi.get('returned', '0')} 🔄\n\n"
    
    # Planning
    if data.get("planning"):
        plan = data["planning"]
        summary += f"⏱️ **Planning (hours)**\n"
        summary += f"├─ Created (est): {plan.get('created_est', '-')}\n"
        summary += f"├─ New Debt: {plan.get('new_debt', '-')}\n"
        summary += f"├─ Planned: {plan.get('planned', '-')}\n"
        summary += f"└─ Debt: {plan.get('debt', '-')}\n\n"
    
    summary += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    return summary




def compare_weeks(current_data, previous_data):
    """Compare current week with previous week and show changes with enhanced visuals"""
    if not current_data or not previous_data:
        return "❌ Not enough data for comparison"
    
    current_week = current_data.get("week", "Current")
    previous_week = previous_data.get("week", "Previous")
    
    def safe_int(val):
        """Safely convert to int"""
        try:
            return int(val) if val and val != '-' else 0
        except:
            return 0
    
    def safe_float(val):
        """Safely convert to float"""
        try:
            return float(val) if val and val != '-' else 0
        except:
            return 0
    
    def get_change(current, previous):
        """Calculate change and return formatted string with visual indicators"""
        curr = safe_int(current)
        prev = safe_int(previous)
        if prev == 0 and curr == 0:
            return f"**{curr}** ➡️"
        if prev == 0:
            return f"**{curr}** 🆕"
        
        change = curr - prev
        percent = (change / prev) * 100
        
        # Enhanced visual indicators based on magnitude
        if change > 0:
            symbol = "🔥" if percent > 50 else "📈" if percent > 20 else "↗️"
        elif change < 0:
            symbol = "⚠️" if percent < -50 else "📉" if percent < -20 else "↘️"
        else:
            symbol = "➡️"
        
        return f"**{curr}** ({change:+d}, {percent:+.1f}%) {symbol}"
    
    def get_change_float(current, previous):
        """Calculate change for float values"""
        curr = safe_float(current)
        prev = safe_float(previous)
        if prev == 0 and curr == 0:
            return f"**{curr:.1f}** ➡️"
        if prev == 0:
            return f"**{curr:.1f}** 🆕"
        
        change = curr - prev
        percent = (change / prev) * 100
        symbol = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        return f"**{curr:.1f}** ({change:+.1f}, {percent:+.1f}%) {symbol}"
    
    # Calculate key metrics for highlights
    curr_cad = current_data.get("created_auto_data", {})
    prev_cad = previous_data.get("created_auto_data", {})
    curr_dd = current_data.get("due_done", {})
    prev_dd = previous_data.get("due_done", {})
    curr_kpi = current_data.get("new_kpis", {})
    prev_kpi = previous_data.get("new_kpis", {})
    curr_plan = current_data.get("planning", {})
    prev_plan = previous_data.get("planning", {})
    
    total_curr = safe_int(curr_cad.get('total_tasks'))
    total_prev = safe_int(prev_cad.get('total_tasks'))
    due_curr = safe_int(curr_dd.get('total_due'))
    done_curr = safe_int(curr_dd.get('total_done'))
    done_prev = safe_int(prev_dd.get('total_done'))
    debt_curr = safe_float(curr_plan.get('debt'))
    debt_prev = safe_float(prev_plan.get('debt'))
    critical_curr = safe_int(curr_kpi.get('critical_over_sla'))
    critical_prev = safe_int(prev_kpi.get('critical_over_sla'))
    
    # Calculate completion rate
    completion_rate = (done_curr / due_curr * 100) if due_curr > 0 else 0
    completion_prev = (done_prev / safe_int(prev_dd.get('total_due')) * 100) if safe_int(prev_dd.get('total_due')) > 0 else 0
    
    # Build summary with executive highlights
    summary = f"📊 **WBR Comparison: {current_week} vs {previous_week}**\n"
    summary += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # === EXECUTIVE SUMMARY ===
    summary += "⭐ **Week Highlights**\n"
    
    # Task volume change
    task_change = total_curr - total_prev
    task_pct = (task_change / total_prev * 100) if total_prev > 0 else 0
    if task_change > 0:
        summary += f"• Task volume UP by {task_change} ({task_pct:+.1f}%) → **{total_curr} tasks** 📈\n"
    elif task_change < 0:
        summary += f"• Task volume DOWN by {abs(task_change)} ({task_pct:.1f}%) → **{total_curr} tasks** 📉\n"
    else:
        summary += f"• Task volume STEADY at **{total_curr} tasks** ➡️\n"
    
    # Completion performance
    completion_change = completion_rate - completion_prev
    if completion_rate >= 100:
        summary += f"• **{completion_rate:.0f}% completion rate** 🎯 ALL TASKS DONE!\n"
    elif completion_rate >= 80:
        summary += f"• Strong completion: **{completion_rate:.0f}%** ({completion_change:+.1f}% vs last week) ✅\n"
    elif completion_rate >= 60:
        summary += f"• Moderate completion: **{completion_rate:.0f}%** ({completion_change:+.1f}% vs last week) 🟡\n"
    else:
        summary += f"• Low completion: **{completion_rate:.0f}%** ({completion_change:+.1f}% vs last week) 🔴\n"
    
    # Debt trend
    debt_change = debt_curr - debt_prev
    if debt_change < 0:
        summary += f"• Debt REDUCED by **{abs(debt_change):.1f}hrs** → Now at {debt_curr:.1f}hrs 🎉\n"
    elif debt_change > 0:
        summary += f"• Debt INCREASED by **{debt_change:.1f}hrs** → Now at {debt_curr:.1f}hrs ⚠️\n"
    else:
        summary += f"• Debt STABLE at **{debt_curr:.1f}hrs** ➡️\n"
    
    # Critical tickets alert
    if critical_curr > critical_prev:
        summary += f"• ⚠️ Critical over SLA UP: **{critical_curr}** (+{critical_curr - critical_prev}) - NEEDS ATTENTION\n"
    elif critical_curr > 0:
        summary += f"• ⚠️ **{critical_curr}** tickets still critical over SLA\n"
    else:
        summary += f"• ✅ NO critical tickets over SLA!\n"
    
    summary += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # === DETAILED BREAKDOWN ===
    summary += "📝 **Tasks Created**\n"
    summary += f"├─ Total: {get_change(curr_cad.get('total_tasks'), prev_cad.get('total_tasks'))}\n"
    summary += f"├─ Auto: {get_change(curr_cad.get('auto_tasks'), prev_cad.get('auto_tasks'))}\n"
    summary += f"└─ Data: {get_change(curr_cad.get('data_tasks'), prev_cad.get('data_tasks'))}\n\n"
    
    # Due/Done with completion rate
    summary += "✅ **Due/Done Status**\n"
    summary += f"├─ Created: {get_change(curr_dd.get('created'), prev_dd.get('created'))}\n"
    summary += f"├─ Auto: {get_change(curr_dd.get('auto'), prev_dd.get('auto'))}\n"
    summary += f"├─ Data: {get_change(curr_dd.get('data'), prev_dd.get('data'))}\n"
    summary += f"├─ Total Due: {get_change(curr_dd.get('total_due'), prev_dd.get('total_due'))}\n"
    summary += f"├─ Total Done: {get_change(curr_dd.get('total_done'), prev_dd.get('total_done'))}\n"
    summary += f"└─ Completion: **{completion_rate:.0f}%** ({completion_change:+.1f}%) "
    summary += "🎯" if completion_rate >= 80 else "🟡" if completion_rate >= 60 else "🔴"
    summary += "\n\n"
    
    # KPIs with visual alerts
    summary += "📊 **Key Performance Indicators**\n"
    summary += f"├─ Critical over SLA: {get_change(curr_kpi.get('critical_over_sla'), prev_kpi.get('critical_over_sla'))}"
    if critical_curr > 3:
        summary += " ⚠️ HIGH"
    summary += "\n"
    summary += f"├─ Returned: {get_change(curr_kpi.get('returned'), prev_kpi.get('returned'))}\n"
    
    repeating_curr = curr_kpi.get('repeating', '-')
    repeating_prev = prev_kpi.get('repeating', '-')
    if repeating_curr != '-' or repeating_prev != '-':
        summary += f"├─ Repeating: {get_change(repeating_curr, repeating_prev)}\n"
    
    launches_curr = curr_kpi.get('new_launches', '-')
    launches_prev = prev_kpi.get('new_launches', '-')
    if launches_curr != '-' or launches_prev != '-':
        summary += f"└─ New Launches: {get_change(launches_curr, launches_prev)}\n"
    else:
        summary = summary.rsplit("├─", 1)
        summary = "└─".join(summary)
    
    summary += "\n"
    
    # Planning with insights
    has_planning = any(v and v != '-' for v in [
        curr_plan.get('created_est'), curr_plan.get('planned'), 
        curr_plan.get('debt'), prev_plan.get('created_est'),
        prev_plan.get('planned'), prev_plan.get('debt')
    ])
    
    if has_planning:
        summary += "⏱️ **Planning & Capacity (hours)**\n"
        summary += f"├─ Created (est): {get_change_float(curr_plan.get('created_est'), prev_plan.get('created_est'))}\n"
        
        new_debt_curr = curr_plan.get('new_debt', '-')
        new_debt_prev = prev_plan.get('new_debt', '-')
        if new_debt_curr != '-' or new_debt_prev != '-':
            summary += f"├─ New Debt: {get_change_float(new_debt_curr, new_debt_prev)}\n"
        
        summary += f"├─ Planned: {get_change_float(curr_plan.get('planned'), prev_plan.get('planned'))}\n"
        summary += f"└─ Debt: {get_change_float(curr_plan.get('debt'), prev_plan.get('debt'))}"
        
        if debt_change < -5:
            summary += " 🎉 GREAT!"
        elif debt_change > 5:
            summary += " ⚠️ GROWING"
        summary += "\n\n"
    
    summary += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    return summary




if __name__ == "__main__":
    import json
    
    # Get current week data
    current = get_wbr_data(week_offset=0)
    
    if current:
        print("📊 Current Week WBR Data:")
        print(format_wbr_summary(current))
        print("\n" + "="*50 + "\n")
        
        # Get previous week data and compare
        previous = get_wbr_data(week_offset=1)
        if previous:
            print(compare_weeks(current, previous))
    else:
        print("❌ Could not fetch WBR data. Check credentials and permissions.")
