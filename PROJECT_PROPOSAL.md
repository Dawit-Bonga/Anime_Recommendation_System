# CS 4580/5580 Project Proposal

## Title

Explainable Hybrid Anime Recommendation System

## Summary

This project is an automated decision system that recommends anime based on a user's input title or watchlist. The system combines collaborative filtering and content-based recommendation in Python, then adds an explanation layer that shows why each recommendation was selected.

The goal is not just to rank anime, but to justify the decision in a way that is understandable to a user. For each recommendation, the system will report the method used, the main similarity signals, and any rule-based filtering steps that affected the final result.

## Problem

Recommendation systems often act like black boxes. A user sees a result, but not the reasoning behind it. This project addresses that problem in the domain of anime discovery by building a recommender that can explain its decisions.

The decision problem is:

- given one anime or a small set of anime
- choose a ranked list of likely good next watches
- explain why those titles were chosen over other candidates
s
## Approach

The system uses a hybrid recommendation pipeline:

- Collaborative filtering with SVD when the input anime exists in the training data
- Content-based recommendation with TF-IDF on genre metadata as a fallback
- Rule-based filtering to remove direct sequels and deduplicate franchise entries

An explanation layer will be added on top of the ranking output. Each recommendation will include:

- recommendation method used
- similarity score or component scores
- shared genre or metadata signals when available
- source title or watchlist items that contributed to the recommendation
- filtering decisions, such as sequel removal or franchise deduplication
- a short natural-language explanation summary

## Why This Fits The Course

This project matches the course requirements because it is:

- an automated decision system
- implemented in Python
- based on techniques discussed in class, including machine learning and decision logic
- explainable rather than purely black-box

It also fits the suggested topic of a recommendation system with smart search and goal-aware decision support.

## Planned Deliverables

- A Python-based recommendation system that runs locally
- A notebook or script that can be run in the Zoo environment
- Explanatory output for each recommendation
- A short write-up covering system design, how to run it, and how the decision explanations work
- Optional web interface for demonstration

## Technical Plan

The current codebase already includes:

- FastAPI backend
- React frontend
- SVD collaborative filtering
- TF-IDF content-based fallback
- title normalization and franchise filtering

To make the project ready for the course submission, I will add:

- a Python-first runnable path for Zoo grading
- structured decision explanations in recommendation responses
- a concise evaluation section with example queries and system behavior
- documentation focused on the decision process rather than only the UI

## Expected Output

For a query such as `Naruto`, the system should return recommendations like:

- title
- final recommendation score
- recommendation method
- explanation summary

Example explanation:

`You picked Naruto, which signals interest in Action and Adventure. This recommendation shares those signals and has a strong match strength of 98%. The system also reports the model score, shared genres, and filtering rules that removed same-franchise sequels.`

## Evaluation

The project will be evaluated in two ways:

- qualitative evaluation through example recommendation traces and explanation quality
- basic ranking sanity checks on known anime titles and watchlists

If time permits, I will also add a simple top-k evaluation or small validation experiment.

## Scope

The core submission will prioritize:

- correct recommendation behavior
- explanation quality
- Zoo-compatible Python execution

The web frontend is useful for presentation, but it is not the core graded component.

## Risks And Mitigation

- Large data and model files may make setup harder in Zoo
- External APIs are not reliable for grading

To reduce risk, the required submission path will avoid dependence on the frontend and third-party APIs. The main deliverable will be a local Python workflow using precomputed data and models.

## Timeline

- Proposal: finalize framing and approval
- Implementation: add explanation layer and Python-only demo path
- Testing: verify local and Zoo-compatible execution
- Final submission: write-up, screenshots if useful, and cleaned code
