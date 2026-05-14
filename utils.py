import json
import pathlib
import random

DATA_PATH=pathlib.Path(__file__).parent / "data"

def read_dataset(name='test.jsonl'):
    res = []
    file_path = DATA_PATH / name
    
    with open(file_path, 'r') as f:
        if name.endswith('.jsonl'):
            # JSONL format: each line is a separate JSON object
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    data = json.loads(line)
                    res.append(data)
        elif name.endswith('.json'):
            # JSON format: entire file is a single JSON array or object
            content = f.read()
            data = json.loads(content)
            if isinstance(data, list):
                res = data
            else:
                res = [data]  # Wrap single object in list
        else:
            # Default to JSONL for unknown extensions
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    res.append(data)
    
    return res

def random_sample(data_list, num_samples):
    """
    Randomly sample elements from the input list and extract questions
    
    Args:
        data_list: Input list to sample from
        num_samples: Number of samples to return
        
    Returns:
        List containing question strings
    """
    
    if not data_list:
        return []
    
    # Ensure num_samples doesn't exceed list length
    n = min(num_samples, len(data_list))
    
    sampled = random.sample(data_list, n)
    
    # Extract questions from sampled data
    result = []
    for item in sampled:
        if isinstance(item, dict):
            if 'question' in item:
                result.append(item['question'])
            elif 'problem' in item:
                result.append(item['problem'])
            elif 'Body' in item and 'Question' in item:
                # SVAMP dataset format: concatenate Body and Question
                combined_question = f"{item['Body']} {item['Question']}"
                result.append(combined_question)
            else:
                # If no question/problem field found, convert to string
                result.append(str(item))
        else:
            # If item is not a dict, convert to string
            result.append(str(item))
    
    return result

