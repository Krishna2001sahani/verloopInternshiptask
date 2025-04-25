# Chat & Agent Metrics Report Generator

## Overview
A Streamlit application that processes customer support chat data and generates comprehensive metrics reports. The app takes an Excel file containing chat data and produces a downloadable report with detailed analytics on chat volume, agent performance, and time utilization.

## Features

### Core Reports
- **Chat Metrics**: Analyze overall chat volume and bot efficiency
  - Incoming chat count (weekly and overall)
  - Unique user counts
  - Bot deflection rates
  - Chats handled by agents vs. bots

- **Agent Metrics**: Evaluate agent performance 
  - Chat resolution counts by agent
  - Average first response time
  - Average chat resolution time
  - CSAT scores (overall, business hours, non-business hours)

### Bonus Reports
- **Half-Hour Distribution**: See chat volume patterns throughout the day
  - Counts incoming chats based on half-hour periods
  - Visualizes hourly patterns with bar charts

- **Agent Time Tracking**: Track agent productivity metrics
  - **Active Time**: Time from first chat assignment to last chat resolution
  - **Free Time**: Time between chats when agent wasn't handling any chats
  - **Cumulative Time**: Total time spent handling all chats combined

## Getting Started

### Prerequisites
- Python 3.7+
- Streamlit
- Pandas
- Numpy
- XlsxWriter

### Installation
```bash
pip install streamlit pandas numpy xlsxwriter
```

### Running the Application
```bash
streamlit run app.py
```

### Using the Application

1. Upload an Excel file containing your chat data
2. The application will process the data and generate metrics
3. Preview the results in the tabbed interface
4. Download the comprehensive report as an Excel file

## Data Requirements

Your Excel file should contain the following columns:
- **ChatStartTime**: When the chat conversation began
- **ChatEndTime**: When the chat conversation ended
- **ClosedBy**: Who closed the chat (agent name or "System" for bot)
- **AgentAssignmentTimestamp**: When chat was assigned to an agent
- **AgentFirstResponseTime**: Time taken by agent to respond initially

Optional columns:
- **UserId**: Unique identifier for chat users (for unique user calculations)
- **CsatScore**: Customer satisfaction scores (for CSAT metrics)

## Time Metrics Calculation Logic

The agent time tracking metrics are calculated as follows:

If a chat is assigned to an agent at 2:00 PM and another chat at 2:10 PM, with the first chat resolved at 2:20 PM and the second at 2:30 PM:

1. **Cumulative Chat Time**: Sum of individual chat durations
   - First chat: 2:20 PM - 2:00 PM = 20 minutes
   - Second chat: 2:30 PM - 2:10 PM = 20 minutes
   - Total: 40 minutes

2. **Active Chat Time**: Span from first assignment to last resolution
   - 2:30 PM - 2:00 PM = 30 minutes

3. **Free Time**: Time agent was not handling chats
   - Active Time - Cumulative Time = 30 - 40 = -10 minutes
   - Since negative values aren't logical for Free Time, we set any negative values to 0
   - If another chat comes at 2:40 PM, the Free Time between 2:30 PM and 2:40 PM would be 10 minutes

## Development

### Project Structure
- `app.py`: Main Streamlit application file
- `README.md`: Project documentation
- `requirements.txt`: Required Python packages

### Future Enhancements
- Add visual heatmap of busiest hours
- Include sentiment analysis of chat transcripts
- Implement agent scheduling recommendations based on chat volume
- Add trend analysis for monitoring changes over time

## License
This project is licensed under the MIT License - see the LICENSE file for details.
