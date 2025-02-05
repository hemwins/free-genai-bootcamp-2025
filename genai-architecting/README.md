## Functional Requirements

The company wants to invest in owning their infrastructure because of two primary concerns: 
1. privacy of user data
2. cost of managed services for GenAI are likely to soar in future.

They want to invest on an AI PC with 15-25K They have 300 active students, and students are located within the city of Nagasaki.

## Assumptions

We are assuming that the Open-source LLMs that we choose will be powerful enough to run on hardware with an investment of 15-25K. Continuous operational costs, technical training and maintenance overhead is excluded here.

We're looking for a single server in our office and we should have enough bandwidth to serve the 300 students.

It should be able to serve same number of students for another language with additinal bandwidth cost, in case we want to expand our language portal for other languages.

## Constraints
English, German, Spanish, French, Japanese, Portuguese, Arabic, Czech, Italian, Korean, Dutch, and Chinese are currently supported by Granite.

Finetuning Granite models for languages beyond these 12 languages can be costly around technical aspects of data engineering and evaluation.

## Data Strategy

There is a concern of copyright, so we must purchase study materials and store them for access in our database.

It should have room for integration with existing data systems. Eg, In future if any existing student taking another language course, then we should have his/her preferences (in terms of culture or tone) in place.

## Integration and Deployment
1. We will implement CI/CD pipelines seamless integration with evolving language options.
2. Develop APIs and interfaces for easy access to GenAI capabilities

## Infrastructure Suggestion

1. GPU: NVIDIA Quadro RTX 8000(Offering up to 48 GB of VRAM, this GPU is ideal for enterprise-level AI tasks.)
2. CPU: Intel Core i9 or AMD Ryzen 9 (For smaller models or light workloads, these CPUs offer solid performance with a balance of speed and cost.)
3. RAM: 64 GB DDR4/DDR5 (Ideal for running large models)

## Monitoring and Optimization

1. Caching to optimize: 
We will be caching the prompt along with extended context information, so as to avoid hitting vector-database or internet again in order to take advantage of previous calls to these resources.
2. Some kind of logging to register LLM's performance over time.

## Governance and Security

We will be implementing output guardrails to adhere to responsible AI principles.

## Model Selection and Development
Self-hosted open source LLM should work for us. We're considering using IBM Granite because it comes with it's training data. This makes it traceable component for the company.

## Link to this component

https://huggingface.co/ibm-granite