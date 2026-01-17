# CDI Data Processing and Visualization

This repository contains tools for processing and visualizing CDI (Communicative Development Inventory) data with section information.

## Files

- `ToddlerCDI_words_by_section_FINAL.csv` - Reference file mapping words to sections
- `process_cdi_data.py` - Script to process CDI data and add section information
- `streamlit_app.py` - Interactive web app for data visualization
- `requirements.txt` - Python dependencies

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Processing CDI Data

Process a CDI data file to map produced words to sections:

```bash
python process_cdi_data.py <input_file> <section_file> [output_file]
```

Example:
```bash
python process_cdi_data.py cdi_data/UnaccFit_items.csv ToddlerCDI_words_by_section_FINAL.csv
```

This will create:
- `*_produced_words_by_section.csv` - A clean dataframe with subject info, produced words, and their sections

### Streamlit Visualization App

Run the interactive web app:

```bash
streamlit run streamlit_app.py
```

Then open your browser to the URL shown (typically `http://localhost:8501`).

#### Features:

1. **Data Upload**: Upload CDI data CSV files via the sidebar
2. **Overview Tab**: 
   - Summary statistics
   - Column information
   - Data types and null counts
3. **Data Explorer Tab**:
   - Filter by study, age, sex
   - View filtered data
   - Select specific columns
4. **Visualizations Tab**:
   - Section-based analysis (if section data available)
   - Age distribution
   - Word production statistics
   - Interactive charts using Plotly
5. **Download Tab**:
   - Process data with section information
   - Download long format, wide format, or section summary
   - Download filtered/processed data

## Data Format

### Input CDI Data
CDI data files typically contain:
- Metadata columns (demographics, background info)
- Word columns (one per word, values like "produces", "not yet", "sometimes")
- Summary columns (totals, percentiles, complexity scores)

### Section Reference File
The section reference file (`ToddlerCDI_words_by_section_FINAL.csv`) contains:
- `section_number`: Numeric section identifier
- `section_title`: Name of the section
- `cdi_code`: CDI code for the section
- `word`: The word (normalized for matching)
- `expected_count`: Expected number of words in this section

### Output Format

The output is a simple dataframe with one row per produced word:
- **Subject metadata**: subject_id, age, sex, study_name
- **Word information**: word, word_column (original column name)
- **Section information**: section_number, section_title, cdi_code

Example:
```
subject_id,age,sex,study_name,word,word_column,section_number,section_title,cdi_code
1,24,Male,UnaccFit,baa baa,baa_baa,1,SOUND EFFECTS AND ANIMAL SOUNDS,1
1,24,Male,UnaccFit,bear,bear,2,ANIMALS (Real or Toy),2
```

## Notes

- Word matching is case-insensitive and handles variations (spaces vs underscores)
- Some words may not be found in the section mapping (marked as "UNMAPPED")
- The processing script handles special cases like "chicken.animal" vs "chicken.food"

