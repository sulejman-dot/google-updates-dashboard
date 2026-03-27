#!/usr/bin/env python3
"""
Trigger Intercom Response Check - Agent Invocation Script

This script is designed to be run by cron. It outputs instructions for the
Gemini agent to execute Intercom response monitoring via MCP.
"""

from datetime import datetime


def main():
    """
    Output instructions for the Gemini agent to check Intercom response times.
    """
    
    print(f"""
🤖 Intercom Response Monitor - Agent Trigger
{'='*60}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

INSTRUCTIONS FOR GEMINI AGENT:
1. Use mcp_intercom_search with query: "object_type:conversations state:open"
2. For each conversation in results, call mcp_intercom_get_conversation
3. For each conversation with full details, call:
   
   from intercom_response_monitor import load_state, save_state, check_conversation_response_time
   
   state = load_state()
   check_conversation_response_time(
       conv_data=<conversation_data>,
       state=state
   )
   save_state(state)

This will check for slow responses (15+ min) and send Slack alerts.
{'='*60}
    """)


if __name__ == "__main__":
    main()
