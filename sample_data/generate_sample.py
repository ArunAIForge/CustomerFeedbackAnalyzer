"""Generate a deterministic 220-row sample CSV (English / Tamil / Tanglish). Run:
    python sample_data/generate_sample.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(40)
PLATFORMS = ["Zomato", "Swiggy", "Google", "Amazon"]

POS = [
    (5, "Biryani was amazing, packing also neat. Will order again!"),
    (5, "Super taste, the biryani is the best in town."),
    (4, "Good food and fresh. Packaging was neat and leak proof."),
    (5, "Staff were very friendly and the food was tasty."),
    (5, "Semma taste! Biryani romba nalla irundhuchu."),
    (4, "Nalla saapadu, packing neat ah irundhuchu."),
    (5, "சுவையான பிரியாணி, மிகவும் நன்றாக இருந்தது."),
    (4, "Fast delivery and hot food. Great job."),
]
NEU = [
    (3, "Food was okay, nothing special. Portion is average."),
    (3, "Decent biryani but the app is a little slow to load."),
    (3, "Average taste, delivery on time."),
]
NEG = [
    (1, "Ordered at 8pm, came at 9:10. Food fully cold. Very bad."),
    (2, "Delivery was very late and the food was cold."),
    (1, "Rider came 1 hour late, worst delivery experience."),
    (2, "Saapadu nalla irundhuchu but bill la extra charge pottanga"),
    (2, "Extra packing charge and service charge added to the bill. Overpriced."),
    (2, "Portion size is very small for the price, expensive."),
    (1, "Food poisoning! Got sick and vomiting after eating the chicken rice. Want a refund."),
    (1, "Wrong order delivered, I asked for veg biryani and got chicken. Rude staff on call."),
    (2, "The app crashed twice during payment, very frustrating."),
    (2, "Packing was bad, curry spilled all over the box."),
    (1, "Staff was rude and the waiter shouted at us."),
    (1, "ரொம்ப லேட்டா வந்தது, சாப்பாடு ஆறிப்போச்சு."),
    (2, "Delivery romba late, food cold ah vandhuchu."),
]

rows = []
start = date(2026, 9, 29)
for i in range(220):
    roll = random.random()
    pool = POS if roll < 0.55 else NEU if roll < 0.68 else NEG
    rating, text = random.choice(pool)
    plat = "Swiggy" if (pool is NEG and "late" in text.lower() and random.random() < 0.7) else random.choice(PLATFORMS)
    d = start + timedelta(days=random.randint(0, 6))
    rows.append([f"R-{1041 + i}", d.isoformat(), plat, rating, text])
rows.append(["R-9999", "2026-10-02", "Google", "", ""])  # empty row to show validation

out = Path(__file__).parent / "reviews_week40.csv"
with out.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["review_id", "date", "platform", "rating", "review_text"])
    w.writerows(rows)
print(f"Wrote {len(rows)} rows to {out}")
