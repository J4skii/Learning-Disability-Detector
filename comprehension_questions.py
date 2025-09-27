import random

# Full pool of questions (30)
# Fields:
# - id: stable numeric id
# - text: question text
# - options: dict of option_key -> option_text
# - answer: correct option_key ("a" | "b" | "c" | "d")
QUESTIONS = [
    # -------- Passage 1: Procrastination (1–10) --------
    {
        "id": 1,
        "text": "According to modern psychology, what is now considered the main reason people procrastinate?",
        "options": {
            "a": "Poor time management and weak planning skills.",
            "b": "Lack of discipline and personal strength.",
            "c": "Difficulty regulating emotions when tasks feel boring, stressful, or overwhelming.",
            "d": "Naturally short attention spans that make it impossible to sustain focus."
        },
        "answer": "c"
    },
    {
        "id": 2,
        "text": "In the opening example, after opening a blank document, what does the person end up doing?",
        "options": {
            "a": "Beginning the essay but quickly stopping after the first paragraph.",
            "b": "Checking their phone, convincing themselves it will only take five minutes.",
            "c": "Drafting a to-do list instead of starting the assignment.",
            "d": "Reviewing their notes to delay the actual writing."
        },
        "answer": "b"
    },
    {
        "id": 3,
        "text": "How does the brain reinforce procrastination, according to the passage?",
        "options": {
            "a": "By producing dopamine each time avoidance provides temporary relief.",
            "b": "By releasing cortisol to increase focus and urgency.",
            "c": "By lowering stress hormones whenever a task is completed.",
            "d": "By strengthening long-term memory during distractions."
        },
        "answer": "a"
    },
    {
        "id": 4,
        "text": "What emotional consequence follows the short-lived relief of avoiding a task?",
        "options": {
            "a": "Motivation increases and the person feels prepared to restart.",
            "b": "Guilt and anxiety begin to build, adding more stress.",
            "c": "Calmness returns, making the task easier to handle.",
            "d": "Determination and discipline are restored."
        },
        "answer": "b"
    },
    {
        "id": 5,
        "text": "In the procrastination loop described, what typically happens in the final stage?",
        "options": {
            "a": "The task is abandoned and never completed.",
            "b": "The task is completed last-minute, but with extra stress and lower quality.",
            "c": "The person feels so guilty they avoid the task even longer.",
            "d": "The task is completed perfectly but with little learning."
        },
        "answer": "b"
    },
    {
        "id": 6,
        "text": "What is the purpose of the “Just Five Minutes Rule”?",
        "options": {
            "a": "To divide work permanently into five-minute sessions.",
            "b": "To make tasks more enjoyable by limiting how long they last.",
            "c": "To trick the brain into starting, since momentum often makes continuing easier.",
            "d": "To delay tasks in smaller, more manageable ways."
        },
        "answer": "c"
    },
    {
        "id": 7,
        "text": "In the section about breaking down tasks, what specific example does the passage give?",
        "options": {
            "a": "Writing the introduction paragraph first.",
            "b": "Finding three articles to read as a smaller starting step.",
            "c": "Editing a previously completed section of the essay.",
            "d": "Creating an outline of the full essay before writing."
        },
        "answer": "b"
    },
    {
        "id": 8,
        "text": "How does self-compassion help people overcome procrastination?",
        "options": {
            "a": "It makes them feel guiltier, motivating them to work harder.",
            "b": "It reduces self-criticism, allowing forgiveness for past delays and lowering avoidance.",
            "c": "It increases pressure by emphasizing the cost of wasted time.",
            "d": "It distracts them from the stress of the task completely."
        },
        "answer": "b"
    },
    {
        "id": 9,
        "text": "In the conclusion, how does the passage reframe procrastination?",
        "options": {
            "a": "As proof of laziness and lack of willpower.",
            "b": "As a permanent personal weakness.",
            "c": "As a natural human response to stress and discomfort.",
            "d": "As an unavoidable flaw that cannot be managed."
        },
        "answer": "c"
    },
    {
        "id": 10,
        "text": "Which of the following best summarizes the passage’s overall message?",
        "options": {
            "a": "Procrastination is caused by poor planning and must be solved with strict discipline.",
            "b": "Procrastination is rooted in emotional regulation but can be managed with practical strategies like small steps, momentum, and self-compassion.",
            "c": "Procrastination is unavoidable but less damaging if people work well under pressure.",
            "d": "Procrastination is purely a chemical addiction that cannot be broken without medical treatment."
        },
        "answer": "b"
    },

    # -------- Passage 2: Perfectionism (11–20) --------
    {
        "id": 11,
        "text": "According to the passage, what does research suggest is the deeper cause of excessive perfectionism?",
        "options": {
            "a": "A natural drive for achievement and excellence.",
            "b": "The need to manage fears of failure, criticism, and falling short.",
            "c": "Weak organizational and planning skills.",
            "d": "Genetic traits that make people detail-oriented."
        },
        "answer": "b"
    },
    {
        "id": 12,
        "text": "In the introduction, how does the perfectionist behave while working on a report?",
        "options": {
            "a": "They polish minor details like font and reread sections instead of advancing the main work.",
            "b": "They rush to finish quickly, ignoring structure and clarity.",
            "c": "They complete the first draft immediately and then set it aside.",
            "d": "They avoid starting altogether and distract themselves with unrelated activities."
        },
        "answer": "a"
    },
    {
        "id": 13,
        "text": "How is perfectionism reinforced in the brain, according to the text?",
        "options": {
            "a": "The brain rewards temporary relief from anxiety when small edits replace progress.",
            "b": "The brain strengthens memory each time details are polished.",
            "c": "The brain reduces cortisol levels when people delay difficult tasks.",
            "d": "The brain encourages multitasking, which gives a sense of control."
        },
        "answer": "a"
    },
    {
        "id": 14,
        "text": "In the perfectionism cycle described, what typically happens in the final stage?",
        "options": {
            "a": "Time runs out, leading to frustration and incomplete results.",
            "b": "The task is restarted repeatedly until flawless.",
            "c": "The work is abandoned entirely without attempting completion.",
            "d": "The project is finished perfectly but creates exhaustion."
        },
        "answer": "a"
    },
    {
        "id": 15,
        "text": "Why does the passage suggest redefining success as an effective strategy?",
        "options": {
            "a": "It prevents mistakes by encouraging stricter standards.",
            "b": "It shifts focus from flawlessness to whether the work achieves its purpose.",
            "c": "It reduces workload by allowing tasks to be skipped entirely.",
            "d": "It ensures productivity by forcing comparison with others."
        },
        "answer": "b"
    },
    {
        "id": 16,
        "text": "How do time limits help break the cycle of perfectionism?",
        "options": {
            "a": "They create external pressure that forces panic and productivity.",
            "b": "They encourage multitasking to finish more quickly.",
            "c": "They prevent endless revisions by requiring forward movement.",
            "d": "They reduce anxiety by lowering expectations for the work."
        },
        "answer": "c"
    },
    {
        "id": 17,
        "text": "What is the main purpose of self-distancing as a strategy?",
        "options": {
            "a": "To make individuals detach completely from their work.",
            "b": "To imagine giving advice to a friend, reducing harsh self-criticism.",
            "c": "To increase external feedback and accountability.",
            "d": "To motivate people to restart tasks with greater urgency."
        },
        "answer": "b"
    },
    {
        "id": 18,
        "text": "In the conclusion, how does the passage reframe perfectionism?",
        "options": {
            "a": "As proof of strong ambition and dedication.",
            "b": "As a coping mechanism rather than true productivity.",
            "c": "As a weakness that prevents people from achieving success.",
            "d": "As a natural personality trait that cannot be changed."
        },
        "answer": "b"
    },
    {
        "id": 19,
        "text": "What similarity does the passage highlight between perfectionism and procrastination?",
        "options": {
            "a": "Both involve avoiding tasks by turning to entertainment.",
            "b": "Both offer temporary emotional relief while delaying true progress.",
            "c": "Both guarantee higher-quality results in the long run.",
            "d": "Both depend mainly on external deadlines to function."
        },
        "answer": "b"
    },
    {
        "id": 20,
        "text": "Which of the following best summarizes the overall message of the passage?",
        "options": {
            "a": "Perfectionism is simply a form of ambition that should be encouraged.",
            "b": "Perfectionism is a harmless habit that improves detail-oriented work.",
            "c": "Perfectionism, like procrastination, is a coping strategy that provides short-term relief but harms long-term outcomes, and can be managed with strategies like redefining success, time limits, and self-distancing.",
            "d": "Perfectionism is unavoidable and must be accepted as part of human productivity"
        },
        "answer": "c"
    },

    # -------- Passage 3: Multitasking (21–30) --------
    {
        "id": 21,
        "text": "According to the passage, how does research actually describe multitasking?",
        "options": {
            "a": "As an efficient skill where the brain processes information in parallel.",
            "b": "As a phenomenon of divided attention, leading to more mistakes and lower performance.",
            "c": "As an ability that only works effectively for simple tasks.",
            "d": "As a natural talent confirmed by scientific studies."
        },
        "answer": "b"
    },
    {
        "id": 22,
        "text": "What does neuroscience reveal about what the brain does when we think we are multitasking?",
        "options": {
            "a": "It processes multiple streams of input simultaneously.",
            "b": "It rapidly shifts focus between tasks, engaging in task-switching.",
            "c": "It strengthens memory capacity to handle diverse information.",
            "d": "It filters distractions while maintaining efficiency."
        },
        "answer": "b"
    },
    {
        "id": 23,
        "text": "What are the hidden consequences of task-switching?",
        "options": {
            "a": "Increased speed and higher efficiency in all areas.",
            "b": "Reduced time efficiency, lower accuracy, and more mental fatigue.",
            "c": "Fewer errors but greater reliance on working memory.",
            "d": "Stronger motivation with less focus on quality."
        },
        "answer": "b"
    },
    {
        "id": 24,
        "text": "Why does multitasking feel productive to many people, despite slowing progress?",
        "options": {
            "a": "Because external approval reinforces multitasking as a cultural norm.",
            "b": "Because novelty creates a cognitive reward response that feels like progress.",
            "c": "Because multitasking prevents boredom by moving attention constantly.",
            "d": "Because switching tasks allows faster completion overall."
        },
        "answer": "b"
    },
    {
        "id": 25,
        "text": "In the multitasking cycle described in the passage, what occurs during the second stage?",
        "options": {
            "a": "Errors accumulate, leading to extra corrections and lost effort.",
            "b": "Motivation increases as tasks become more engaging.",
            "c": "Stress decreases due to stimulation from novelty.",
            "d": "Work is completed faster with fewer mistakes."
        },
        "answer": "a"
    },
    {
        "id": 26,
        "text": "Which strategy is highlighted as Single-Task Commitment?",
        "options": {
            "a": "Pausing deliberately before task changes to reset attention.",
            "b": "Focusing on one task in dedicated time blocks, resisting the urge to switch.",
            "c": "Ranking activities by their long-term signifigance.",
            "d": "Removing all distractions by multitasking in structured cycles."
        },
        "answer": "b"
    },
    {
        "id": 27,
        "text": "Why does the author emphasize mindful transitions?",
        "options": {
            "a": "To make switching more frequent and less noticeable.",
            "b": "To pause deliberately, helping attention reset between tasks.",
            "c": "To reduce stress by avoiding tasks altogether.",
            "d": "To increase efficiency by multitasking in short bursts."
        },
        "answer": "b"
    },
    {
        "id": 28,
        "text": "How is multitasking reframed in the conclusion?",
        "options": {
            "a": "As a permanent human skill that improves with practice.",
            "b": "As a costly cognitive trap that reduces true focus.",
            "c": "As a natural coping mechanism for stress and anxiety.",
            "d": "As a useful habit that simply needs balance."
        },
        "answer": "b"
    },
    {
        "id": 29,
        "text": "What connection is drawn between multitasking, procrastination, and perfectionism?",
        "options": {
            "a": "All three provide short-term brain rewards while harming long-term progress.",
            "b": "All three strengthen discipline and create sustainable motivation.",
            "c": "All three improve productivity under strict deadlines.",
            "d": "All three occur only when external accountability is missing."
        },
        "answer": "a"
    },
    {
        "id": 30,
        "text": "Which of the following best summarizes the central idea of the passage?",
        "options": {
            "a": "Multitasking increases productivity by keeping the brain stimulated with novelty.",
            "b": "Multitasking is not true efficiency but task-switching, which leads to mistakes, fatigue, and slower progress, and can be improved by focusing strategies.",
            "c": "Multitasking is a natural strength that should be embraced in modern digital environments.",
            "d": "Multitasking is only harmful when combined with procrastination or perfectionism."
        },
        "answer": "b"
    },
]


def get_random_questions(num_questions=10, shuffle_options=True, seed=None):
    """
    Return a random subset of QUESTIONS (default 10), and optionally shuffle option order.
    Each returned item includes:
      - id
      - text
      - options_shuffled: list of tuples [(key, text), ...] in randomized order
      - answer
    """
    rng = random.Random(seed)
    subset = rng.sample(QUESTIONS, k=min(num_questions, len(QUESTIONS)))
    if shuffle_options:
        for q in subset:
            items = list(q["options"].items())  # [(key, text), ...]
            rng.shuffle(items)
            q["options_shuffled"] = items
    else:
        q["options_shuffled"] = list(q["options"].items())
    return subset
