"""Prompt templates (LCEL building blocks)."""
from langchain_core.prompts import ChatPromptTemplate

ANALYSIS_SYSTEM = """You analyse customer reviews for a restaurant / online-store business in India.
Reviews may be English, Tamil (Tamil script) or Tanglish (Tamil written in English letters).
Understand them fully and ALWAYS write the summary and reply in English.

Rules:
- sentiment: positive | neutral | negative (judge the text; the star rating is only a hint).
- category: exactly one of food_quality, delivery, price, staff, packaging, app.
  Pick the main thing the customer talks about. Lateness, a missing order, a rider problem, or food that
  arrived cold BECAUSE of delay is 'delivery', not 'food_quality'. Extra charges / bill disputes are 'price'.
- urgency: high ONLY for health/food-safety issues, refund demands, abuse/rude staff,
  or a wrong order. medium for a clear complaint. low for praise or minor remarks.
- language: "Tamil" ONLY if written in Tamil script; "Tanglish" if Tamil words are written in English letters
  (e.g. "saapadu nalla irundhuchu"); "English" if plain English; otherwise "Other".
- summary: ONE short English sentence (max 15 words) stating the facts (include numbers like delay minutes).
- suggested_reply: polite, one or two SHORT sentences (max 25 words), ready to post, apologise only when there is a problem.
  Do not promise refunds or compensation you cannot know about."""

ANALYSIS_HUMAN = "Platform: {platform}\nStar rating: {rating}\nReview: {review_text}"

analysis_prompt = ChatPromptTemplate.from_messages(
    [("system", ANALYSIS_SYSTEM), ("human", ANALYSIS_HUMAN)]
)

REPORT_SYSTEM = """You write the weekly feedback insight for a business manager.
You receive one line per analysed review: id | platform | sentiment | category | urgency | summary.

Return:
- top_complaints: up to 3 recurring complaint themes. For each, list the review ids (copied EXACTLY
  from the input) that belong to it. Only use negative reviews.
- top_praises: up to 3 recurring praise themes, same format, positive reviews only.
- action_items: exactly 3 concrete, practical actions. The last one must be to reply to the urgent reviews.

Never invent ids. Do not output any counts or percentages; they are computed elsewhere."""

REPORT_HUMAN = "Urgent (high) reviews this week: {urgent_count}\n\nReviews:\n{review_lines}"

report_prompt = ChatPromptTemplate.from_messages(
    [("system", REPORT_SYSTEM), ("human", REPORT_HUMAN)]
)

BATCH_HUMAN = """Analyse each review below. Return exactly one result per review, in the same order,
with review_id copied exactly. Each input line is: review_id | platform | stars | review text

{reviews}"""

batch_prompt = ChatPromptTemplate.from_messages([("system", ANALYSIS_SYSTEM), ("human", BATCH_HUMAN)])
PROMPT_VERSION = "v5-batch"  # bump when prompts change so cached results are not reused
