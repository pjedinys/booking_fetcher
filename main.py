import json
import requests
import pandas as pd

with open("data.json", "r") as f:
    data = json.load(f)

destinations = ["Maldives", "Cyprus", "Greece", "Italy", "Turkey", "Portugal", "Spain"]
max_price_pp = 15000 # price per person

headers = {
    "Host": "www.booking.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Content-Type": "application/json",
    "Origin": "https://www.booking.com",
    "Connection": "keep-alive"
}
url = "https://www.booking.com/dml/graphql"


data["variables"]["input"]["dates"]["checkin"] = None
data["variables"]["input"]["dates"]["checkout"] = None
data["variables"]["input"]["flexibleDatesConfig"]["broadDatesCalendar"]["checkinMonths"].append("7-2025")
data["variables"]["input"]["flexibleDatesConfig"]["broadDatesCalendar"]["checkinMonths"].append("8-2025")
data["variables"]["input"]["flexibleDatesConfig"]["broadDatesCalendar"]["los"].append(4) # num nights
data["variables"]["input"]["flexibleDatesConfig"]["broadDatesCalendar"]["losType"] = "CUSTOM"
data["variables"]["input"]["flexibleDatesConfig"]["broadDatesCalendar"]["startWeekdays"].append(1) # monday
data["variables"]["input"]["flexibleDatesConfig"]["dateFlexUseCase"] = "BROAD_DATES"
data["variables"]["input"]["flexibleDatesConfig"]["dateRangeCalendar"]["checkin"] = None
data["variables"]["input"]["flexibleDatesConfig"]["dateRangeCalendar"]["checkout"] = None
data["variables"]["input"]["nbRooms"] = 1
data["variables"]["input"]["nbAdults"] = 2
data["variables"]["input"]["nbChildren"] = 0
data["variables"]["input"]["doAvailabilityCheck"] = True

dictionary = {"city":[], "url":[], "price":[], "currency":[], "review_score":[], "review_count":[], "recommended_checkin":[], "recommended_checkout":[], "meal_plan":[]}

counter = 0
for destination in destinations:
    data["variables"]["input"]["location"]["searchString"] = destination
    session = requests.Session()
            
    response = session.post(url, json=data, headers=headers)
    json = response.json()
    results = json["data"]["searchQueries"]["search"]["results"]

    mealMap = {"No mealplan": 0,
               "Breakfast included": 0.25, 
               "Breakfast & dinner included": 0.5,
               "All meals included": 0.75,
               "All-inclusive": 1}

    for row in results:
        price = row["blocks"][0]["finalPrice"]["amount"]
        if max_price_pp >= price/data["variables"]["input"]["nbAdults"]:
            dictionary["city"].append(row["basicPropertyData"]["location"]["city"])
            dictionary["url"].append(f"https://www.booking.com/hotel/{row["basicPropertyData"]["location"]["countryCode"]}/{row["basicPropertyData"]["pageName"]}.cs.html")
            dictionary["price"].append(price)
            dictionary["currency"].append(row["blocks"][0]["finalPrice"]["currency"])
            dictionary["review_score"].append(row["basicPropertyData"]["reviewScore"]["score"])
            dictionary["review_count"].append(row["basicPropertyData"]["reviewScore"]["reviewCount"])
            dictionary["recommended_checkin"].append(row["recommendedDate"]["checkin"])
            dictionary["recommended_checkout"].append(row["recommendedDate"]["checkout"])
            mealPlan = row["mealPlanIncluded"]["text"] if row["mealPlanIncluded"] else "No mealplan"
            dictionary["meal_plan"].append(mealPlan)

    df = pd.DataFrame(dictionary)
    df['normalized_price'] = (df['price'] - df['price'].min()) / (df['price'].max() - df['price'].min())
    normalized_review_score = (df['review_score'] - df['review_score'].min()) / (df['review_score'].max() - df['review_score'].min())
    normalized_review_count = (df['review_count'] - df['review_count'].min()) / (df['review_count'].max() - df['review_count'].min())
    weighted_review_score = normalized_review_score * normalized_review_count
    df['normalized_weighted_review_score'] = (weighted_review_score - weighted_review_score.min()) / (weighted_review_score.max() - weighted_review_score.min())
    df["score"] = df.apply(lambda row: (mealMap[row.iloc[8]]+row.iloc[9]+row.iloc[10])/3, axis=1)
    df = df.sort_values(by="score", ascending=False).reset_index(drop=True)

    counter += 1
    print(f"{100*counter/len(destinations)}%")
    
df.to_csv("result.csv", index=False)
print("Done")