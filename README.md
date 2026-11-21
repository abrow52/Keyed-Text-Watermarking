# Keyed-Text-Watermarking

## Setup
May need to setup virtual environment
 - python3 -m venv .venv
 - source .venv/bin/activate
 - To generate a secret key: python3 scripts/key.py 

## How to Run
(results will vary as the secret key will differ)
- To watermark the evaluation passages: python3 -m scripts.watermark
- To run the detector on the unmarked passages: python3 -m scripts.detect
- To submit a preset passage: python3 experiments/serviceHarness.py
- To run the attacks:
  - python3 -m experiments.runRemoval
  - python3 -m experiments.keyForgery
  - python3 -m experiments.queryForgery

## Data Sources
### Calibration Passages
The Wonderful Wizard of Oz
- https://www.gutenberg.org/ebooks/55
- https://www.gutenberg.org/cache/epub/55/pg55-images.html

Through the Looking Glass
- https://www.gutenberg.org/ebooks/12
- https://www.gutenberg.org/cache/epub/12/pg12-images.html

The Adventures of Pinocchio
- https://www.gutenberg.org/ebooks/500
- https://www.gutenberg.org/cache/epub/500/pg500-images.html

The Colors of Space
- https://www.gutenberg.org/ebooks/20796
- https://www.gutenberg.org/cache/epub/20796/pg20796-images.html
### Evaluation Passages
Peter Pan : [Peter and Wendy]
- https://www.gutenberg.org/ebooks/16
- https://www.gutenberg.org/cache/epub/16/pg16-images.html

The Princess and the Goblin
- https://www.gutenberg.org/ebooks/708
- https://www.gutenberg.org/cache/epub/708/pg708-images.html

A Little Girl in Old Boston
- https://www.gutenberg.org/ebooks/23786
- https://www.gutenberg.org/cache/epub/23786/pg23786-images.html

Grimm's Fairy Tales
- https://www.gutenberg.org/ebooks/2591
- https://www.gutenberg.org/cache/epub/2591/pg2591-images.html

## Contribution Statement
All contributions were made by Alicia Brown
