# Shura Legal Frontdesk Agent

A LiveKit agent for handling legal consultation appointments in Arabic.

## The Timeout Issue

The timeout error you encountered is caused by missing environment variables required for the voice features (Azure Speech Services). The agent tries to initialize these services during startup, but without proper API keys, it hangs and eventually times out.

## Quick Fix Options

### Option 1: Test with Simplified Agent (Recommended for debugging)

Run the simplified version that doesn't require external API keys:

```bash
python test_simple.py
```

This will test the agent in text-only mode without requiring Azure Speech or other external services.

### Option 1.5: Test with Voice Features (Azure Speech Services)

If you want to test voice interaction in Arabic, use one of these files:

```bash
# Using ElevenLabs TTS (multilingual)
livekit-agents run test_simple_agent.py

# Using Azure TTS (better Arabic support)
livekit-agents run test_simple_agent_azure_tts.py
```

**Note**: You need to set up Azure Speech Services first (see Option 2 below).

### Option 2: Set Up Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Azure Speech Services Configuration
# Get these from Azure Portal: https://portal.azure.com/
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=your_azure_region_here

# Calendar Integration (Optional)
# Get this from Cal.com: https://cal.com/
CAL_API_KEY=your_cal_api_key_here
```

### Option 3: Use the Simplified Agent for Production

If you don't need voice features, use `test_simple_agent.py` instead of `frontdesk_agent.py`. This version:

- Removes Azure Speech-to-Text and Text-to-Speech
- Removes Voice Activity Detection (VAD)
- Removes Turn Detection
- Works in text-only mode
- Still has all the core functionality for appointment booking

## Running the Agent

### For Testing (Text Mode)
```bash
python test_simple.py
```

### For Production (Voice Mode)
```bash
# Make sure you have the .env file set up
python frontdesk_agent.py
```

### Using LiveKit CLI
```bash
# For the simplified version
livekit-agents run test_simple_agent.py

# For the full version (requires .env)
livekit-agents run frontdesk_agent.py
```

## Features

- **Appointment Scheduling**: Book legal consultation appointments
- **Arabic Language Support**: Full Arabic conversation support
- **Calendar Integration**: Works with Cal.com or uses fake calendar for testing
- **Client Data Collection**: Collects client information for appointments
- **Multiple Consultation Types**: Basic, Gold, and Platinum consultation packages

## Troubleshooting

### Common Issues

1. **Timeout Error**: Missing environment variables for Azure Speech Services
2. **Import Errors**: Make sure all dependencies are installed
3. **Calendar Issues**: Check if CAL_API_KEY is set correctly

### Dependencies

Install required packages:
```bash
pip install -r requirements.txt
```

### Environment Setup

1. **Azure Speech Services** (Required for voice features): 
   - Go to [Azure Portal](https://portal.azure.com/)
   - Create a Speech Service resource
   - Go to "Keys and Endpoint" section
   - Copy Key 1 and Region
   - Set in .env file:
     ```env
     AZURE_SPEECH_KEY=your_key_here
     AZURE_SPEECH_REGION=your_region_here
     ```

2. **Cal.com Integration** (Optional):
   - Sign up at cal.com
   - Get API key from settings
   - Set CAL_API_KEY in .env file

## Agent Behavior

The agent:
- Greets users in Arabic
- Collects client information
- Shows available appointment slots
- Books appointments
- Provides pricing information
- Handles consultation types (Basic, Gold, Platinum)

## Testing

Run the test suite:
```bash
pytest test_agent.py
```

Or test the simplified version:
```bash
python test_simple.py
```
