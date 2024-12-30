# idea-exploration

## Introduction

Much like my [previous project](https://github.com/venkatesh-narayan/learning-agent/tree/main), this project has the following motivation: I often search things up on Perplexity when trying to learn something new, and after a few weeks of searching, I come across an article / blog post / paper that is super useful (for example, because it explains something really well, or just completely changes the way I think about the space) - and I always think, "it would've been so nice if I found this a few weeks earlier." This project aims at solving that.

There were a couple instances in my previous project where I found useful content from the generated recommendations, and I realized that part of the reason I found that interesting content was because the search queries that the LLM generated were actually along a direction that I hadn't considered. So I realized: if the outputs could just be more comprehensive and creative, I will be able to find more useful content.

## Approach

The main idea was: if I can use reasoning models from OpenAI and Gemini to come up with a "reasoning breakdown graph" - similar to how an expert with strong first-principles reasoning breaks problems down - you will be able to get a more comprehensive scan over the web of things that are generally useful and in the right direction for the user's goal. There are two breakdown graphs that I generate:

1. Key Information Analysis: given what my goal is, what are some key pieces of information that I should know, REGARDLESS of what implementation I choose to do? For example, if I want to build a custom t-shirt company, it's generally useful to know what the raw material costs of t-shirts are (among other things), and this is something I should know regardless of how I choose to actually build out that company.

2. Solution Exploration: given what my goal is, and the findings from the Key Information Analysis, give me a set of comprehensive lines of reasoning that explore the idea more. In other words, generate some high level directions (that are both creative and comprehensive), and then break down these ideas more into the sets of questions that need to be asked in order to properly understand if this is a plausible line of reasoning or not. For example, if I wanted to build a custom t-shirt company, it would be nice to know that there are technologies that do 3D knitting, and it would be nice to go into that line of thinking and see if this approach matches with my specifications.

Generally, for either Key Information Analysis or Solution Exploration, the steps are as follows:

- Use an ensemble of `o1-preview` and `gemini-2.0-flash-thinking-exp` to generate an initial graph that breaks a problem down via first principles thinking. Rather than hallucinating information, it's told to stop once it generates nodes that require real information (e.g. if we need to clarify something from the user, or if we need to search for something on the web).

- Once we generate a graph, we process it; there are three main things that happen during processing, based on the type of node that was generated:
    - Ask the user for information: this is only for mission-critical things, like `"what's your budget"`, or other specific questions that require better understanding of what my goal is.

    - Search the web for information: rather than relying on hallucinated information from LLM's, we can search for real information where we need it. For example, if we were building a custom t-shirt company, it's worth asking things like `"what fabrics do other companies make t-shirts out of"`, `"how much does it cost per unit length of that fabric"`, and `"are there discounts I could get for bulk purchases of that fabric"`, instead of using the raw numbers that the LLM generates. The graph already generates search queries for these nodes, so we use Perplexity API to get the citations, scrape the citations, and try to extract information that's extremely relevant to our goal and our current line of attack.

        - If we find no useful information, we do the following:
            - Break down this approach into other search queries that are more fundamental, and try again. For example, if we search for `"how much fabric is wasted in fast fashion companies per year"`, there's probably no website that's done a detailed breakdown for this (likely because this information is private), so it's unlikely that we'd find a real answer. So instead, we can break it down into other queries, like the ones mentioned above, that might be able to give us a better sense of what the answer should be.

            - If we still can't find any useful information from these new queries, we use reasoning models to do a strong first-principles based analysis to estimate what the answer should be. And we make it clear to the user that it's just an educated guess, since we couldn't find a real answer for this question.

    - Calculations: rather than relying on LLM's to do math for us, we get them to write code to do the math for us. For example, if I'm trying to figure out `"what is the raw material cost of a t-shirt from h&m"`, the calculation we'd need to do is `"cost_per_yard_of_material * amount_of_material_necessary"`; we would find these two pieces of information using web searches, as detailed in the previous bullet point, and then use an LLM to use those values to write code and get the result.

Once we get all of this information, we can use it to go deeper into each line of reasoning. So TL;DR: generate reasoning graph, process each node to do specific things, then use that to deepen the graph, etc.

## Example

![image](https://github.com/user-attachments/assets/c48f5a55-ce1c-49ca-b191-53a59aa873f2)

This is roughly what the frontend looks like right now - the frontend isn't displaying the outputted graph properly (it doesn't handle breakdown nodes properly), but this should give an idea of what I've done in this project.

## Further Directions

The LLM's are reasonable enough at generating some directions - including some that I wouldn't have thought of - but in breaking stuff down, it feels too high-level and not really "expert-driven". It still is missing the aspect of generating legitimate key insights. This is fundamentally a drawback that the current reasoning models (or LLM's generally) have. Wondering if we could somehow gather synthetic data to train LLM's to reason with these types of graphs. And rather than doing web-searching, we could use a differentiable retrieval index to find the best websites / pieces of information (there are some papers, like [this one](https://arxiv.org/pdf/2202.06991) that have done similar things, so it's probably possible to do). This is kind of hand-wavy though, not really sure what the entire training process would look like. I think something like this would be interesting though, because it would force the LLM to break difficult problems down into first principles and search through its memory for relevant information - much like how humans solve problems.
