"""
Simple script to map produced words to sections in CDI data
"""
import pandas as pd
from pathlib import Path


def normalize_word(word):
    """Normalize word for matching (lowercase, replace spaces/underscores)"""
    if pd.isna(word):
        return None
    return str(word).lower().replace(' ', '_').replace('-', '_')


def load_section_mapping(section_file):
    """Load section mapping from reference file"""
    df_sections = pd.read_csv(section_file)
    
    # Create mapping: normalized_word -> section info
    word_to_section = {}
    for _, row in df_sections.iterrows():
        word = normalize_word(row['word'])
        if word:
            word_to_section[word] = {
                'section_number': row['section_number'],
                'section_title': row['section_title'],
                'cdi_code': row['cdi_code']
            }
    
    return word_to_section


def process_cdi_file(input_file, section_file, output_file=None):
    """
    Process CDI data: map produced words to sections
    
    Args:
        input_file: Path to CDI data CSV file
        section_file: Path to section reference CSV file
        output_file: Optional output file path
    """
    print(f"Loading section mapping from {section_file}...")
    word_to_section = load_section_mapping(section_file)
    
    print(f"Loading CDI data from {input_file}...")
    df = pd.read_csv(input_file, low_memory=False)
    
    # Get subject metadata columns (keep these in output)
    metadata_cols = ['subject_id', 'age', 'sex', 'study_name']
    available_metadata = [col for col in metadata_cols if col in df.columns]
    
    # Find all word columns (columns that could be words)
    # Exclude known metadata and summary columns
    exclude_cols = [
        'opt_out', 'local_lab_id', 'repeat_num', 'administration_id', 'link',
        'completed', 'completedBackgroundInfo', 'due_date', 'last_modified',
        'created_date', 'completed_date', 'source_id', 'event_id', 'country',
        'zip_code', 'birth_order', 'birth_weight_lb', 'birth_weight_kg',
        'multi_birth_boolean', 'multi_birth', 'sibling_boolean', 'sibling_count',
        'sibling_data', 'born_on_due_date', 'early_or_late', 'due_date_diff',
        'form_filler', 'form_filler_other', 'primary_caregiver', 'primary_caregiver_other',
        'mother_yob', 'mother_education', 'secondary_caregiver', 'secondary_caregiver_other',
        'father_yob', 'father_education', 'annual_income', 'child_hispanic_latino',
        'child_ethnicity', 'caregiver_info', 'caregiver_other', 'other_languages_boolean',
        'other_languages', 'language_from', 'language_days_per_week', 'language_hours_per_day',
        'ear_infections_boolean', 'ear_infections', 'hearing_loss_boolean', 'hearing_loss',
        'vision_problems_boolean', 'vision_problems', 'illnesses_boolean', 'illnesses',
        'services_boolean', 'services', 'worried_boolean', 'worried',
        'learning_disability_boolean', 'learning_disability', 'children_comforted',
        'show_respect', 'close_bonds', 'parents_help_learn', 'play_learning',
        'explore_experiment', 'do_as_told', 'read_at_home', 'teach_alphbet',
        'rhyming_games', 'read_for_pleasure', 'child_asks_for_reading',
        'child_self_reads', 'child_asks_words_say', 'place_of_residence',
        'primary_caregiver_occupation', 'primary_caregiver_occupation_description',
        'secondary_caregiver_occupation', 'secondary_caregiver_occupation_description',
        'kindergarten_since_when', 'kindergarten_hpd', 'kindergarten_dpw',
        'benchmark age', 'benchmark cohort age', 'Total Produced',
        'Total Produced Percentile-sex', 'Total Produced Percentile-both',
        'How Children Use Words', 'Word Endings 1', 'Word Endings 1 Percentile-sex',
        'Word Endings 1 Percentile-both', 'Word Forms 1 Nouns',
        'Word Forms 1 Nouns Percentile-sex', 'Word Forms 1 Nouns Percentile-both',
        'Word Forms 1 Verbs', 'Word Forms 2 Nouns', 'Word Forms 2 Verbs',
        'Combining', 'Combining % yes answers at this age and sex', 'Complexity',
        'Complexity Percentile-sex', 'Complexity Percentile-both',
        'Combination Example 1', 'Combination Example 2', 'Combination Example 3',
        'usepast', 'usefuture', 'miss_produce', 'miss_comp', 'usepossessive',
        'splural', 'spossess', 'ing', 'ed', 'combine'
    ]
    
    exclude_set = set(exclude_cols + available_metadata)
    word_columns = [col for col in df.columns if col not in exclude_set]
    
    print(f"Found {len(word_columns)} word columns")
    
    # Process each row and collect produced words with sections
    results = []
    
    for idx, row in df.iterrows():
        # Get subject info
        subject_info = {col: row.get(col) for col in available_metadata}
        
        # Find all produced words for this subject
        for word_col in word_columns:
            value = row[word_col]
            
            # Check if word is produced
            if pd.notna(value) and str(value).strip().lower() == 'produces':
                # Normalize column name to match section file
                normalized_col = normalize_word(word_col)
                
                # Handle special cases (e.g., "chicken.animal" -> "chicken")
                base_word = normalized_col.split('.')[0] if '.' in normalized_col else normalized_col
                
                # Get section info
                section_info = word_to_section.get(base_word)
                
                if section_info:
                    # Add to results
                    result_row = {
                        **subject_info,
                        'word': base_word.replace('_', ' '),
                        'word_column': word_col,
                        'section_number': section_info['section_number'],
                        'section_title': section_info['section_title'],
                        'cdi_code': section_info['cdi_code']
                    }
                    results.append(result_row)
    
    # Create new dataframe
    df_result = pd.DataFrame(results)
    
    # Save output
    if output_file is None:
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_produced_words_by_section.csv"
    else:
        output_file = Path(output_file)
    
    print(f"Saving results to {output_file}...")
    df_result.to_csv(output_file, index=False)
    
    print(f"\n✅ Processing complete!")
    print(f"  - Total produced words: {len(df_result)}")
    print(f"  - Unique subjects: {df_result['subject_id'].nunique() if 'subject_id' in df_result.columns else 'N/A'}")
    print(f"  - Unique sections: {df_result['section_title'].nunique() if 'section_title' in df_result.columns else 'N/A'}")
    
    # Show summary by section
    if len(df_result) > 0 and 'section_title' in df_result.columns:
        print(f"\n📊 Words produced by section:")
        section_counts = df_result.groupby('section_title').size().sort_values(ascending=False)
        for section, count in section_counts.head(10).items():
            print(f"  - {section}: {count} words")
    
    return df_result


def create_aggregated_by_section(df_long):
    """
    Create aggregated DataFrame with words grouped by section as lists.
    
    Args:
        df_long: Long-format DataFrame from process_cdi_file (one row per word)
    
    Returns:
        DataFrame with columns: subject_id, age, sex, study_name, section_number, 
        section_title, cdi_code, words (list), word_count
    """
    if len(df_long) == 0:
        return pd.DataFrame()
    
    # Group by subject and section, aggregating words into lists
    agg_dict = {
        'word': lambda x: list(x),  # Collect words as list
    }
    
    # Get all subject metadata columns (excluding word-related columns)
    subject_cols = ['subject_id', 'age', 'sex', 'study_name']
    available_subject_cols = [col for col in subject_cols if col in df_long.columns]
    
    # Get section columns
    section_cols = ['section_number', 'section_title', 'cdi_code']
    available_section_cols = [col for col in section_cols if col in df_long.columns]
    
    # Group by subject info and section info
    groupby_cols = available_subject_cols + available_section_cols
    
    # For section columns, take first value (they should be same within group)
    agg_dict.update({col: 'first' for col in available_section_cols})
    
    df_agg = df_long.groupby(groupby_cols, as_index=False).agg(agg_dict)
    
    # Rename word column to words and add word count
    df_agg = df_agg.rename(columns={'word': 'words'})
    df_agg['word_count'] = df_agg['words'].apply(len)
    
    # Reorder columns: subject info, section info, words, word_count
    column_order = available_subject_cols + available_section_cols + ['words', 'word_count']
    df_agg = df_agg[column_order]
    
    return df_agg


def calculate_key_metrics(df_long, df_original=None):
    """
    Calculate key metrics for each subject:
    1. Total words produced
    2. Number of verbs produced (sections 14, 15, 21)
    3. Number of pronouns produced (section 19)
    4. Wh-words produced (section 16)
    5. Words produced (JSON with word and section info)
    5. Parent/Subject info (JSON with all metadata)
    
    Args:
        df_long: Long-format DataFrame from process_cdi_file (one row per word)
        df_original: Original DataFrame (optional, for parent info)
    
    Returns:
        DataFrame with columns: subject_id, age, sex, study_name, total_words, 
        verbs_count, pronouns_count, wh_words_count, words_produced (JSON), parent_info (JSON)
    """
    import json
    
    if len(df_long) == 0:
        return pd.DataFrame()
    
    # Verb sections: 14 (ADVERBS), 15 (ACTION WORDS), 21 (HELPING VERBS)
    verb_sections = [14, 15, 21]
    pronoun_section = 19
    wh_words_section = 16
    
    # Get subject metadata columns
    subject_cols = ['subject_id', 'age', 'sex', 'study_name']
    available_subject_cols = [col for col in subject_cols if col in df_long.columns]
    
    if 'subject_id' not in df_long.columns:
        # Use index as subject identifier if subject_id not available
        df_long = df_long.copy()
        df_long['subject_id'] = df_long.index
    
    # Group by subject and calculate metrics
    results = []
    
    for subject_id, group in df_long.groupby('subject_id'):
        # Get subject info from first row
        subject_info = {}
        if len(group) > 0:
            first_row = group.iloc[0]
            for col in available_subject_cols:
                if col in first_row:
                    subject_info[col] = first_row[col]
        
        # Ensure subject_id is in the result
        if 'subject_id' not in subject_info:
            subject_info['subject_id'] = subject_id
        
        # Calculate metrics
        total_words = len(group)
        
        # Verbs: sections 14, 15, 21
        verbs = group[group['section_number'].isin(verb_sections)]
        verbs_count = len(verbs)
        
        # Pronouns: section 19
        pronouns = group[group['section_number'] == pronoun_section]
        pronouns_count = len(pronouns)
        
        # Wh-words: section 16
        wh_words = group[group['section_number'] == wh_words_section]
        wh_words_count = len(wh_words)
        
        # Create words_produced JSON: list of dicts with word and section info
        words_list = []
        for _, row in group.iterrows():
            word_entry = {
                'word': row.get('word', ''),
                'section_number': int(row.get('section_number', 0)) if pd.notna(row.get('section_number')) else None,
                'section_title': row.get('section_title', ''),
                'cdi_code': int(row.get('cdi_code', 0)) if pd.notna(row.get('cdi_code')) else None
            }
            words_list.append(word_entry)
        
        words_produced_json = json.dumps(words_list)
        
        # Get parent/subject info from original dataframe if available
        parent_info_json = "{}"
        if df_original is not None and 'subject_id' in df_original.columns:
            parent_rows = df_original[df_original['subject_id'] == subject_id]
            if len(parent_rows) > 0:
                parent_row = parent_rows.iloc[0]
                
                # Identify word columns to exclude (same logic as in process_cdi_file)
                metadata_cols = ['subject_id', 'age', 'sex', 'study_name']
                exclude_cols = [
                    'opt_out', 'local_lab_id', 'repeat_num', 'administration_id', 'link',
                    'completed', 'completedBackgroundInfo', 'due_date', 'last_modified',
                    'created_date', 'completed_date', 'source_id', 'event_id', 'country',
                    'zip_code', 'birth_order', 'birth_weight_lb', 'birth_weight_kg',
                    'multi_birth_boolean', 'multi_birth', 'sibling_boolean', 'sibling_count',
                    'sibling_data', 'born_on_due_date', 'early_or_late', 'due_date_diff',
                    'form_filler', 'form_filler_other', 'primary_caregiver', 'primary_caregiver_other',
                    'mother_yob', 'mother_education', 'secondary_caregiver', 'secondary_caregiver_other',
                    'father_yob', 'father_education', 'annual_income', 'child_hispanic_latino',
                    'child_ethnicity', 'caregiver_info', 'caregiver_other', 'other_languages_boolean',
                    'other_languages', 'language_from', 'language_days_per_week', 'language_hours_per_day',
                    'ear_infections_boolean', 'ear_infections', 'hearing_loss_boolean', 'hearing_loss',
                    'vision_problems_boolean', 'vision_problems', 'illnesses_boolean', 'illnesses',
                    'services_boolean', 'services', 'worried_boolean', 'worried',
                    'learning_disability_boolean', 'learning_disability', 'children_comforted',
                    'show_respect', 'close_bonds', 'parents_help_learn', 'play_learning',
                    'explore_experiment', 'do_as_told', 'read_at_home', 'teach_alphbet',
                    'rhyming_games', 'read_for_pleasure', 'child_asks_for_reading',
                    'child_self_reads', 'child_asks_words_say', 'place_of_residence',
                    'primary_caregiver_occupation', 'primary_caregiver_occupation_description',
                    'secondary_caregiver_occupation', 'secondary_caregiver_occupation_description',
                    'kindergarten_since_when', 'kindergarten_hpd', 'kindergarten_dpw',
                    'benchmark age', 'benchmark cohort age', 'Total Produced',
                    'Total Produced Percentile-sex', 'Total Produced Percentile-both',
                    'How Children Use Words', 'Word Endings 1', 'Word Endings 1 Percentile-sex',
                    'Word Endings 1 Percentile-both', 'Word Forms 1 Nouns',
                    'Word Forms 1 Nouns Percentile-sex', 'Word Forms 1 Nouns Percentile-both',
                    'Word Forms 1 Verbs', 'Word Forms 2 Nouns', 'Word Forms 2 Verbs',
                    'Combining', 'Combining % yes answers at this age and sex', 'Complexity',
                    'Complexity Percentile-sex', 'Complexity Percentile-both',
                    'Combination Example 1', 'Combination Example 2', 'Combination Example 3',
                    'usepast', 'usefuture', 'miss_produce', 'miss_comp', 'usepossessive',
                    'splural', 'spossess', 'ing', 'ed', 'combine'
                ]
                
                # Columns to include (metadata and excluded columns, but NOT word columns)
                exclude_set = set(exclude_cols + metadata_cols)
                word_columns = [col for col in df_original.columns if col not in exclude_set]
                
                # Get all columns except word columns (which are already in words_produced)
                parent_info = {}
                for col in parent_row.index:
                    # Skip word columns
                    if col not in word_columns:
                        value = parent_row[col]
                        # Convert to JSON-serializable format
                        if pd.notna(value):
                            if isinstance(value, (list, dict)):
                                parent_info[col] = value
                            else:
                                parent_info[col] = str(value)
                
                parent_info_json = json.dumps(parent_info)
        
        result_row = {
            **subject_info,
            'total_words': total_words,
            'verbs_count': verbs_count,
            'pronouns_count': pronouns_count,
            'wh_words_count': wh_words_count,
            'words_produced': words_produced_json,
            'parent_info': parent_info_json
        }
        results.append(result_row)
    
    df_metrics = pd.DataFrame(results)
    
    # Reorder columns
    if len(df_metrics) > 0:
        column_order = available_subject_cols + ['total_words', 'verbs_count', 'pronouns_count', 'wh_words_count', 'words_produced', 'parent_info']
        # Only include columns that exist
        column_order = [col for col in column_order if col in df_metrics.columns]
        df_metrics = df_metrics[column_order]
    
    return df_metrics


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python process_cdi_data.py <input_cdi_file> <section_file> [output_file]")
        print("\nExample:")
        print("  python process_cdi_data.py cdi_data/UnaccFit_items.csv ToddlerCDI_words_by_section_FINAL.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    section_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    process_cdi_file(input_file, section_file, output_file)
