---
title: "SparseJEPA: Sparse Representation Learning of Joint Embedding Predictive Architectures"
collection: publications
category: manuscripts
permalink: /publication/2009-10-01-paper-title-number-1
excerpt: 'Current Project. Integrating Sparsity into JEPA.'
date: 2025-1-01
# venue: 'Journal 1'
# slidesurl: 'http://academicpages.github.io/files/slides1.pdf'
paperurl: 'https://arxiv.org/abs/2504.16140'
citation: 'Max Hartman, Lav R. Varshney, "SparseJEPA: Sparse Representation Learning of Joint Embedding Predictive Architectures", 2025.'
---

Joint Embedding Predictive Architectures (JEPA) have emerged as a powerful framework for learning general purpose representations. However, these models often lack interpretability and suffer from inefficiencies due to dense embedding representations. We propose SparseJEPA, a unique extension that incorporates sparse representation learning into the JEPA framework, enhancing both quality and interpretability of learned representations. SparseJEPA leverages a penalty method, encouraging latent-space variables to be shared among data features with stronger semantic relationships, while preserving predictive performance. Additionally, the sparse representations provide improved interpretability by highlighting the most relevant features in the learned embeddings, enabling deeper insights into the relationships between inputs. We demonstrate the effectiveness of SparseJEPA on CIFAR100 as a benchmark dataset, by pre-training a light-weight Vision Transformer, and fine-tuning on image classification as a downstream task. Our results indicate that sparsity not only enhances latent-space interpretabilty but also aids in learning meaningful representations.