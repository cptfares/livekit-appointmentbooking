#!/usr/bin/env python3
"""
Simple test script to verify the agent works without external dependencies.
This script tests the agent in a text-only mode without requiring Azure Speech or other external services.
"""

import asyncio
import sys
import os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from livekit.agents import AgentSession
from livekit.plugins import openai
from calendar_api import FakeCalendar, AvailableSlot
from test_simple_agent import SimpleShuraLegalAgent, ClientData

async def test_agent():
    """Test the agent with a simple conversation."""
    
    # Set up timezone
    timezone = "Asia/Riyadh"
    tz = ZoneInfo(timezone)
    today = datetime.now(tz).date()
    
    # Create some test slots
    slots = [
        AvailableSlot(start_time=datetime.combine(today, time(9, 0), tzinfo=tz), duration_min=30),
        AvailableSlot(start_time=datetime.combine(today, time(9, 30), tzinfo=tz), duration_min=30),
        AvailableSlot(start_time=datetime.combine(today + timedelta(days=1), time(14, 0), tzinfo=tz), duration_min=30),
        AvailableSlot(start_time=datetime.combine(today + timedelta(days=1), time(14, 30), tzinfo=tz), duration_min=30),
    ]
    
    # Create calendar and userdata
    cal = FakeCalendar(timezone=timezone, slots=slots)
    await cal.initialize()
    userdata = ClientData(cal=cal)
    
    print("🤖 Testing Shura Legal Agent (Text Mode)")
    print("=" * 50)
    
    try:
        # Create LLM and session
        async with openai.LLM(model="gpt-4o", parallel_tool_calls=False, temperature=0.45) as llm:
            async with AgentSession(llm=llm, userdata=userdata) as session:
                await session.start(SimpleShuraLegalAgent(timezone=timezone))
                
                # Test conversation
                print("\n👤 User: السلام عليكم")
                result = await session.run(user_input="السلام عليكم")
                
                # Print agent response
                for event in result.events:
                    if hasattr(event, 'content') and event.content:
                        print(f"🤖 Agent: {event.content}")
                
                print("\n👤 User: أريد موعد استشارة قانونية")
                result = await session.run(user_input="أريد موعد استشارة قانونية")
                
                # Print agent response
                for event in result.events:
                    if hasattr(event, 'content') and event.content:
                        print(f"🤖 Agent: {event.content}")
                
                print("\n✅ Test completed successfully!")
                
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
