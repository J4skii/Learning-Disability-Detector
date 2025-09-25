import numpy as np
from typing import Dict, List, Tuple, Any
import json
from datetime import datetime

class AssessmentEngine:
    """Enhanced ML-based assessment engine"""
    
    def __init__(self):
        self.assessment_configs = {
            'dyslexia': {
                'questions': [
                    {
                        'id': 'spelling_1',
                        'type': 'multiple_choice',
                        'question': 'Choose the correct spelling:',
                        'options': ['Acomodate', 'Accommodate', 'Acomadate'],
                        'correct': 1,
                        'weight': 1.0,
                        'difficulty': 'medium'
                    },
                    {
                        'id': 'synonym_1',
                        'type': 'multiple_choice',
                        'question': 'Match the word: Confident',
                        'options': ['Timid', 'Sure of oneself', 'Sad'],
                        'correct': 1,
                        'weight': 1.2,
                        'difficulty': 'easy'
                    },
                    # Add more sophisticated questions
                ],
                'thresholds': {
                    'low_risk': 0.8,
                    'medium_risk': 0.6,
                    'high_risk': 0.4
                }
            },
            'dyscalculia': {
                'questions': [
                    {
                        'id': 'sequence_1',
                        'type': 'multiple_choice',
                        'question': 'What comes next in this sequence? 2, 4, 8, 16, __',
                        'options': ['18', '24', '32'],
                        'correct': 2,
                        'weight': 1.5,
                        'difficulty': 'hard'
                    },
                    # Add more questions
                ],
                'thresholds': {
                    'low_risk': 0.75,
                    'medium_risk': 0.5,
                    'high_risk': 0.3
                }
            },
            'memory': {
                'items': ['Apple', 'Book', 'Tiger', 'Spoon'],
                'distractors': ['Banana', 'Car'],
                'thresholds': {
                    'low_risk': 0.75,
                    'medium_risk': 0.5,
                    'high_risk': 0.25
                }
            }
        }
    
    def evaluate_assessment(self, test_type: str, responses: List[str], 
                          user_profile: Dict, response_times: List[float] = None) -> Dict[str, Any]:
        """Enhanced evaluation with ML-like scoring"""
        
        if test_type == 'memory':
            return self._evaluate_memory(responses, user_profile, response_times)
        else:
            return self._evaluate_cognitive(test_type, responses, user_profile, response_times)
    
    def _evaluate_cognitive(self, test_type: str, responses: List[str], 
                           user_profile: Dict, response_times: List[float] = None) -> Dict[str, Any]:
        """Evaluate cognitive assessments with weighted scoring"""
        
        config = self.assessment_configs[test_type]
        questions = config['questions']
        
        total_weight = sum(q['weight'] for q in questions)
        weighted_score = 0
        correct_count = 0
        
        response_analysis = []
        
        for i, (response, question) in enumerate(zip(responses, questions)):
            is_correct = response == chr(ord('a') + question['correct'])
            if is_correct:
                weighted_score += question['weight']
                correct_count += 1
            
            # Analyze response time if available
            time_factor = 1.0
            if response_times and i < len(response_times):
                expected_time = self._get_expected_time(question['difficulty'])
                time_ratio = response_times[i] / expected_time
                time_factor = self._calculate_time_factor(time_ratio)
            
            response_analysis.append({
                'question_id': question['id'],
                'correct': is_correct,
                'response_time': response_times[i] if response_times and i < len(response_times) else None,
                'time_factor': time_factor,
                'difficulty': question['difficulty']
            })
        
        # Calculate normalized score
        normalized_score = weighted_score / total_weight
        
        # Apply user profile adjustments
        profile_adjustment = self._calculate_profile_adjustment(user_profile, test_type)
        adjusted_score = min(1.0, normalized_score * profile_adjustment)
        
        # Determine risk level and confidence
        risk_level, confidence = self._calculate_risk_and_confidence(
            adjusted_score, config['thresholds'], response_analysis
        )
        
        return {
            'type': test_type.title(),
            'score': correct_count,
            'max_score': len(questions),
            'normalized_score': round(adjusted_score, 3),
            'confidence_score': round(confidence, 3),
            'flag': risk_level in ['medium_risk', 'high_risk'],
            'risk_level': risk_level,
            'message': self._generate_message(test_type, risk_level, adjusted_score),
            'recommendations': self._generate_recommendations(test_type, risk_level, response_analysis),
            'response_analysis': response_analysis
        }
    
    def _evaluate_memory(self, responses: List[str], user_profile: Dict, 
                        response_times: List[float] = None) -> Dict[str, Any]:
        """Enhanced memory evaluation"""
        
        config = self.assessment_configs['memory']
        correct_items = set(config['items'])
        selected_items = set(responses)
        
        # Calculate precision, recall, and F1 score
        true_positives = len(correct_items.intersection(selected_items))
        false_positives = len(selected_items - correct_items)
        false_negatives = len(correct_items - selected_items)
        
        precision = true_positives / len(selected_items) if selected_items else 0
        recall = true_positives / len(correct_items)
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Apply profile adjustments
        profile_adjustment = self._calculate_profile_adjustment(user_profile, 'memory')
        adjusted_score = min(1.0, f1_score * profile_adjustment)
        
        risk_level, confidence = self._calculate_risk_and_confidence(
            adjusted_score, config['thresholds'], []
        )
        
        return {
            'type': 'Working Memory',
            'score': true_positives,
            'max_score': len(correct_items),
            'normalized_score': round(adjusted_score, 3),
            'confidence_score': round(confidence, 3),
            'flag': risk_level in ['medium_risk', 'high_risk'],
            'risk_level': risk_level,
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1_score': round(f1_score, 3),
            'message': self._generate_message('memory', risk_level, adjusted_score),
            'recommendations': self._generate_recommendations('memory', risk_level, [])
        }
    
    def _get_expected_time(self, difficulty: str) -> float:
        """Get expected response time based on difficulty"""
        times = {'easy': 10, 'medium': 20, 'hard': 30}
        return times.get(difficulty, 20)
    
    def _calculate_time_factor(self, time_ratio: float) -> float:
        """Calculate adjustment factor based on response time"""
        if time_ratio < 0.3:  # Too fast, might be guessing
            return 0.8
        elif time_ratio > 3.0:  # Too slow, might indicate difficulty
            return 0.9
        else:
            return 1.0
    
    def _calculate_profile_adjustment(self, user_profile: Dict, test_type: str) -> float:
        """Adjust scoring based on user profile"""
        adjustment = 1.0
        
        # Age group adjustments
        age_group = user_profile.get('age_group', 'adult')
        if age_group == 'child':
            adjustment *= 1.1  # More lenient for children
        elif age_group == 'teen':
            adjustment *= 1.05
        
        # Learning style adjustments
        learning_style = user_profile.get('learning_style', '')
        if test_type == 'dyslexia' and learning_style == 'visual':
            adjustment *= 1.05
        elif test_type == 'memory' and learning_style == 'visual':
            adjustment *= 1.1
        
        return adjustment
    
    def _calculate_risk_and_confidence(self, score: float, thresholds: Dict, 
                                     analysis: List[Dict]) -> Tuple[str, float]:
        """Calculate risk level and confidence score"""
        
        if score >= thresholds['low_risk']:
            risk_level = 'low_risk'
            confidence = 0.8 + (score - thresholds['low_risk']) * 0.2 / (1 - thresholds['low_risk'])
        elif score >= thresholds['medium_risk']:
            risk_level = 'medium_risk'
            confidence = 0.6 + (score - thresholds['medium_risk']) * 0.2 / (thresholds['low_risk'] - thresholds['medium_risk'])
        else:
            risk_level = 'high_risk'
            confidence = 0.4 + score * 0.2 / thresholds['medium_risk']
        
        # Adjust confidence based on response consistency
        if analysis:
            consistency = self._calculate_consistency(analysis)
            confidence *= consistency
        
        return risk_level, min(0.95, confidence)
    
    def _calculate_consistency(self, analysis: List[Dict]) -> float:
        """Calculate response consistency factor"""
        if not analysis:
            return 1.0
        
        # Check for patterns in incorrect responses
        difficulty_performance = {}
        for item in analysis:
            diff = item['difficulty']
            if diff not in difficulty_performance:
                difficulty_performance[diff] = []
            difficulty_performance[diff].append(item['correct'])
        
        # Expect better performance on easier questions
        consistency = 1.0
        if 'easy' in difficulty_performance and 'hard' in difficulty_performance:
            easy_score = sum(difficulty_performance['easy']) / len(difficulty_performance['easy'])
            hard_score = sum(difficulty_performance['hard']) / len(difficulty_performance['hard'])
            
            if hard_score > easy_score:  # Inconsistent pattern
                consistency *= 0.9
        
        return consistency
    
    def _generate_message(self, test_type: str, risk_level: str, score: float) -> str:
        """Generate detailed assessment message"""
        
        messages = {
            'dyslexia': {
                'low_risk': f"Reading and language processing skills appear to be within typical range (score: {score:.1%}). Continue regular reading practice.",
                'medium_risk': f"Some indicators suggest potential reading challenges (score: {score:.1%}). Consider additional assessment or support.",
                'high_risk': f"Multiple indicators suggest possible dyslexia-related challenges (score: {score:.1%}). Professional evaluation recommended."
            },
            'dyscalculia': {
                'low_risk': f"Mathematical reasoning skills appear to be developing appropriately (score: {score:.1%}).",
                'medium_risk': f"Some areas of mathematical processing may need attention (score: {score:.1%}). Consider targeted practice.",
                'high_risk': f"Significant challenges with number processing detected (score: {score:.1%}). Professional assessment recommended."
            },
            'memory': {
                'low_risk': f"Working memory performance is within expected range (score: {score:.1%}).",
                'medium_risk': f"Working memory may benefit from targeted exercises (score: {score:.1%}).",
                'high_risk': f"Working memory challenges detected (score: {score:.1%}). Consider memory training strategies."
            }
        }
        
        return messages.get(test_type, {}).get(risk_level, "Assessment completed.")
    
    def _generate_recommendations(self, test_type: str, risk_level: str, 
                                analysis: List[Dict]) -> str:
        """Generate personalized recommendations"""
        
        base_recommendations = {
            'dyslexia': {
                'low_risk': "Continue regular reading. Try varied genres and difficulty levels.",
                'medium_risk': "Practice phonics exercises. Use text-to-speech tools. Break reading into smaller chunks.",
                'high_risk': "Seek professional evaluation. Use assistive technology. Consider specialized tutoring."
            },
            'dyscalculia': {
                'low_risk': "Practice mental math daily. Explore mathematical concepts through games.",
                'medium_risk': "Use visual aids for math concepts. Practice number sense exercises. Break problems into steps.",
                'high_risk': "Professional assessment recommended. Use manipulatives and visual tools. Consider specialized math support."
            },
            'memory': {
                'low_risk': "Continue challenging memory with puzzles and games.",
                'medium_risk': "Practice memory strategies like chunking and visualization. Use organizational tools.",
                'high_risk': "Implement memory aids and strategies. Consider working memory training programs."
            }
        }
        
        return base_recommendations.get(test_type, {}).get(risk_level, "Continue practicing and monitoring progress.")

# Global instance
assessment_engine = AssessmentEngine()