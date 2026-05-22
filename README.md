# multilingual-emotion-analysis

A starter project for multilingual emotion analysis in **Korean**, **Chinese**, and **English** using Python and BERT.

## Project Structure

- `data/` - Sample multilingual CSV datasets
- `notebooks/` - Jupyter notebooks for experiments and training
- `results/` - Evaluation outputs and artifacts
- `models/` - Saved model checkpoints and final models

## Dataset Format

Each CSV file uses the same schema:

```csv
text,label,language
```

Included sample datasets:

- `data/korean.csv`
- `data/chinese.csv`
- `data/english.csv`

## Starter Notebook

The notebook `notebooks/multilingual_sentiment_bert.ipynb` includes a starter workflow to:

1. Load and combine multilingual CSV data
2. Encode labels
3. Tokenize text with `bert-base-multilingual-cased`
4. Fine-tune a sequence classification model with Hugging Face `Trainer`
5. Run basic evaluation and save outputs

## Quick Start

1. Create and activate a Python environment
2. Install dependencies:
   - `pandas`
   - `scikit-learn`
   - `torch`
   - `transformers`
   - `datasets`
   - `jupyter`
3. Launch Jupyter and open `notebooks/multilingual_sentiment_bert.ipynb`
