def evaluate_dyslexia(answers):
    # Simple answer key for demo purposes
    correct = ['b','b','a','a','b']
    score = sum(1 for a,c in zip(answers, correct) if a==c)
    return {
        'type': 'Dyslexia',
        'score': score,
        'flag': score < 3,
        'message': 'Possible signs of dyslexia' if score < 3 else 'No major signs detected.'
    }

def evaluate_dyscalculia(answers):
    correct = ['c','b','a','a','b']
    score = sum(1 for a,c in zip(answers, correct) if a==c)
    return {
        'type': 'Dyscalculia',
        'score': score,
        'flag': score < 3,
        'message': 'Possible signs of dyscalculia' if score < 3 else 'No major signs detected.'
    }

def evaluate_memory(answers):
    correct = ['Apple','Book','Tiger','Spoon']
    # answers is list of selected values
    score = sum(1 for a in answers if a in correct)
    return {
        'type': 'Working Memory',
        'score': score,
        'flag': score < 2,
        'message': 'Possible working memory challenges' if score < 2 else 'Working memory within typical range.'
    }
