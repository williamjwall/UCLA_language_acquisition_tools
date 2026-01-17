# Quick Start Guide

## Process Your CDI Data

```bash
# Process a single file
python process_cdi_data.py cdi_data/UnaccFit_items.csv ToddlerCDI_words_by_section_FINAL.csv

# Process another file
python process_cdi_data.py "cdi_data/Longitudinal MomSeg Follow-Up Study (30 months)_items.csv" ToddlerCDI_words_by_section_FINAL.csv
```

## Run the Visualization App

```bash
streamlit run streamlit_app.py
```

Then:
1. Open your browser to the URL shown (usually `http://localhost:8501`)
2. Upload a CDI data file using the sidebar
3. Explore the data using the tabs
4. Download processed data with section information

## What Gets Created

When you process a file, you'll get:

**`*_produced_words_by_section.csv`** - A clean dataframe with:
   - Subject information (ID, age, sex, study)
   - Each produced word
   - Section mapping for each word
   - One row per produced word

## Example Output

The output will look like:
```
subject_id,age,sex,study_name,word,word_column,section_number,section_title,cdi_code
1,24,Male,UnaccFit,baa baa,baa_baa,1,SOUND EFFECTS AND ANIMAL SOUNDS,1
1,24,Male,UnaccFit,bear,bear,2,ANIMALS (Real or Toy),2
```

This makes it easy to:
- Filter by section
- Count words per section
- Analyze which words are produced
- Create visualizations

