import utilities
import requests
import gspread
import json
from datetime import datetime


script_id = "for_hire_listings"



def get_listing_data():
  if utilities.use_test_data:
    sheet_data = [{'Timestamp': '2024-05-16T13:54:21.173Z', 'Approved': 'TRUE', 'Name': 'Name', 'Position': 'Position Sought', 'Your Location': '', 'Location': '', 'Type': '', 'About': 'About', 'Resume': 'https://resume.link', 'Cover': 'https://cover.link', 'Email': 'example@gmail.com', 'Transaction': ''}, {'Timestamp': '2024-05-16T18:20:44.729Z', 'Approved': '', 'Name': 'Full name/pseudonym', 'Position': 'Position Sought', 'Your Location': 'Your Location', 'Location': 'Remote, Hybrid', 'Type': 'FullTime, Contract', 'About': 'About', 'Resume': 'https://resume.link', 'Cover': 'https://cover.link', 'Email': 'example@gmail.com', 'Transaction': 'https://etherscan.io'}, {'Timestamp': '2024-05-22T00:08:46.573Z', 'Approved': '', 'Name': 'name', 'Position': 'position', 'Your Location': 'location', 'Location': 'Remote', 'Type': 'FullTime, Contract', 'About': 'About You (300 characters max)', 'Resume': 'https://resume.link', 'Cover': 'https://cover.link', 'Email': 'example@gmail.com', 'Transaction': 'https://etherscan.io'}]
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
  processed_data = []
  current_listings = utilities.read_file(f"_data/for-hire-listings.json")
  approved_listings = []
  new_listings = 0
  # filter for approved listings and reformat
  for row in raw_data:
    if row["Approved"] == "TRUE":
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
        "email": row["Email"]
      }
      approved_listings.append(entry)
    elif row["Approved"] == "":
      new_listings += 1
  # filter for newly approved listings
  for approved_listing in approved_listings:
    is_new_listing = True
    for listing in current_listings:
      if approved_listing["id"] == listing["id"]:
        is_new_listing = False
    if is_new_listing:
      processed_data.append(approved_listing)
  # filter expired listings from current_listings
  for listing in current_listings:
    # active if less than 31 days old
    active = (utilities.current_time - listing["epoch"]) < 2592000
    if active:
      processed_data.append(listing)
  # send discord ping for new listings
  if new_listings > 0:
    plural = ""
    if new_listings > 1:
      plural = "s"
    msg = f"[{new_listings} new for-hire listing{plural}](<{utilities.FOR_HIRE_LISTINGS_URL}>)"
    utilities.sendDiscordMsg(msg)
  utilities.log(processed_data, context=f"{script_id}__process_listing_data")
  return processed_data

def save_listing_data(processed_data):
  utilities.save_to_file(f"_data/for-hire-listings.json", processed_data, context=f"{script_id}__save_listing_data")


def update_for_hire_listings():
  try:
    raw_data = get_listing_data()
    processed_data = process_listing_data(raw_data)
    save_listing_data(processed_data)
  except Exception as error:
    utilities.log(f"{error}: {script_id}")
    utilities.report_error(error, context=f"{script_id}__update_for_hire_listings")


