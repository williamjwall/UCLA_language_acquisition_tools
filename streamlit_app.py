"""
Simple Streamlit app for CDI data analysis
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import tempfile
import os
import json

# Page config
st.set_page_config(
    page_title="UCLA MacArthur-Bates CDI Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 UCLA MacArthur-Bates CDI Analyzer")
st.markdown("Upload CDI data to analyze word production metrics")

# Sidebar for file upload
st.sidebar.header("📁 Upload Data")
uploaded_file = st.sidebar.file_uploader(
    "Upload CDI data file (CSV)",
    type=['csv'],
    help="Upload a CDI data file to analyze"
)

# Load section reference data
@st.cache_data
def load_section_data():
    """Load section reference data"""
    section_file = Path("ToddlerCDI_words_by_section_FINAL.csv")
    if section_file.exists():
        return pd.read_csv(section_file)
    return None

section_ref = load_section_data()

# Main content
if uploaded_file is not None:
    try:
        # Load data
        df = pd.read_csv(uploaded_file, low_memory=False)
        st.success(f"✅ Loaded {len(df)} rows")
        
        # Process data automatically
        st.header("📋 Processing Data")
        with st.spinner("Mapping words to sections..."):
            from process_cdi_data import process_cdi_file, calculate_key_metrics
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
                df.to_csv(tmp.name, index=False)
                tmp_path = tmp.name
            
            # Process
            output_path = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False).name
            df_processed = process_cdi_file(
                tmp_path,
                "ToddlerCDI_words_by_section_FINAL.csv",
                output_path
            )
            
            # Calculate key metrics (pass original df for parent info)
            df_metrics = calculate_key_metrics(df_processed, df_original=df)
            
            # Cleanup temp files
            os.unlink(tmp_path)
            os.unlink(output_path)
        
        if len(df_metrics) == 0:
            st.warning("No data could be processed. Please check your file format.")
        else:
            st.success(f"✅ Processed {len(df_metrics)} subjects")
            
            # Display metrics
            st.header("📈 Key Metrics")
            
            # Summary cards
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                avg_total = df_metrics['total_words'].mean()
                st.metric("Avg Total Words", f"{avg_total:.1f}")
            with col2:
                avg_verbs = df_metrics['verbs_count'].mean()
                st.metric("Avg Verbs", f"{avg_verbs:.1f}")
            with col3:
                avg_pronouns = df_metrics['pronouns_count'].mean()
                st.metric("Avg Pronouns", f"{avg_pronouns:.1f}")
            with col4:
                avg_wh = df_metrics['wh_words_count'].mean()
                st.metric("Avg Wh-words", f"{avg_wh:.1f}")
            
            # Data table (hide JSON columns for cleaner display)
            st.subheader("Metrics by Subject")
            display_cols = [col for col in df_metrics.columns if col not in ['words_produced', 'parent_info']]
            st.dataframe(df_metrics[display_cols], use_container_width=True, height=400)
            
            # Expandable sections for JSON data
            if 'words_produced' in df_metrics.columns:
                with st.expander("View Words Produced (JSON)", expanded=False):
                    if 'subject_id' in df_metrics.columns:
                        subject_options = df_metrics['subject_id'].tolist()
                        selected_subject = st.selectbox(
                            "Select Subject",
                            options=subject_options,
                            key="words_select"
                        )
                        words_json = df_metrics[df_metrics['subject_id'] == selected_subject]['words_produced'].iloc[0]
                    else:
                        selected_idx = st.selectbox(
                            "Select Subject",
                            options=range(len(df_metrics)),
                            format_func=lambda x: f"Subject {x}",
                            key="words_select"
                        )
                        words_json = df_metrics.iloc[selected_idx]['words_produced']
                    words_data = json.loads(words_json)
                    
                    # Transform to section-based structure: {section_title: [words]}
                    section_words = {}
                    for word_entry in words_data:
                        section_title = word_entry.get('section_title', 'Unknown')
                        word = word_entry.get('word', '')
                        if section_title not in section_words:
                            section_words[section_title] = []
                        section_words[section_title].append(word)
                    
                    st.json(section_words)
            
            if 'parent_info' in df_metrics.columns:
                with st.expander("Subject Info (JSON)", expanded=False):
                    if 'subject_id' in df_metrics.columns:
                        subject_options = df_metrics['subject_id'].tolist()
                        selected_subject = st.selectbox(
                            "Select Subject",
                            options=subject_options,
                            key="parent_select"
                        )
                        parent_json = df_metrics[df_metrics['subject_id'] == selected_subject]['parent_info'].iloc[0]
                    else:
                        selected_idx = st.selectbox(
                            "Select Subject",
                            options=range(len(df_metrics)),
                            format_func=lambda x: f"Subject {x}",
                            key="parent_select"
                        )
                        parent_json = df_metrics.iloc[selected_idx]['parent_info']
                    parent_data = json.loads(parent_json)
                    st.json(parent_data)
            
            # Visualizations
            st.header("📊 Visualizations")
            
            # Bar graphs for words by section
            if 'words_produced' in df_metrics.columns:
                st.subheader("Words by Section")
                
                # Aggregate words by section across all subjects
                section_counts = {}
                for _, row in df_metrics.iterrows():
                    words_json = row['words_produced']
                    words_data = json.loads(words_json)
                    for word_entry in words_data:
                        section_title = word_entry.get('section_title', 'Unknown')
                        section_counts[section_title] = section_counts.get(section_title, 0) + 1
                
                if section_counts:
                    df_sections = pd.DataFrame([
                        {'Section': k, 'Word Count': v} 
                        for k, v in sorted(section_counts.items(), key=lambda x: x[1], reverse=True)
                    ])
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Top sections bar chart
                        fig_sections = px.bar(
                            df_sections.head(20),
                            x='Word Count',
                            y='Section',
                            orientation='h',
                            title="Top 20 Sections by Word Count (All Subjects)",
                            labels={'Word Count': 'Number of Words Produced', 'Section': 'Section Title'}
                        )
                        fig_sections.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig_sections, use_container_width=True)
                    
                    with col2:
                        # All sections bar chart
                        fig_all = px.bar(
                            df_sections,
                            x='Section',
                            y='Word Count',
                            title="All Sections - Word Count (All Subjects)",
                            labels={'Word Count': 'Number of Words Produced', 'Section': 'Section Title'}
                        )
                        fig_all.update_layout(height=600, xaxis_tickangle=-45)
                        st.plotly_chart(fig_all, use_container_width=True)
                    
                    # Per-subject section breakdown
                    st.subheader("Words by Section - Individual Subjects")
                    if 'subject_id' in df_metrics.columns:
                        selected_subject_viz = st.selectbox(
                            "Select Subject to View",
                            options=df_metrics['subject_id'].tolist(),
                            key="section_viz_select"
                        )
                    else:
                        selected_subject_viz = st.selectbox(
                            "Select Subject to View",
                            options=range(len(df_metrics)),
                            format_func=lambda x: f"Subject {x}",
                            key="section_viz_select"
                        )
                    
                    # Get words for selected subject
                    if 'subject_id' in df_metrics.columns:
                        subject_row = df_metrics[df_metrics['subject_id'] == selected_subject_viz].iloc[0]
                    else:
                        subject_row = df_metrics.iloc[selected_subject_viz]
                    
                    words_json = subject_row['words_produced']
                    words_data = json.loads(words_json)
                    
                    # Count words by section for this subject
                    subject_section_counts = {}
                    for word_entry in words_data:
                        section_title = word_entry.get('section_title', 'Unknown')
                        subject_section_counts[section_title] = subject_section_counts.get(section_title, 0) + 1
                    
                    if subject_section_counts:
                        df_subject_sections = pd.DataFrame([
                            {'Section': k, 'Word Count': v} 
                            for k, v in sorted(subject_section_counts.items(), key=lambda x: x[1], reverse=True)
                        ])
                        
                        fig_subject = px.bar(
                            df_subject_sections,
                            x='Section',
                            y='Word Count',
                            title=f"Words by Section - Subject {selected_subject_viz}",
                            labels={'Word Count': 'Number of Words Produced', 'Section': 'Section Title'}
                        )
                        fig_subject.update_layout(height=500, xaxis_tickangle=-45)
                        st.plotly_chart(fig_subject, use_container_width=True)
            
            viz_col1, viz_col2 = st.columns(2)
            
            with viz_col1:
                # Total words distribution
                fig1 = px.histogram(
                    df_metrics,
                    x='total_words',
                    nbins=20,
                    title="Total Words Produced Distribution",
                    labels={'total_words': 'Total Words', 'count': 'Number of Children'}
                )
                st.plotly_chart(fig1, use_container_width=True)
                
                # Verbs vs Pronouns scatter
                fig3 = px.scatter(
                    df_metrics,
                    x='verbs_count',
                    y='pronouns_count',
                    size='total_words',
                    hover_data=['subject_id', 'age', 'sex'] if 'subject_id' in df_metrics.columns else [],
                    title="Verbs vs Pronouns",
                    labels={'verbs_count': 'Verbs Count', 'pronouns_count': 'Pronouns Count'}
                )
                st.plotly_chart(fig3, use_container_width=True)
            
            with viz_col2:
                # Verbs, Pronouns, Wh-words comparison
                metrics_long = pd.melt(
                    df_metrics,
                    id_vars=[col for col in df_metrics.columns if col not in ['total_words', 'verbs_count', 'pronouns_count', 'wh_words_count', 'words_produced', 'parent_info']],
                    value_vars=['verbs_count', 'pronouns_count', 'wh_words_count'],
                    var_name='Metric',
                    value_name='Count'
                )
                metrics_long['Metric'] = metrics_long['Metric'].str.replace('_count', '').str.replace('_', ' ').str.title()
                
                fig2 = px.box(
                    metrics_long,
                    x='Metric',
                    y='Count',
                    title="Verbs, Pronouns, and Wh-words Distribution",
                    labels={'Count': 'Count', 'Metric': 'Word Type'}
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                # Age vs Total Words (if age available)
                if 'age' in df_metrics.columns:
                    fig4 = px.scatter(
                        df_metrics,
                        x='age',
                        y='total_words',
                        color='sex' if 'sex' in df_metrics.columns else None,
                        hover_data=['subject_id'] if 'subject_id' in df_metrics.columns else [],
                        title="Age vs Total Words Produced",
                        labels={'age': 'Age (months)', 'total_words': 'Total Words'}
                    )
                    st.plotly_chart(fig4, use_container_width=True)
            
            # Download section
            st.header("💾 Download Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Download metrics
                csv_metrics = df_metrics.to_csv(index=False)
                st.download_button(
                    label="📥 Download Metrics (CSV)",
                    data=csv_metrics,
                    file_name="cdi_metrics.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Download processed data (long format)
                csv_processed = df_processed.to_csv(index=False)
                st.download_button(
                    label="📥 Download Processed Data (CSV)",
                    data=csv_processed,
                    file_name="cdi_processed_data.csv",
                    mime="text/csv"
                )
    
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.exception(e)

else:
    st.info("👈 Please upload a CDI data file using the sidebar to get started.")
    
    st.markdown("""
    ### What this app does:
    
    1. **Upload** your CDI data file
    2. **Process** - Automatically maps words to sections
    3. **Analyze** - Calculates key metrics:
       - Total words produced
       - Verbs produced (sections 14, 15, 21)
       - Pronouns produced (section 19)
       - Wh-words produced (section 16)
    4. **Visualize** - Simple charts showing the data
    5. **Download** - Export your results
    
    ### Metrics Explained:
    - **Total Words**: All words produced by the child
    - **Verbs**: Includes Adverbs (14), Action Words (15), and Helping Verbs (21)
    - **Pronouns**: Section 19 only
    - **Wh-words**: Question words from section 16
    """)
