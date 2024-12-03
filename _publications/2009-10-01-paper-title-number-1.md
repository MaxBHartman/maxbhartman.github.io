---
title: "SwitchCIT: Switching for Continual Instruction Tuning of Large Language Models"
collection: publications
category: manuscripts
permalink: /publication/2009-10-01-paper-title-number-1
excerpt: 'Switch Network to help alleviate catastrophic forgetting in continual learning.'
# date: '2024-07-16'
# venue: 'Journal 1'
# slidesurl: 'http://academicpages.github.io/files/slides1.pdf'
paperurl: 'https://arxiv.org/abs/2407.11780'
citation: 'Xinbo Wu, **Max Hartman**, Vidhata Jayaraman, and Lav R. Varshney, "SwitchCIT: Switching for Continual Instruction Tuning of Large Language Models", 2024.'
---

Large language models (LLMs) have exhibited impressive capabilities in various domains, particularly in general language understanding. However these models, trained on massive text data, may not be finely optimized for specific tasks triggered by instructions. Continual instruction tuning is crucial to adapt LLMs to evolving tasks and domains, ensuring their effectiveness and relevance across a wide range of applications. In the context of continual instruction tuning, where models are sequentially trained on different tasks, catastrophic forgetting can occur, leading to performance degradation on previously learned tasks. This work addresses the catastrophic forgetting in continual instruction learning for LLMs through a switching mechanism for routing computations to parameter-efficient tuned models. We demonstrate the effectiveness of our method through experiments on continual instruction tuning of different natural language generation tasks.