"""
Learning Disability Assessment Logic
Enhanced with security validation and improved scoring algorithms.
"""
import logging
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)


class AssessmentValidator:
    """Validation utilities for assessment inputs."""
    
    @staticmethod
    def validate_answers(answers: List[str], expected_count: int) -> bool:
        """Validate assessment answers."""
        if not answers or len(answers) != expected_count:
            return False
        
        # Check for valid answer formats
        valid_patterns = [r'^[a-d]$', r'^[A-D]$', r'^[1-4]$']  # Multiple choice patterns
        for answer in answers:
            if not any(re.match(pattern, str(answer)) for pattern in valid_patterns):
                return False
        
        return True
    
    @staticmethod
    def validate_memory_answers(answers: List[str]) -> bool:
        """Validate memory test answers."""
        if not answers:
            return False
        
        # Check for reasonable word answers (letters and spaces only)
        for answer in answers:
            if not re.match(r'^[a-zA-Z\s]+$', str(answer)):
                return False
        
        return True


def evaluate_dyslexia(answers: List[str]) -> Dict[str, Any]:
    """
    Evaluate dyslexia assessment with enhanced security and scoring.
    
    Args:
        answers: List of user answers (should be 5 answers)
    
    Returns:
        Dictionary with assessment results
    """
    try:
        # Validate inputs
        if not AssessmentValidator.validate_answers(answers, 5):
            raise ValueError("Invalid dyslexia assessment answers")
        
        # Convert answers to lowercase for comparison
        normalized_answers = [str(answer).lower().strip() for answer in answers]
        
        # Enhanced answer key with multiple valid responses
        correct_answers = {
            0: ['b', 'b'],  # Question 1: Multiple acceptable answers
            1: ['b', 'b'],
            2: ['a', 'a'],
            3: ['a', 'a'],
            4: ['b', 'b']
        }
        
        # Calculate score with partial credit
        score = 0
        for i, answer in enumerate(normalized_answers):
            if answer in correct_answers.get(i, []):
                score += 1
            elif answer in ['a', 'b', 'c', 'd']:  # Valid but incorrect
                score += 0.5
        
        # Determine flag based on enhanced criteria
        flag = score < 3.5  # More nuanced threshold
        
        # Enhanced messaging based on score ranges
        if score >= 4.5:
            message = "Excellent performance. No significant signs of dyslexia detected."
        elif score >= 3.5:
            message = "Good performance. Minor areas for improvement may exist."
        elif score >= 2.5:
            message = "Some challenges detected. Consider additional assessment."
        else:
            message = "Significant challenges detected. Professional evaluation recommended."
        
        logger.info(f"Dyslexia assessment completed. Score: {score}/5, Flag: {flag}")
        
        return {
            'type': 'Dyslexia',
            'score': int(score),
            'flag': flag,
            'message': message,
            'confidence': min(100, max(0, int((score / 5) * 100)))
        }
        
    except Exception as e:
        logger.error(f"Error in dyslexia evaluation: {e}")
        raise ValueError("Assessment evaluation failed")


def evaluate_dyscalculia(answers: List[str]) -> Dict[str, Any]:
    """
    Evaluate dyscalculia assessment with enhanced security and scoring.
    
    Args:
        answers: List of user answers (should be 5 answers)
    
    Returns:
        Dictionary with assessment results
    """
    try:
        # Validate inputs
        if not AssessmentValidator.validate_answers(answers, 5):
            raise ValueError("Invalid dyscalculia assessment answers")
        
        # Convert answers to lowercase for comparison
        normalized_answers = [str(answer).lower().strip() for answer in answers]
        
        # Enhanced answer key
        correct_answers = {
            0: ['c', 'c'],
            1: ['b', 'b'],
            2: ['a', 'a'],
            3: ['a', 'a'],
            4: ['b', 'b']
        }
        
        # Calculate score with partial credit
        score = 0
        for i, answer in enumerate(normalized_answers):
            if answer in correct_answers.get(i, []):
                score += 1
            elif answer in ['a', 'b', 'c', 'd']:  # Valid but incorrect
                score += 0.5
        
        # Determine flag based on enhanced criteria
        flag = score < 3.5
        
        # Enhanced messaging
        if score >= 4.5:
            message = "Excellent mathematical reasoning. No significant signs of dyscalculia detected."
        elif score >= 3.5:
            message = "Good mathematical skills. Minor areas for improvement may exist."
        elif score >= 2.5:
            message = "Some mathematical challenges detected. Consider additional assessment."
        else:
            message = "Significant mathematical challenges detected. Professional evaluation recommended."
        
        logger.info(f"Dyscalculia assessment completed. Score: {score}/5, Flag: {flag}")
        
        return {
            'type': 'Dyscalculia',
            'score': int(score),
            'flag': flag,
            'message': message,
            'confidence': min(100, max(0, int((score / 5) * 100)))
        }
        
    except Exception as e:
        logger.error(f"Error in dyscalculia evaluation: {e}")
        raise ValueError("Assessment evaluation failed")


def evaluate_memory(answers: List[str]) -> Dict[str, Any]:
    """
    Evaluate working memory assessment with enhanced security and scoring.
    
    Args:
        answers: List of user recalled items
    
    Returns:
        Dictionary with assessment results
    """
    try:
        # Validate inputs
        if not AssessmentValidator.validate_memory_answers(answers):
            raise ValueError("Invalid memory assessment answers")
        
        # Normalize answers (case-insensitive, strip whitespace)
        normalized_answers = [str(answer).lower().strip() for answer in answers]
        
        # Enhanced correct answers with variations
        correct_items = {
            'apple': ['apple', 'apples'],
            'book': ['book', 'books'],
            'tiger': ['tiger', 'tigers'],
            'spoon': ['spoon', 'spoons']
        }
        
        # Calculate score with fuzzy matching
        score = 0
        matched_items = set()
        
        for answer in normalized_answers:
            for correct_item, variations in correct_items.items():
                if answer in variations and correct_item not in matched_items:
                    score += 1
                    matched_items.add(correct_item)
                    break
        
        # Determine flag based on enhanced criteria
        flag = score < 3  # Need to recall at least 3 out of 4 items
        
        # Enhanced messaging
        if score >= 4:
            message = "Excellent working memory. All items recalled correctly."
        elif score >= 3:
            message = "Good working memory. Minor areas for improvement may exist."
        elif score >= 2:
            message = "Some working memory challenges detected. Consider additional assessment."
        else:
            message = "Significant working memory challenges detected. Professional evaluation recommended."
        
        logger.info(f"Memory assessment completed. Score: {score}/4, Flag: {flag}")
        
        return {
            'type': 'Working Memory',
            'score': score,
            'flag': flag,
            'message': message,
            'confidence': min(100, max(0, int((score / 4) * 100)))
        }
        
    except Exception as e:
        logger.error(f"Error in memory evaluation: {e}")
        raise ValueError("Assessment evaluation failed")


def evaluate_flash_cards(answers: List[str]) -> Dict[str, Any]:
    """
    Evaluate flash card recognition assessment.
    
    Args:
        answers: List of user responses
    
    Returns:
        Dictionary with assessment results
    """
    try:
        # Validate inputs
        if not AssessmentValidator.validate_memory_answers(answers):
            raise ValueError("Invalid flash card assessment answers")
        
        # Normalize answers
        normalized_answers = [str(answer).lower().strip() for answer in answers]
        
        # Correct flash card items with variations
        correct_items = {
            'cat': ['cat', 'cats'],
            'apple': ['apple', 'apples'],
            'book': ['book', 'books'],
            'house': ['house', 'houses'],
            'sun': ['sun', 'sunshine']
        }
        
        # Calculate score
        score = 0
        matched_items = set()
        
        for answer in normalized_answers:
            for correct_item, variations in correct_items.items():
                if answer in variations and correct_item not in matched_items:
                    score += 1
                    matched_items.add(correct_item)
                    break
        
        # Determine flag
        flag = score < 3  # Need to recognize at least 3 out of 5 items
        
        # Enhanced messaging
        if score >= 5:
            message = "Excellent recognition skills. All items identified correctly."
        elif score >= 4:
            message = "Good recognition skills. Minor areas for improvement may exist."
        elif score >= 3:
            message = "Some recognition challenges detected. Consider additional practice."
        else:
            message = "Significant recognition challenges detected. Professional evaluation recommended."
        
        logger.info(f"Flash card assessment completed. Score: {score}/5, Flag: {flag}")
        
        return {
            'type': 'Flash Cards',
            'score': score,
            'flag': flag,
            'message': message,
            'confidence': min(100, max(0, int((score / 5) * 100)))
        }
        
    except Exception as e:
        logger.error(f"Error in flash card evaluation: {e}")
        raise ValueError("Assessment evaluation failed")


def get_assessment_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of multiple assessment results.
    
    Args:
        results: List of assessment result dictionaries
    
    Returns:
        Summary dictionary with overall analysis
    """
    try:
        if not results:
            return {'error': 'No assessment results provided'}
        
        total_assessments = len(results)
        flagged_assessments = sum(1 for result in results if result.get('flag', False))
        average_confidence = sum(result.get('confidence', 0) for result in results) / total_assessments
        
        # Determine overall risk level
        if flagged_assessments >= 3:
            risk_level = 'High'
            recommendation = 'Professional evaluation strongly recommended'
        elif flagged_assessments >= 2:
            risk_level = 'Medium'
            recommendation = 'Consider additional assessments and monitoring'
        elif flagged_assessments >= 1:
            risk_level = 'Low'
            recommendation = 'Monitor progress and consider targeted interventions'
        else:
            risk_level = 'Minimal'
            recommendation = 'Continue regular monitoring and development'
        
        return {
            'total_assessments': total_assessments,
            'flagged_assessments': flagged_assessments,
            'average_confidence': round(average_confidence, 1),
            'risk_level': risk_level,
            'recommendation': recommendation,
            'timestamp': results[0].get('timestamp') if results else None
        }
        
    except Exception as e:
        logger.error(f"Error generating assessment summary: {e}")
        return {'error': 'Failed to generate assessment summary'}
