# FileX Practice Directory

This directory is set up for testing FileX indexing and search functionality.

## Structure

- `sample1.txt` - Contains information about types of fruits
- `sample2.txt` - Contains information about programming languages
- `sample3.txt` - Contains information about cooking techniques
- `documents/` - Subdirectory with additional text files
- `data/` - Subdirectory with data-related content
- `test_query_examples.txt` - Suggested queries for testing

## Testing FileX

### 1. Index the practice directory

From the backend directory:
```bash
cd backend
python filex.py index ../practice
```

Or from the practice directory:
```bash
cd practice
python ../backend/filex.py index .
```

### 2. Search for content

```bash
python filex.py search "types of fruits"
python filex.py search "programming languages"
python filex.py search "cooking techniques"
python filex.py search "data processing"
python filex.py search "meeting notes"
```

### 3. Check status

```bash
python filex.py status
```

## Notes

- The `.filex` directory will be created automatically when you run the index command
- This directory is a git repository for testing
- All text files are `.txt` format for easy testing
