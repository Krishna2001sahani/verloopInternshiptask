import pandas as pd
import streamlit as st
import io
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Chat & Agent Metrics Report Generator", layout="centered")

st.title("📈 Chat & Agent Metrics Report Generator")
st.write("Upload your Excel file and download the comprehensive report with chat and agent metrics!")

# File uploader
uploaded_file = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Read uploaded file
        df = pd.read_excel(uploaded_file)
        
        # Process timestamps for both reports
        df['ChatStartTime'] = pd.to_datetime(df['ChatStartTime'], dayfirst=True, errors='coerce')
        df['ChatEndTime'] = pd.to_datetime(df['ChatEndTime'], dayfirst=True, errors='coerce')
        df['AgentAssignmentTimestamp'] = pd.to_datetime(df['AgentAssignmentTimestamp'], dayfirst=True, errors='coerce')

        # Define bins and labels for both reports
        bins = [
            pd.Timestamp('2021-02-01'),
            pd.Timestamp('2021-02-08'),
            pd.Timestamp('2021-02-15'),
            pd.Timestamp('2021-02-22'),
            pd.Timestamp('2021-03-01')
        ]
        labels = ['01 Feb - 07 Feb', '08 Feb - 14 Feb', '15 Feb - 21 Feb', '22 Feb - 28 Feb']

        # Bin the data into weeks
        df['Week'] = pd.cut(df['ChatEndTime'], bins=bins, labels=labels, right=False)
        
        # ==== CHAT METRICS SECTION ====
        
        # Metric calculations
        incoming_chats = df.groupby('Week').size()
        overall_incoming_chats = df.shape[0]

        unique_users = df.groupby('Week')['UserId'].nunique() if 'UserId' in df.columns else pd.Series(0, index=labels)
        overall_unique_users = df['UserId'].nunique() if 'UserId' in df.columns else 0

        closed_by_bot = df[df['ClosedBy'] == 'System'].groupby('Week').size()
        overall_closed_by_bot = df[df['ClosedBy'] == 'System'].shape[0]

        bot_deflection = (closed_by_bot / incoming_chats) * 100
        overall_bot_deflection = (overall_closed_by_bot / overall_incoming_chats) * 100

        closed_by_agents = df[df['ClosedBy'] != 'System'].groupby('Week').size()
        overall_closed_by_agents = df[df['ClosedBy'] != 'System'].shape[0]

        # Combine into one DataFrame
        chat_summary = pd.DataFrame({
            'Incoming Chats': incoming_chats,
            'Unique Users': unique_users,
            'Closed By Bot': closed_by_bot,
            'Bot Deflection %': bot_deflection,
            'Closed By Agents': closed_by_agents
        }).fillna(0)

        chat_summary['Bot Deflection %'] = chat_summary['Bot Deflection %'].round(2)

        # Add Overall row
        overall_row = pd.DataFrame({
            'Incoming Chats': [overall_incoming_chats],
            'Unique Users': [overall_unique_users],
            'Closed By Bot': [overall_closed_by_bot],
            'Bot Deflection %': [round(overall_bot_deflection, 2)],
            'Closed By Agents': [overall_closed_by_agents]
        }, index=['Overall'])

        final_chat_metrics = pd.concat([overall_row, chat_summary])
        final_chat_metrics = final_chat_metrics.reset_index().rename(columns={'index': 'Week'})
        
        # ==== AGENT METRICS SECTION ====
        
        # Function to convert AgentFirstResponseTime to seconds
        def time_to_seconds(x):
            if pd.isna(x) or x == '-' or x == '':
                return np.nan
            
            try:
                # Convert to string if it's not already
                x_str = str(x)
                
                # If it's a time format like "0:00:04"
                if ':' in x_str:
                    parts = x_str.split(':')
                    if len(parts) == 3:
                        hours = int(parts[0])
                        minutes = int(parts[1])
                        seconds = int(parts[2])
                        return hours * 3600 + minutes * 60 + seconds
                
                # Try pandas timedelta as a fallback
                return pd.to_timedelta(x).total_seconds()
            except Exception:
                return np.nan

        # Convert AgentFirstResponseTime to seconds
        df['AgentFirstResponseTime_seconds'] = df['AgentFirstResponseTime'].apply(time_to_seconds)

        # Calculate Chat Resolution Time (in seconds)
        df['ChatResolutionTime_seconds'] = (df['ChatEndTime'] - df['ChatStartTime']).dt.total_seconds()

        # Filter only agent-handled chats (not System or Bot)
        agent_values = [val for val in df['ClosedBy'].unique() if val not in ['System', 'Bot']]
        df_agents = df[df['ClosedBy'].isin(agent_values)].copy()

        # Business hour check
        def is_business_hour(ts):
            if pd.isna(ts):
                return False
            return 10 <= ts.hour < 17

        df_agents['BusinessHour'] = df_agents['ChatEndTime'].apply(is_business_hour)

        # Create the agent summary dataframe
        agent_records = []

        # Overall summary first
        overall_chats = df_agents.shape[0]
        overall_avg_frt = df_agents['AgentFirstResponseTime_seconds'].mean()
        overall_avg_resolution = df_agents['ChatResolutionTime_seconds'].mean()
        
        # Check if CsatScore column exists
        if 'CsatScore' in df_agents.columns:
            overall_avg_csat = df_agents[df_agents['CsatScore'] > 0]['CsatScore'].mean()
            overall_bh_csat = df_agents[(df_agents['BusinessHour']) & (df_agents['CsatScore'] > 0)]['CsatScore'].mean()
            overall_obh_csat = df_agents[(~df_agents['BusinessHour']) & (df_agents['CsatScore'] > 0)]['CsatScore'].mean()
        else:
            overall_avg_csat = np.nan
            overall_bh_csat = np.nan
            overall_obh_csat = np.nan

        agent_records.append([
            'Overall', 
            'SUM',
            'SUM',
            'AVERAGE',
            'AVERAGE',
            'AVERAGE',
            'AVERAGE',
            'AVERAGE',
        ])

        # Weekly agent-wise report
        for week in labels:
            temp_week = df_agents[df_agents['Week'] == week]
            
            # Add weekly summary row
            weekly_chats = temp_week.shape[0]
            weekly_avg_frt = temp_week['AgentFirstResponseTime_seconds'].mean()
            weekly_avg_resolution = temp_week['ChatResolutionTime_seconds'].mean()
            
            if 'CsatScore' in temp_week.columns:
                weekly_avg_csat = temp_week[temp_week['CsatScore'] > 0]['CsatScore'].mean()
                weekly_bh_csat = temp_week[(temp_week['BusinessHour']) & (temp_week['CsatScore'] > 0)]['CsatScore'].mean()
                weekly_obh_csat = temp_week[(~temp_week['BusinessHour']) & (temp_week['CsatScore'] > 0)]['CsatScore'].mean()
            else:
                weekly_avg_csat = np.nan
                weekly_bh_csat = np.nan
                weekly_obh_csat = np.nan
            
            # Now add agent-specific rows
            for agent in sorted(temp_week['ClosedBy'].unique()):
                temp_agent = temp_week[temp_week['ClosedBy'] == agent]
                chats_resolved = temp_agent.shape[0]
                
                # Check if we have any valid response times for this agent
                valid_frt = temp_agent['AgentFirstResponseTime_seconds'].dropna()
                avg_frt = valid_frt.mean() if not valid_frt.empty else np.nan
                
                avg_chat_resolution = temp_agent['ChatResolutionTime_seconds'].mean()
                
                if 'CsatScore' in temp_agent.columns:
                    avg_csat = temp_agent[temp_agent['CsatScore'] > 0]['CsatScore'].mean()
                    bh_csat = temp_agent[(temp_agent['BusinessHour']) & (temp_agent['CsatScore'] > 0)]['CsatScore'].mean()
                    obh_csat = temp_agent[(~temp_agent['BusinessHour']) & (temp_agent['CsatScore'] > 0)]['CsatScore'].mean()
                else:
                    avg_csat = np.nan
                    bh_csat = np.nan
                    obh_csat = np.nan

                agent_records.append([
                    week,
                    agent,
                    chats_resolved,
                    round(avg_frt, 2) if not pd.isna(avg_frt) else '',
                    round(avg_chat_resolution, 2) if not pd.isna(avg_chat_resolution) else '',
                    round(avg_csat, 2) if not pd.isna(avg_csat) else '',
                    round(bh_csat, 2) if not pd.isna(bh_csat) else '',
                    round(obh_csat, 2) if not pd.isna(obh_csat) else ''
                ])

        # Create Final Agent DataFrame
        final_agent_metrics = pd.DataFrame(agent_records, columns=[
            'Week',
            'Agent Name',
            'Chats Resolved',
            'Avg Agent First Response Time (seconds)',
            'Avg Agent Chat Resolution Time (seconds)',
            'Average Agent CSAT Score',
            'Business Hours CSAT [Business Hours: 10AM-5PM]',
            'Outside Business Hours CSAT'
        ])
        
        # ==== BONUS METRICS SECTION ====
        
        # 1. HALF-HOUR DISTRIBUTION
        # Create a function to extract half-hour periods
        def get_half_hour_period(timestamp):
            if pd.isna(timestamp):
                return np.nan
            hour = timestamp.hour
            minute = 0 if timestamp.minute < 30 else 30
            return f"{hour:02d}:{minute:02d}"
        
        # Apply the function to starting times
        df['HalfHourPeriod'] = df['ChatStartTime'].apply(get_half_hour_period)
        
        # Group by half-hour and count
        half_hour_distribution = df.groupby('HalfHourPeriod').size().reset_index()
        half_hour_distribution.columns = ['HalfHourPeriod', 'IncomingChats']
        
        # Sort by time periods
        half_hour_distribution['SortKey'] = half_hour_distribution['HalfHourPeriod'].apply(
            lambda x: int(x.split(':')[0]) * 60 + int(x.split(':')[1]) if pd.notna(x) else 0
        )
        half_hour_distribution = half_hour_distribution.sort_values('SortKey').drop('SortKey', axis=1)
        half_hour_distribution = half_hour_distribution.dropna()
        
        # 2. AGENT TIME TRACKING
        # Get unique dates and agents
        df_agents['Date'] = df_agents['ChatStartTime'].dt.date
        dates = sorted(df_agents['Date'].unique())
        agents = sorted(df_agents['ClosedBy'].unique())
        
        # Prepare results storage
        agent_time_records = []
        
        # Process each agent on each day
        for date in dates:
            for agent in agents:
                # Filter chats for this agent on this date
                agent_day_chats = df_agents[
                    (df_agents['Date'] == date) & 
                    (df_agents['ClosedBy'] == agent)
                ].copy()
                
                if len(agent_day_chats) == 0:
                    continue
                    
                # Sort by assignment time
                agent_day_chats = agent_day_chats.sort_values('AgentAssignmentTimestamp')
                
                # Calculate cumulative time (sum of individual chat durations)
                cumulative_seconds = 0
                for _, chat in agent_day_chats.iterrows():
                    if pd.notna(chat['ChatEndTime']) and pd.notna(chat['AgentAssignmentTimestamp']):
                        chat_duration = (chat['ChatEndTime'] - chat['AgentAssignmentTimestamp']).total_seconds()
                        cumulative_seconds += max(0, chat_duration)  # Avoid negative durations
                
                # Calculate active time (from first assignment to last resolution)
                if len(agent_day_chats) > 0 and pd.notna(agent_day_chats['AgentAssignmentTimestamp'].min()) and pd.notna(agent_day_chats['ChatEndTime'].max()):
                    first_assignment = agent_day_chats['AgentAssignmentTimestamp'].min()
                    last_resolution = agent_day_chats['ChatEndTime'].max()
                    active_seconds = (last_resolution - first_assignment).total_seconds()
                else:
                    active_seconds = 0
                    
                # Calculate free time (active - cumulative)
                free_seconds = max(0, active_seconds - cumulative_seconds)
                
                # Convert seconds to HH:MM:SS format
                def seconds_to_time_format(seconds):
                    if pd.isna(seconds) or seconds < 0:
                        return "00:00:00"
                    hours, remainder = divmod(int(seconds), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                active_time = seconds_to_time_format(active_seconds)
                free_time = seconds_to_time_format(free_seconds)
                cumulative_time = seconds_to_time_format(cumulative_seconds)
                
                # Add record to results
                agent_time_records.append({
                    'Date': date,
                    'Agent': agent,
                    'Chats Handled': len(agent_day_chats),
                    'Active Time': active_time,
                    'Free Time': free_time,
                    'Cumulative Time': cumulative_time
                })
        
        # Create DataFrame for agent time metrics
        agent_time_df = pd.DataFrame(agent_time_records)
        if len(agent_time_df) == 0:
            # Create empty dataframe with columns if no data
            agent_time_df = pd.DataFrame(columns=['Date', 'Agent', 'Chats Handled', 'Active Time', 'Free Time', 'Cumulative Time'])

        # ==== CREATE COMBINED EXCEL FILE WITH ALL REPORTS ====
        
        # Save the output to an in-memory bytes buffer
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Chat metrics on first tab
            final_chat_metrics.to_excel(writer, index=False, sheet_name='Chat Metrics')
            
            # Agent metrics on second tab
            final_agent_metrics.to_excel(writer, index=False, sheet_name='Agent Metrics')
            
            # Bonus metrics on additional tabs
            half_hour_distribution.to_excel(writer, index=False, sheet_name='Half Hour Distribution')
            agent_time_df.to_excel(writer, index=False, sheet_name='Agent Time Tracking')
            
            # Format all worksheets
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D9E1F2',
                'border': 1,
                'align': 'center'
            })
            
            cell_format = workbook.add_format({'border': 1, 'align': 'center'})
            
            # Format Chat Metrics tab
            chat_worksheet = writer.sheets['Chat Metrics']
            for col_num, value in enumerate(final_chat_metrics.columns.values):
                chat_worksheet.write(0, col_num, value, header_format)
            chat_worksheet.set_column(0, len(final_chat_metrics.columns) - 1, 20, cell_format)
            
            # Format Agent Metrics tab
            agent_worksheet = writer.sheets['Agent Metrics']
            for col_num, value in enumerate(final_agent_metrics.columns.values):
                agent_worksheet.write(0, col_num, value, header_format)
            agent_worksheet.set_column(0, len(final_agent_metrics.columns) - 1, 22, cell_format)
            
            # Format Half Hour Distribution tab
            half_hour_worksheet = writer.sheets['Half Hour Distribution']
            for col_num, value in enumerate(half_hour_distribution.columns.values):
                half_hour_worksheet.write(0, col_num, value, header_format)
            half_hour_worksheet.set_column(0, len(half_hour_distribution.columns) - 1, 15, cell_format)
            
            # Format Agent Time Tracking tab
            time_tracking_worksheet = writer.sheets['Agent Time Tracking']
            for col_num, value in enumerate(agent_time_df.columns.values):
                time_tracking_worksheet.write(0, col_num, value, header_format)
            time_tracking_worksheet.set_column(0, len(agent_time_df.columns) - 1, 15, cell_format)

        st.success("✅ Report generated successfully with all metrics!")

        # Create download button
        st.download_button(
            label="📥 Download Complete Report",
            data=output.getvalue(),
            file_name="chat_and_agent_metrics_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Tabs for preview
        tab1, tab2, tab3, tab4 = st.tabs([
            "Chat Metrics Preview", 
            "Agent Metrics Preview", 
            "Half Hour Distribution", 
            "Agent Time Tracking"
        ])
        
        with tab1:
            st.subheader("🔎 Chat Metrics Preview")
            st.dataframe(final_chat_metrics)
            
        with tab2:
            st.subheader("🔎 Agent Metrics Preview")
            st.dataframe(final_agent_metrics)
            
        with tab3:
            st.subheader("🔎 Half Hour Distribution")
            st.dataframe(half_hour_distribution)
            
            # Add a simple bar chart visualization
            st.bar_chart(half_hour_distribution.set_index('HalfHourPeriod')['IncomingChats'])
            
        with tab4:
            st.subheader("🔎 Agent Time Tracking")
            st.dataframe(agent_time_df)

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
        st.error("For debugging, check the error above and ensure your file has the correct columns")

else:
    st.info("Please upload an Excel file to proceed.")
    
    # Display expected file format
    st.subheader("Expected File Format")
    st.write("""
    Your Excel file should contain the following columns:
    - ChatStartTime
    - ChatEndTime
    - ClosedBy
    - AgentAssignmentTimestamp
    - AgentFirstResponseTime
    
    Optional columns:
    - UserId (for unique user calculations)
    - CsatScore (for CSAT metrics)
    """)
    
    # Display information about the bonus metrics
    st.subheader("Bonus Metrics Included")
    st.write("""
    This app also calculates the following bonus metrics:
    
    1. **Half-Hour Distribution** - Counts incoming chats based on half-hour periods of the day
    
    2. **Agent Time Tracking** - For each agent on a daily basis:
       - **Active Time** - Time from first chat assignment to last chat resolution (HH:MM:SS)
       - **Cumulative Time** - Total time spent handling all chats combined (HH:MM:SS)
       - **Free Time** - Time between chats when agent wasn't handling any chats (HH:MM:SS)
    """)