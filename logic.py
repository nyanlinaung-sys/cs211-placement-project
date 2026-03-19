import json
import pandas as pd
import os
from sklearn.tree import DecisionTreeClassifier
from sklearn.multioutput import MultiOutputClassifier

# CONFIGURATION: No magic numbers. Each question is worth 2 points.
# Thresholds are based on the 10-point scale provided in your regulation images.
PASSING_CONFIG = {
    "Group_1_4": {
        "categories": [
            "Basic: loop/ for-each", "Basic: Method/parameter passing", 
            "Basic: If-else/Boolean zen", "Arrays/ArrayList"
        ],
        "abs_min": 4,          # All categories must meet >= 4
        "pass_min": 6,         # Minimum score for passing is 6
        "min_pass_count": 3    # Three categories must meet 6
    },
    "Group_5_6": {
        "categories": ["Classes", "Inheritance/interfaces"],
        "abs_min": 5,          # All categories must meet >= 5
        "pass_min": 7,         # One category must meet 7
        "min_pass_count": 1
    },
    "Group_7_8": {
        "categories": [
            "Java Collections Framework -HashSet", 
            "Java Collections Framework -HashMap"
        ],
        "abs_min": 4,          # All categories must meet >= 4
        "pass_min": 5,         # One category must meet 5
        "min_pass_count": 1
    }
}

def load_questions():
    with open('questions.json', 'r') as f:
        return json.load(f)

def check_passing_status(category_scores):
    """
    Evaluates if the student meets the group-based passing criteria.
    Returns: 'Pass' if all rules met, 'Advice' if close, 'Reject' otherwise.
    """
    # Logic based on the provided Minimum Requirement images
    all_groups_passed = True
    
    for group_name, rules in PASSING_CONFIG.items():
        # Scale category 'correct' count to the 10-point scale (Correct * 2)
        group_points = [category_scores.get(cat, {"correct": 0})["correct"] * 2 for cat in rules["categories"]]
        
        # Rule 1: Every category in the group must meet the absolute minimum
        if not all(p >= rules["abs_min"] for p in group_points):
            return "Reject"
            
        # Rule 2: Specific count must meet the higher passing threshold
        high_scores = sum(1 for p in group_points if p >= rules["pass_min"])
        if high_scores < rules["min_pass_count"]:
            all_groups_passed = False # Might be 'Advice' territory

    return "Pass" if all_groups_passed else "Advice"

def calculate_results(user_answers, questions):
    raw_correct = 0
    feedback = []
    category_scores = {}
    
    for i, q in enumerate(questions):
        cat = q['category']
        if cat not in category_scores:
            category_scores[cat] = {"correct": 0, "total": 0}
        category_scores[cat]["total"] += 1
        
        if i < len(user_answers):
            if user_answers[i] == q['answer']:
                raw_correct += 1
                category_scores[cat]["correct"] += 1
            else:
                feedback.append({"category": cat, "tip": q['tip']})
                
    # Scale to 10-point max (Each question worth 2 points)
    total_points = raw_correct * 2
    
    # Determine Status based on group rules
    status = check_passing_status(category_scores)
    
    return total_points, feedback, category_scores, status

def get_multi_label_prediction(row_data):
    csv_file = 'student_training_data.csv'
    feature_cols = [
        "Basic: loop/ for-each", "Basic: Method/parameter passing", 
        "Basic: If-else/Boolean zen", "Arrays/ArrayList",
        "Classes", "Inheritance/interfaces", 
        "Java Collections Framework -HashSet", "Java Collections Framework -HashMap"
    ]
    target_cols = [f"T_{col}" for col in feature_cols]

    try:
        if not os.path.exists(csv_file):
            raise FileNotFoundError("CSV not found.")
        df = pd.read_csv(csv_file)
        X = df[feature_cols]
        y = df[target_cols]

        model = MultiOutputClassifier(DecisionTreeClassifier(criterion='entropy', max_depth=5))
        model.fit(X, y)  # type: ignore

        current_input = pd.DataFrame([row_data])[feature_cols]
        prediction = model.predict(current_input)[0]  # type: ignore
        results = [feature_cols[i] for i, val in enumerate(prediction) if val == 1]
        return results if results else ["General Review"]
    except Exception:
        # Fallback if CSV/Model fails
        return [cat for cat, score in row_data.items() if score < 6]