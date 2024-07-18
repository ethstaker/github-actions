import utilities
import requests
import gspread
import json
from datetime import datetime


script_id = "for_hire_listings"



def get_listing_data():
  if utilities.use_test_data:
    sheet_data = [{'Timestamp': '2024-05-16T13:54:21.173Z', 'Approved': 'TRUE', 'Name': 'Name', 'Position': 'Position Sought', 'Your Location': '', 'Location': '', 'Github': 'https://github.com/xyz', 'Type': '', 'About': 'About', 'Resume': 'https://resume.link', 'Cover': 'https://cover.link', 'Email': 'example@gmail.com', 'Transaction': ''}, {'Timestamp': '2024-05-16T18:20:44.729Z', 'Approved': '', 'Name': 'Full name/pseudonym', 'Position': 'Position Sought', 'Your Location': 'Your Location', 'Location': 'Remote, Hybrid', 'Github': 'https://github.com/xyz', 'Type': 'FullTime, Contract', 'About': 'About', 'Resume': 'https://resume.link', 'Cover': 'https://cover.link', 'Email': 'example@gmail.com', 'Transaction': 'https://etherscan.io'}, {'Timestamp': '2024-05-22T00:08:46.573Z', 'Approved': '', 'Name': 'name', 'Position': 'position', 'Your Location': 'location', 'Location': 'Remote', 'Github': 'https://github.com/xyz', 'Type': 'FullTime, Contract', 'About': 'About You (300 characters max)', 'Resume': 'https://resume.link', 'Cover': 'https://cover.link', 'Email': 'example@gmail.com', 'Transaction': 'https://etherscan.io'}]
  else:
    credentials = utilities.GOOGLE_CREDENTIALS
    # get the sheet data
    # reference: https://docs.gspread.org/en/v5.7.0/user-guide.html
    gc = gspread.service_account_from_dict(credentials)
    sheet = gc.open_by_key(utilities.SHEETS_URL).worksheet("For-Hire Listings")
    sheet_data = sheet.get_all_records()
  # utilities.log(sheet_data, context=f"{script_id}__get_listing_data")
  return sheet_data

def process_listing_data(raw_data):
  current_listings = utilities.read_file(f"_data/for-hire-listings.json")
  approved_listings = []
  new_listing_submissions = []
  newly_approved_listings = []
  newly_expired_listings = []

  # reformat and create lists of approved and new listings
  for row in raw_data:
    entry = {
      "id": row["Id"],
      "epoch": utilities.current_time,
      "name": row["Name"],
      "position": row["Position"],
      "location": row["Location"],
      "work_location": row["Work Location"],
      "about": row["About"],
      "type": row["Type"],
      "resume": row["Resume"],
      "cover": row["Cover"],
      "github": row["Github"],
      "email": row["Email"]
    }
    if row["Approved"] == "TRUE":
      approved_listings.append(entry)
    elif row["Approved"] == "":
      new_listing_submissions.append(entry)

  # create list of newly expired listings
  for listing in current_listings:
    # expired if more than 31 days old (one day grace period to account for script delay)
    expired = (utilities.current_time - listing["epoch"]) > 2592000
    if expired:
      newly_expired_listings.append(listing)

  # create list of newly approved listings
  for approved_listing in approved_listings:
    is_new_listing = True
    for current_listing in current_listings:
      if approved_listing["id"] == current_listing["id"]:
        is_new_listing = False
    if is_new_listing:
      newly_approved_listings.append(approved_listing)

  # send discord ping for new listings
  # for listing in newly_approved_listings:
  #   name = f"**{listing['name'].strip()}**"
  #   position = f"*{listing['position'].strip().title()}*"
  #   role_type = f"{listing['type'].strip()}"
  #   work_location = f"{listing['work_location'].strip()}"
  #   location = ""
  #   if listing["work_location"] != "Remote":
  #     location = f"Location: {listing['location'].strip().lower()}\n"
  #   about = ""
  #   if listing["about"]:
  #     about = f"> {listing['about'].strip()}\n"
  #   if 
  #   links = f"[Resume]({listing['resume']})"
  #   if listing["cover"]:
  #     links += f"  |  [Cover]({listing['cover'].strip()})"
  #   if listing["github"]:
  #     links += f"  |  [Github]({listing['github'].strip()})"
  #   contact = f"Contact: {listing['email'].strip()}"
  #   msg = "\n".join((
  #     f"{name}  ({position})",
  #     f"{role_type}  |  {work_location}",
  #     f"{location}",
  #     f"{about}",
  #     f"{links}",
  #     f"",
  #     f"{contact}"
  #     f"\n---------------------------------"))
  #   utilities.sendDiscordMsg(utilities.DISCORD_FOR_HIRE_LISTINGS_WEBHOOK, msg)

  # send discord ping for new listing submissions
  if len(new_listing_submissions) > 0:
    plural = ""
    if len(new_listing_submissions) > 1:
      plural = "s"
    msg = f"[{len(new_listing_submissions)} new for-hire listing{plural}](<{utilities.FOR_HIRE_LISTINGS_URL}>)"
    utilities.sendDiscordMsg(utilities.DISCORD_WEBSITE_WEBHOOK, msg)

  # send discord ping for expired listings
  if len(newly_expired_listings) > 0:
    plural = ""
    ids = []
    if len(newly_expired_listings) > 1:
      plural = "s"
    for listing in newly_expired_listings:
      ids.append(listing["id"])
    msg = f"[{len(newly_expired_listings)} expired for-hire listing{plural}](<{utilities.FOR_HIRE_LISTINGS_URL}>): {', '.join(ids)}"
    utilities.sendDiscordMsg(utilities.DISCORD_WEBSITE_WEBHOOK, msg)
  utilities.log(approved_listings, context=f"{script_id}__process_listing_data")
  return approved_listings

def save_listing_data(approved_listings):
  utilities.save_to_file(f"_data/for-hire-listings.json", approved_listings, context=f"{script_id}__save_listing_data")


def update_for_hire_listings():
  try:
    raw_data = get_listing_data()
    approved_listings = process_listing_data(raw_data)
    save_listing_data(approved_listings)
  except Exception as error:
    utilities.log(f"{error}: {script_id}")
    utilities.report_error(error, context=f"{script_id}__update_for_hire_listings")


